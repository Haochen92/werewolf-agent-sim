"""The extraction job's served-game path (v8 decisions §16), on a throwaway database: a run takes the
games its selection names, skips games already extracted, and writes their lessons back for the replay
and the learning tick; a game already folded into the store keeps its lessons."""

import os
import uuid
from contextlib import contextmanager

import psycopg
import pytest
from dotenv import load_dotenv

from Agents.memory.extraction.served_games import ServedSelection, select_served_games, write_back
from Agents.schemas.evaluation import ExtractionCase

load_dotenv()
DSN = os.environ.get("WW_POSTGRES_DSN")
needs_db = pytest.mark.skipif(not DSN, reason="WW_POSTGRES_DSN not set (ww-postgres container)")

LINEUP = ["healer"] * 10


@contextmanager
def _throwaway_db():
    """A fresh database holding the server's tables, dropped afterwards."""
    from sqlalchemy import create_engine
    from sqlmodel import SQLModel

    import server.database_models  # noqa: F401 — registers the tables

    name = f"ww_served_test_{uuid.uuid4().hex[:10]}"
    admin = psycopg.connect(DSN, autocommit=True)
    admin.execute(f'CREATE DATABASE "{name}"')
    test_dsn = DSN.rsplit("/", 1)[0] + f"/{name}"
    engine = create_engine(test_dsn.replace("postgresql://", "postgresql+psycopg://", 1))
    try:
        SQLModel.metadata.create_all(engine)
        yield test_dsn
    finally:
        engine.dispose()
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


def _case(game_id: str, human_players=()) -> ExtractionCase:
    return ExtractionCase(game_id=game_id, roles={"player_1": "healer"}, lineup=LINEUP, game_outcome="villagers",
                          human_players=list(human_players), formatted_discussions="record",
                          formatted_strategy_notes="notes")


def _add_game(dsn: str, game_id: str, *, memory=True, n_humans=0, finished="2026-10-20", extracted=False):
    """A completed ten-seat game, through the server's own table mappings so every default applies."""
    from datetime import datetime, timezone

    from sqlalchemy import create_engine
    from sqlmodel import Session

    from server.database_models import EventRow, GameRow

    humans = [f"player_{i + 1}" for i in range(n_humans)]
    engine = create_engine(dsn.replace("postgresql://", "postgresql+psycopg://", 1))
    with Session(engine) as session:
        session.add(GameRow(
            game_id=game_id, status="completed", memory=memory, n_humans=n_humans, human_players=humans,
            extraction_input=_case(game_id, humans).model_dump(mode="json"), days=3,
            finished_at=datetime.fromisoformat(finished).replace(tzinfo=timezone.utc),
            lessons_extracted_at=datetime(2026, 10, 21, tzinfo=timezone.utc) if extracted else None))
        session.flush()
        session.add(EventRow(game_id=game_id, seq=1, payload={"type": "game_started", "lineup": LINEUP}))
        session.commit()
    engine.dispose()


def _ids(selected) -> list[str]:
    return [case.game_id for _metadata, case in selected]


@needs_db
def test_a_run_takes_what_its_selection_names():
    with _throwaway_db() as dsn:
        _add_game(dsn, "g-ai", finished="2026-10-20")
        _add_game(dsn, "g-human", n_humans=1, finished="2026-10-21")
        _add_game(dsn, "g-off", memory=False, finished="2026-10-22")
        _add_game(dsn, "g-done", extracted=True, finished="2026-10-23")

        assert _ids(select_served_games(ServedSelection(), dsn)) == ["g-ai", "g-human"]  # memory on, not done
        assert _ids(select_served_games(ServedSelection(humans=False), dsn)) == ["g-ai"]
        assert _ids(select_served_games(ServedSelection(humans=True), dsn)) == ["g-human"]
        assert _ids(select_served_games(ServedSelection(memory=None), dsn)) == ["g-ai", "g-human", "g-off"]
        assert _ids(select_served_games(ServedSelection(redo=True), dsn)) == ["g-ai", "g-human", "g-done"]
        assert _ids(select_served_games(ServedSelection(games=["g-h"]), dsn)) == ["g-human"]
        assert _ids(select_served_games(ServedSelection(since="2026-10-20T12:00"), dsn)) == ["g-human"]
        sample = _ids(select_served_games(ServedSelection(memory=None, sample=2, seed=7), dsn))
        assert len(sample) == 2 and sample == _ids(select_served_games(
            ServedSelection(memory=None, sample=2, seed=7), dsn))  # the same seed takes the same games
        metadata, case = select_served_games(ServedSelection(humans=True), dsn)[0]
        assert metadata["input"] == "saved" and case.human_players == ["player_1"] and case.observations == []


@needs_db
def test_written_lessons_mark_the_game_and_a_folded_game_keeps_its_own():
    with _throwaway_db() as dsn:
        _add_game(dsn, "g-new")
        _add_game(dsn, "g-folded")
        filled = [_case("g-new").model_copy(update={"model_used": "claude-sonnet-5-5"}), _case("g-folded")]
        with psycopg.connect(dsn) as conn:
            conn.execute("insert into game_lessons (game_id, run_name, extraction_case, replay, folded_in_gen) "
                         "values ('g-folded', 'earlier', '{}', '{}', 1)")

        result = write_back("run_1", filled, {"g-new": {"revised": 0}}, dsn)

        assert result == {"written": 1, "skipped_folded": ["g-folded"]}
        with psycopg.connect(dsn) as conn:
            run, replay, dehalo, model = conn.execute(
                "select run_name, replay, dehalo, model_used from game_lessons where game_id = 'g-new'").fetchone()
            assert run == "run_1" and replay["event"] == "memory_extracted" and replay["day"] == 3
            assert dehalo == {"revised": 0} and model == "claude-sonnet-5-5"
            marked = dict(conn.execute("select game_id, lessons_extracted_at is not null from games").fetchall())
            assert marked == {"g-new": True, "g-folded": False}
            assert conn.execute("select run_name from game_lessons where game_id = 'g-folded'").fetchone() == ("earlier",)
        assert select_served_games(ServedSelection(), dsn)[0][1].game_id == "g-folded"  # g-new is done

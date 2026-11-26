"""A served game's evaluation cases on a real Postgres database, in the test container.

The unit tests (tests/server/test_eval_case_storage.py) show that a game hands its cases to the
repository. These show the rest on the real tables: the cases of a whole game played by the real
engine are saved and read back by the evaluation code's own reader; a second write replaces the
first; and the shelf life deletes old rows and leaves newer ones.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from evaluation.src.data.sources.sidecar import LocalCaseSource
from server.config import ServerSettings
from server.database_models.game import COMPLETED
from server.db import Database
from server.game.run_config import game_run_config
from server.housekeeping.export_eval_cases import export_cases
from server.housekeeping.sweeper import expire_eval_cases
from server.storage.eval_cases import RECORD_FORMAT, EvalCaseArchive, encode_cases
from server.storage.game_repository import GameRepository
from tests.factories.served_game import (
    GAME_TIMEOUT_S,
    delegate_until_over,
    give_models,
    open_server,
    wait_for_question,
)
from tests.fixtures.database import sqlalchemy_url

HUMAN_TOKEN = "seat-token-of-the-human"


async def test_a_served_games_cases_are_saved_and_read_back_by_the_evaluation_reader(
        server_tables_dsn, scripted_model, refuse_real_models, tmp_path):
    # Arrange: a server on the test database, and a game with one human seat
    server = await open_server(server_tables_dsn)
    try:
        session = await server.registry.start_instant(
            game_run_config(memory=False, human_player=1), api_key="", model="",
            seat_tokens=[HUMAN_TOKEN])
        give_models(session, scripted_model(3))
        session.subscribe(HUMAN_TOKEN)

        # Act: the real engine plays the game to its end, then the stored cases are exported
        await wait_for_question(session, server.graph)
        await delegate_until_over(session)
        await asyncio.wait_for(session.wait_finished(), timeout=GAME_TIMEOUT_S)
    finally:
        await server.stop()
    assert session.game_over and session.error is None
    database = Database(sqlalchemy_url(server_tables_dsn))
    await database.startup()
    try:
        archive = EvalCaseArchive(database)
        listings = await archive.list_games()
        exported = await export_cases(archive, tmp_path)
    finally:
        await database.close()

    # Assert: one row for the game, in the current format, holding every case the game built
    built = session._context["eval_sink"].records
    assert [(g.game_id, g.n_cases, g.partial, g.record_format) for g in listings] == [
        (session.game_id, len(built), False, RECORD_FORMAT)]
    assert exported == 1
    # The evaluation code's reader turns the exported files back into typed cases.
    source = LocalCaseSource(tmp_path / "games.jsonl")
    (trace_id,) = source.trace_ids()
    turn_cases = source.eval_cases(trace_id)
    assert len(turn_cases) > 20  # a ten-seat game has well over twenty seat decisions
    assert {case.player_id for case in turn_cases} <= {f"player_{n}" for n in range(1, 11)}
    assert len(source.day_summary_cases(trace_id)) >= 1  # the game had at least one day


async def test_a_second_write_replaces_a_games_cases(server_tables_dsn):
    # Arrange
    database = Database(sqlalchemy_url(server_tables_dsn))
    await database.startup()
    try:
        repository, archive = GameRepository(database), EvalCaseArchive(database)
        assert await repository.create_game("itest-game", status=COMPLETED, model="test-model",
                                            seats=[])
        first, second = [{"name": "one"}], [{"name": "one"}, {"name": "two"}]

        # Act: the game's cases are written twice
        for records, partial in ((first, True), (second, False)):
            assert await repository.record_eval_cases(
                "itest-game", encode_cases(records), n_cases=len(records), partial=partial,
                record_format=RECORD_FORMAT)

        # Assert: one row, holding the second write
        (listing,) = await archive.list_games()
        assert (listing.n_cases, listing.partial) == (2, False)
        assert await archive.load_cases("itest-game") == second
    finally:
        await database.close()


async def test_the_shelf_life_deletes_old_cases_and_keeps_newer_ones(server_tables_dsn):
    # Arrange: three games whose cases were saved 200, 183 and 10 days before "now"
    now = datetime(2027, 6, 1, tzinfo=timezone.utc)
    settings = ServerSettings(EVAL_CASES_TTL_DAYS=183)
    database = Database(sqlalchemy_url(server_tables_dsn))
    await database.startup()
    try:
        repository, archive = GameRepository(database), EvalCaseArchive(database)
        for game_id, age_days in (("old", 200), ("at-the-limit", 183), ("recent", 10)):
            assert await repository.create_game(game_id, status=COMPLETED, model="test-model",
                                                seats=[])
            assert await repository.record_eval_cases(
                game_id, encode_cases([{"name": game_id}]), n_cases=1, partial=False,
                record_format=RECORD_FORMAT)
            async with database.session() as session:
                await session.execute(
                    text("UPDATE game_eval_cases SET saved_at = :at WHERE game_id = :id"),
                    {"at": now - timedelta(days=age_days), "id": game_id})
                await session.commit()

        # Act
        deleted = await expire_eval_cases(archive, settings, now=now)

        # Assert: only the game past the shelf life lost its cases; its game row is untouched
        assert deleted == 1
        # Exactly at the limit is kept: a row goes once it is older than the shelf life.
        assert [g.game_id for g in await archive.list_games()] == ["at-the-limit", "recent"]
        assert await repository.load_game("old") is not None
    finally:
        await database.close()

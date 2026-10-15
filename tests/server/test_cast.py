"""The puppet cast: picks are honoured, the rest is drawn, nobody stands twice, and the
catalogue is what the server hands out."""

from __future__ import annotations

import asyncio
import importlib.util
import random
from pathlib import Path

import pytest

from server.db import Database
from server.game.cast import CATALOGUE, DRAW_POOL, CastSeat, draw_cast, seat_number
from server.storage.game_repository import GameRepository
from tests.fixtures.server import FakeGraph

SEATS = [f"player_{i}" for i in range(1, 10)]


def test_the_draw_covers_every_seat_with_a_distinct_puppet():
    cast = draw_cast(SEATS, rng=random.Random(7))
    assert [c.seat for c in cast] == SEATS
    assert len({c.character for c in cast}) == len(SEATS)
    assert all(c.character in DRAW_POOL and not c.chosen for c in cast)


def test_picks_stand_where_they_were_made_and_are_never_drawn_for_anyone_else():
    picks = {"player_3": "whale", "player_7": "shade"}
    cast = draw_cast(SEATS, picks, rng=random.Random(1))
    by_seat = {c.seat: c for c in cast}
    assert by_seat["player_3"] == CastSeat("player_3", "whale", True)
    assert by_seat["player_7"] == CastSeat("player_7", "shade", True)
    others = [c.character for c in cast if not c.chosen]
    assert "whale" not in others and "shade" not in others
    assert len({c.character for c in cast}) == len(SEATS)


def test_the_draw_is_random_but_seedable():
    assert draw_cast(SEATS, rng=random.Random(3)) == draw_cast(SEATS, rng=random.Random(3))
    assert draw_cast(SEATS, rng=random.Random(3)) != draw_cast(SEATS, rng=random.Random(4))


def test_more_seats_than_puppets_is_refused():
    with pytest.raises(ValueError):
        draw_cast([f"player_{i}" for i in range(1, len(DRAW_POOL) + 2)])


def test_seats_order_by_number_not_text():
    assert sorted(["player_10", "player_2", "player_1"], key=seat_number) == [
        "player_1", "player_2", "player_10"]


def test_the_catalogue_has_distinct_ids_and_the_songbird_keeps_its_slug():
    ids = [c.id for c in CATALOGUE]
    assert len(set(ids)) == len(ids)
    assert next(c.display_name for c in CATALOGUE if c.id == "shade") == "Songbird"


def test_the_migrations_seed_exactly_the_catalogue():
    """A catalogued puppet the table lacks would fail the cast's foreign key at the deal."""
    seeded = []
    for path in sorted((Path(__file__).resolve().parents[2] / "alembic/versions").glob("*.py")):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        seeded += getattr(module, "SEED", [])
    assert seeded == [(c.id, c.display_name) for c in CATALOGUE]


# ---- the repository's acknowledgements, as for events --------------------------------


async def test_disabled_storage_acknowledges_a_cast_write_and_loads_nothing():
    repository = GameRepository(Database(""))
    assert await repository.record_cast("g", [CastSeat("player_1", "owl", False)])
    assert await repository.load_cast("g") == []


async def test_storage_failure_does_not_acknowledge_a_cast_write(monkeypatch):
    database = Database("postgresql+psycopg://unused")

    def unavailable():
        raise ConnectionError("test: database unavailable")

    monkeypatch.setattr(database, "session", unavailable)
    assert not await GameRepository(database).record_cast(
        "g", [CastSeat("player_1", "owl", False)])


# ---- GET /characters -------------------------------------------------------------------


def test_the_catalogue_is_served_with_ids_and_display_names(api_client):
    cards = api_client.get("/characters").json()
    assert [c["id"] for c in cards] == [c.id for c in CATALOGUE]
    assert {"id": "shade", "display_name": "Songbird", "retired": False} in cards


# ---- the session: the cast is drawn at the deal and written down once ----------------


def _deal_chunk(human_players: list[str]) -> dict:
    """The engine's INITIALIZE_GAME update, as the session sees it: nine seats dealt,
    ``human_players`` among them."""
    roles = {f"player_{i}": "villager" for i in range(1, 10)}
    roles["player_2"] = "wolf"
    return {"type": "updates", "ns": [], "data": {"INITIALIZE_GAME": {
        "roles": roles, "human_players": human_players, "current_day": 1}}}


class CastRepository:
    """The narrow contract the session writes the cast through."""

    def __init__(self, accept: bool = True) -> None:
        self.accept = accept
        self.written: list[list[CastSeat]] = []

    async def record_events(self, game_id, events):
        return True

    async def update_game(self, game_id, **fields):
        return True

    async def record_cast(self, game_id, cast):
        self.written.append(list(cast))
        return self.accept


async def test_the_deal_lands_each_pick_on_the_seat_its_player_was_dealt(quiet_session):
    repository = CastRepository()
    session = quiet_session(
        FakeGraph([_deal_chunk(["player_4", "player_7"])]),
        seat_tokens=["tok-a", "tok-b"], picks=["whale", None], repository=repository)
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    by_seat = {c.seat: c for c in session.cast}
    assert sorted(by_seat) == sorted(SEATS)
    assert by_seat["player_4"] == CastSeat("player_4", "whale", True)  # tok-a's pick
    assert not by_seat["player_7"].chosen  # tok-b never chose: the house drew
    assert len({c.character for c in session.cast}) == 9
    assert repository.written == [session.cast]  # written once, with the deal


async def test_a_failed_cast_write_is_retried_with_the_next_save(quiet_session):
    repository = CastRepository(accept=False)
    session = quiet_session(FakeGraph([_deal_chunk([])]), repository=repository)
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)
    assert len(repository.written) == 1 and not session._saved_cast  # refused, kept

    repository.accept = True
    await session._persist_tail()
    assert len(repository.written) == 2 and session._saved_cast  # retried with the tail
    await session._persist_tail()
    assert len(repository.written) == 2  # saved: never written again


async def test_a_rebuilt_game_keeps_the_cast_it_stored_and_never_redraws(quiet_session):
    stored = [CastSeat(s, c, False) for s, c in zip(SEATS, DRAW_POOL)]
    session = quiet_session(FakeGraph([]), seat_tokens=["tok-a"], picks=["cat"])
    session.reload_history([], ["player_3"], stored)
    assert session.cast == stored and session._saved_cast
    session._deal_cast(SEATS)  # a replayed deal chunk after a restart changes nothing
    assert session.cast == stored


def test_a_game_recorded_before_casts_were_stored_keeps_none(quiet_session):
    session = quiet_session(FakeGraph([]))
    session.reload_history([], [], [])
    assert session.cast == [] and not session._saved_cast

"""The puppet cast: picks are honoured, the rest is drawn, nobody stands twice, and the
catalogue is what the server hands out."""

from __future__ import annotations

import random

import pytest

from server.db import Database
from server.game.cast import CATALOGUE, DRAW_POOL, CastSeat, draw_cast, seat_number
from server.storage.game_repository import GameRepository

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

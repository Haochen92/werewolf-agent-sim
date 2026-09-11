"""Retention sweeper (seat_continuity.md §7): a parked game nobody is watching has a
shelf life; everything else is left alone."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from server.config import ServerSettings
from server.game.lobby import GameLobby
from server.game.live_game_registry import LiveGameRegistry
from server.housekeeping.sweeper import is_expired, sweep_parked_games
from tests.factories.builders import human_turn_request
from tests.fixtures.server import HangingGraph

SETTINGS = ServerSettings(_env_file=None, SOLO_PARK_TTL_SECONDS=3600,
                          MULTI_PARK_TTL_SECONDS=86400)


class Repo:
    def __init__(self):
        self.upserts = []

    async def upsert_game(self, game_id, **fields):
        self.upserts.append((game_id, fields))


async def _parked(quiet_session, *, seats, idle: timedelta):
    """A started session parked on one human question for `idle`."""
    session = quiet_session(HangingGraph(), seat_tokens=seats)
    session.start()
    await asyncio.sleep(0)
    session.pending_requests["p1"] = human_turn_request(player_id="p1")
    session.parked_since = datetime.now(timezone.utc) - idle
    return session


async def test_solo_past_an_hour_is_expired_before_it_is_not(quiet_session):
    old = await _parked(quiet_session, seats=["t1"], idle=timedelta(minutes=61))
    young = await _parked(quiet_session, seats=["t1"], idle=timedelta(minutes=59))
    assert is_expired(old, SETTINGS) and not is_expired(young, SETTINGS)
    await old.shutdown()
    await young.shutdown()


async def test_multi_uses_the_day_window(quiet_session):
    old = await _parked(quiet_session, seats=["t1", "t2"], idle=timedelta(hours=25))
    young = await _parked(quiet_session, seats=["t1", "t2"], idle=timedelta(hours=2))
    assert is_expired(old, SETTINGS) and not is_expired(young, SETTINGS)
    await old.shutdown()
    await young.shutdown()


async def test_a_watched_or_settled_game_is_never_expired(quiet_session):
    watched = await _parked(quiet_session, seats=["t1"], idle=timedelta(hours=5))
    watched.subscribe(lambda: "p1")
    assert not is_expired(watched, SETTINGS)
    running = await _parked(quiet_session, seats=["t1"], idle=timedelta(hours=5))
    running.pending_requests.clear()  # the graph is driving, not parked
    assert not is_expired(running, SETTINGS)
    over = await _parked(quiet_session, seats=["t1"], idle=timedelta(hours=5))
    over.game_over = True
    assert not is_expired(over, SETTINGS)
    for s in (watched, running, over):
        await s.shutdown()


async def test_sweep_drops_only_the_expired_and_is_idempotent(quiet_session):
    expired = await _parked(quiet_session, seats=["t1"], idle=timedelta(hours=2))
    fresh = await _parked(quiet_session, seats=["t1"], idle=timedelta(minutes=1))
    repo = Repo()
    games = LiveGameRegistry(repo, SimpleNamespace(graph=None))
    for entry in (expired, fresh, GameLobby(model="", name="x")):
        games.adopt(entry)

    assert await sweep_parked_games(games, SETTINGS) == [expired.game_id]
    assert expired.error.startswith("abandoned:") and expired._finished.is_set()
    assert repo.upserts == [(expired.game_id, {"status": "dropped", "error": expired.error})]
    assert fresh.error is None
    assert games.get(expired.game_id) is None  # ended and unwatched: the row answers now

    assert await sweep_parked_games(games, SETTINGS) == []  # nothing left to do
    await fresh.shutdown()

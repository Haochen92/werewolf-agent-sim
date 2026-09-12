"""The live registry's promise: a game leaves the table when it has ended and nobody is
watching, and not before. The endings themselves are tested with the session and the
sweeper; this file covers only the letting go."""

from __future__ import annotations

from types import SimpleNamespace

from server.game.live_game_registry import LiveGameRegistry
from tests.fixtures.server import FakeGraph


class Repo:
    def __init__(self):
        self.upserts = []

    async def upsert_game(self, game_id, **fields):
        self.upserts.append((game_id, fields))


def _registry():
    return LiveGameRegistry(Repo(), SimpleNamespace(graph=None))


async def test_an_ended_game_nobody_watches_leaves_at_once(quiet_session):
    games = _registry()
    session = quiet_session(FakeGraph([]), seat_tokens=["tok"])
    games._place(session)

    await session.abandon("test: over")
    assert games.get(session.game_id) is None


async def test_an_ended_game_stays_until_its_last_viewer_leaves(quiet_session):
    games = _registry()
    session = quiet_session(FakeGraph([]), seat_tokens=["tok"])
    games._place(session)
    first, second = session.subscribe(), session.subscribe()

    await session.abandon("test: over")
    assert games.get(session.game_id) is session  # two streams still open on it
    session.unsubscribe(first)
    assert games.get(session.game_id) is session  # one left
    session.unsubscribe(second)
    assert games.get(session.game_id) is None


async def test_a_live_game_is_never_released(quiet_session):
    games = _registry()
    session = quiet_session(FakeGraph([]), seat_tokens=["tok"])
    games._place(session)

    q = session.subscribe()
    session.unsubscribe(q)  # viewers come and go while the game is live
    assert games.release_idle() == []
    assert games.get(session.game_id) is session
    await session.shutdown()


async def test_release_idle_is_the_backstop_when_no_hook_fired(quiet_session):
    games = _registry()
    session = quiet_session(FakeGraph([]), seat_tokens=["tok"])
    games._place(session)
    session.on_idle = None  # pretend the hook was never wired
    session._end()

    assert games.release_idle() == [session.game_id]
    assert games.get(session.game_id) is None
    assert games.release_idle() == []  # nothing left to forget

"""The live registry's promise: a game leaves the table when it has ended and nobody is
watching, and not before. The endings themselves are tested with the session and the
sweeper; this file covers only the letting go."""

from __future__ import annotations

from types import SimpleNamespace

from server.game.live_game_registry import LiveGameRegistry
from tests.fixtures.server import FakeGraph


class _FakeGameRepository:
    def __init__(self):
        self.updates = []

    async def update_game(self, game_id, **fields):
        self.updates.append((game_id, fields))


def _registry():
    return LiveGameRegistry(_FakeGameRepository(), SimpleNamespace(graph=None))


async def test_an_ended_game_nobody_watches_leaves_at_once(quiet_session):
    # Arrange
    games = _registry()
    session = quiet_session(FakeGraph([]), seat_tokens=["tok"])
    games._register(session)

    # Act: the game ends
    await session.drop("test: over")

    # Assert
    assert games.get(session.game_id) is None


async def test_an_ended_game_stays_until_its_last_viewer_leaves(quiet_session):
    # Arrange: a game with two viewers
    games = _registry()
    session = quiet_session(FakeGraph([]), seat_tokens=["tok"])
    games._register(session)
    first, second = session.subscribe(), session.subscribe()

    # Round 1: the game ends
    await session.drop("test: over")
    assert games.get(session.game_id) is session  # two streams still open on it

    # Round 2: the first viewer leaves
    session.unsubscribe(first)
    assert games.get(session.game_id) is session  # one left

    # Round 3: the last viewer leaves
    session.unsubscribe(second)
    assert games.get(session.game_id) is None


async def test_a_live_game_is_never_released(quiet_session):
    # Arrange
    games = _registry()
    session = quiet_session(FakeGraph([]), seat_tokens=["tok"])
    games._register(session)

    # Act
    q = session.subscribe()
    session.unsubscribe(q)  # viewers come and go while the game is live

    # Assert
    assert games.get(session.game_id) is session
    await session.suspend()

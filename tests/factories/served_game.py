"""The server's own pieces over a real database, for the integration tests that play a hosted game.

`open_server(dsn)` builds what the server's startup builds (`server/resources.py`): the graph
runtime (the Postgres checkpoint saver, the lesson store and the compiled game graph), the
database and the game repository, and the live game registry. `ServerProcess.stop()` takes them
down in the order the server's shutdown does: every running game is suspended first
(`LiveGameRegistry.shutdown`), then the runtime and the database are closed.

The rest are the steps a test takes while a game plays: give a session the test's models, wait
for the human seat's question, answer every question until the game ends, and read the event log
the database holds.

The models never come from here: the test passes its own (`ScriptedModels`, `FakeModels`) and
`give_models` puts them in the session's graph context, as the server would find its own.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import SimpleNamespace

from server.db import Database
from server.game.game_session import GameSession
from server.game.live_game_registry import LiveGameRegistry
from server.graph_runtime import GraphRuntime
from server.storage.game_repository import GameRepository
from tests.fixtures.database import sqlalchemy_url

GAME_TIMEOUT_S = 120
"""How long any one wait on a game may take. A whole scripted game takes seconds offline; a game
that hangs fails the test when this runs out instead of holding up the suite."""


class StreamTrackingGraph:
    """The real compiled game graph, passed through unchanged, which also counts how many of its
    streams are running. A game paused on a human's question has a stream that ended; waiting
    for that, and not only for the question, means no sibling node of the paused step is still
    running in a worker thread when the test stops the server."""

    def __init__(self, graph):
        self._graph = graph
        self.streams_running = 0

    async def astream(self, *args, **kwargs):
        self.streams_running += 1
        try:
            async for part in self._graph.astream(*args, **kwargs):
                yield part
        finally:
            self.streams_running -= 1

    def __getattr__(self, name):
        return getattr(self._graph, name)


@dataclass
class ServerProcess:
    """What one server process holds, built by `open_server`."""

    runtime: GraphRuntime
    database: Database
    repository: GameRepository
    registry: LiveGameRegistry
    graph: StreamTrackingGraph

    async def stop(self) -> None:
        """Shut down as the server's lifespan does: suspend every game, then close storage."""
        try:
            await self.registry.shutdown()
        finally:
            await self.runtime.close()
            await self.database.close()


async def open_server(dsn: str, *, check_key=None) -> ServerProcess:
    """Start the graph runtime, the database and the registry on `dsn`, as the server's
    startup does. `check_key` replaces the registry's probe of a player's key with the
    provider (a test must never ask a real provider); None keeps the registry's default,
    which is only reached when a game is started with a key.

    The registry is handed the runtime's compiled graph wrapped in `StreamTrackingGraph`;
    the registry reads nothing else from the runtime (`.graph` only)."""
    runtime = GraphRuntime(dsn)
    await runtime.startup()
    database = Database(sqlalchemy_url(dsn))
    await database.startup()
    repository = GameRepository(database)
    graph = StreamTrackingGraph(runtime.graph)
    extra = {} if check_key is None else {"check_key": check_key}
    registry = LiveGameRegistry(repository, SimpleNamespace(graph=graph), **extra)
    return ServerProcess(runtime, database, repository, registry, graph)


async def accept_any_key(model: str, api_key: str) -> None:
    """The registry's key probe, answered without asking a provider: every key is accepted."""
    return None


def give_models(session: GameSession, models) -> None:
    """Put the test's models in the session's graph context, where the game's turns look for
    them (`Agents/llm_factory/game_models.py`). Call it before the session's task first runs:
    a session's task starts at the event loop's next turn, so right after `start_instant` or
    `recover_registry` returns is in time. The context dict is updated in place, because the
    session hands that same dict to every stream.

    The session's own models object holds the game's model names and the player's keys, and the
    turn code scrubs a provider's error with them. The test's object takes its place, so it is
    given the same names and keys: the game then still carries the keys where the engine can
    reach them, which is what a planted-key test needs."""
    own = session._models
    models.model, models.rescue_model = own.model, own.rescue_model
    models._api_key, models._backup_key = own._api_key, own._backup_key
    session._use_models(models)


async def wait_for_question(session: GameSession, graph: StreamTrackingGraph) -> str:
    """Wait until the game is paused on a human seat's question with its stream ended, and
    return that seat. Fails if the game ends first, or if no question comes in time."""
    async def paused() -> str:
        while True:
            if session.ended:
                raise AssertionError(f"the game ended before a human question: {session.error!r}")
            if session.pending_requests and graph.streams_running == 0:
                return next(iter(session.pending_requests))
            await asyncio.sleep(0.02)

    return await asyncio.wait_for(paused(), timeout=GAME_TIMEOUT_S)


async def delegate_until_over(session: GameSession) -> int:
    """Hand every question the game asks to the seat's own agent (`{"delegate": True}`) until
    the game ends; return how many questions were answered."""
    async def play() -> int:
        answered = 0
        while not session.ended:
            for seat in list(session.pending_requests):
                session.submit_turn({"delegate": True}, seat=seat)
                answered += 1
            await asyncio.sleep(0.02)
        return answered

    return await asyncio.wait_for(play(), timeout=GAME_TIMEOUT_S)


async def checkpoint_questions(graph, session: GameSession) -> list[dict]:
    """The questions the engine's checkpoint says the game is waiting on, as stored."""
    state = await graph.aget_state(session.config)
    return [item.value for task in state.tasks for item in (task.interrupts or ())]


async def stored_event_seqs(database: Database, game_id: str) -> list[int]:
    """The sequence numbers of a game's stored events, in order."""
    from sqlmodel import select

    from server.database_models.game import EventRow

    async with database.session() as db:
        rows = await db.execute(
            select(EventRow.seq).where(EventRow.game_id == game_id).order_by(EventRow.seq))
        return list(rows.scalars().all())

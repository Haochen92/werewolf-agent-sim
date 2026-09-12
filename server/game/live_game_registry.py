"""The table of every game this process knows about, and the moves between stages.

    (nothing) ──open_room──▶ waiting ──start──▶ running ──▶ completed | dropped
    (nothing) ──start_instant──────────────────▶ running
    row ──revive──▶ running                                    (boot, via housekeeping)
    running ──drop──▶ dropped                                  (sweep, via housekeeping)
    ended, last viewer gone ──▶ (forgotten; the database row answers for it from then on)

The process builds one registry at startup, in resources.py, and keeps it for as long as
it runs. Each entry is one game at one stage, found by its game_id: a GameLobby while
people are still joining, a GameSession once the game is being played.

The table holds only games that can still move: rooms that are waiting and games that are
running, parked ones included. A waiting room lives in memory only: its database row is
born when the game starts, so a restart closes every room, the way a matchmaking lobby
closes when its server goes away, and only running games are rebuilt at boot.

A game that has ended, by finishing, by its task dying, or by being dropped, leaves the
table as soon as its last viewer disconnects. Its row and its events were written down as
it went, so its URL keeps answering from the database, and a finished game has a replay
under the same id. That is the promise the name makes.

This is the only code that puts a game in the table or replaces one. A route collects what
the request carries and calls a single method here, and housekeeping calls ``revive`` at
boot and ``drop`` when the sweeper gives up on a game. The two endings a game reaches on
its own, its engine run finishing and its task dying, are handled by GameSession, which
records them itself and then tells the registry it is done through ``on_idle``.

The registry never looks inside a running game (turns, viewers, clocks and pacing all
belong to GameSession) and it does not know about HTTP. It raises LookupError when a game
is in the wrong stage and PermissionError when a host key does not match; the routes in
routes/rooms.py turn those into 409 and 403, and the providers in dependencies.py answer
404 for an id nobody here knows.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from Agents.config import RunConfig
from Agents.schemas.human_player import HumanTurnRequest

from server.database_models.game import DROPPED, RUNNING, GameRow
from server.game.lobby import GameLobby
from server.game.game_session import GameSession
from server.storage.game_repository import GameRepository

logger = logging.getLogger(__name__)

Entry = GameSession | GameLobby

_BYOK_EPITAPH = ("the game's API key did not survive the server restart "
                 "(keys are never stored) — start a new game")


class LiveGameRegistry:
    """Every waiting room and running game in this process, found by game_id, together
    with the methods that move a game from one stage to the next."""

    def __init__(self, repository: GameRepository, graph_runtime) -> None:
        self._repository = repository
        self._graph_runtime = graph_runtime  # .graph is None when Postgres is unconfigured
        self._entries: dict[str, Entry] = {}

    # -- lookup ---------------------------------------------------------------------------

    def get(self, game_id: str) -> Entry | None:
        return self._entries.get(game_id)

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def lobbies(self) -> list[GameLobby]:
        return [e for e in self._entries.values() if isinstance(e, GameLobby)]

    @property
    def sessions(self) -> list[GameSession]:
        return [e for e in self._entries.values() if isinstance(e, GameSession)]

    def _register(self, session: GameSession) -> None:
        """Register the game session keyed by its game_id.
        Attaches the callback _release to the session as its on_idle handler; the session
        runs it once it has ended and no viewers are left.
        The step every door shares; tests call it directly to seat a session
        without starting it."""

        session.on_idle = lambda: self._release(session.game_id)
        self._entries[session.game_id] = session

    def _release(self, game_id: str) -> None:
        """Remove an ended game from the live registry. The game and associated events are
        already persisted in the database."""
        entry = self._entries.get(game_id)
        if isinstance(entry, GameSession) and entry.ended:
            del self._entries[game_id]
            logger.info("game %s: left the live registry", game_id)

    @property
    def durable(self) -> bool:
        """Whether games persist across restarts (a durable graph is configured)."""
        return self._graph_runtime.graph is not None

    def _require_lobby(self, game_id: str) -> GameLobby:
        """Fetch the waiting room for join, lock and start, or say why there is none: the
        id is unknown, or the game has already started. Raises LookupError either way,
        which the routes turn into a 409."""
        entry = self._entries.get(game_id)
        if entry is None:
            raise LookupError("unknown game")
        if not isinstance(entry, GameLobby):
            raise LookupError("game already started")
        return entry

    # -- open a room: (nothing) -> waiting ------------------------------------------------

    async def open_room(self, *, api_key: str = "", model: str = "",
                        name: str = "") -> GameLobby:
        """Open a waiting room: build it and register it in the table. Nothing is written
        to the database until the game starts; a room that never starts leaves no trace.
        Its id is the id the running game will keep, so one identifier covers the room
        and the game it becomes."""
        room = GameLobby(api_key=api_key, model=model, name=name)
        self._entries[room.game_id] = room
        return room

    async def join(self, game_id: str, name: str) -> str:
        """Claim a seat and return its secret token. LookupError when the room is
        locked, full, or already started."""
        room = self._require_lobby(game_id)
        return room.join(name)

    async def lock(self, game_id: str, host_key: str, locked: bool) -> GameLobby:
        """Lock or unlock a room. A locked room turns new joins away but keeps the players
        already in it. Only the host may do this."""
        room = self._require_lobby(game_id)
        if host_key != room.host_key:
            raise PermissionError("only the host may lock the room")
        room.locked = locked
        return room

    # -- → running ------------------------------------------------------------------------

    async def start(self, game_id: str, host_key: str) -> GameSession:
        """Replace the waiting room with a running game under the same id. Only the host
        may do this. Nothing is awaited between checking the room and swapping it out, so
        a second start or a late join cannot slip in halfway through."""
        room = self._require_lobby(game_id)
        if host_key != room.host_key:
            raise PermissionError("only the host may start the game")
        session = GameSession(
            room.run_config(), api_key=room.api_key, model=room.model,
            seat_tokens=room.tokens, graph=self._graph_runtime.graph,
            repository=self._repository)
        return await self._launch(
            session, model=room.model, byok=bool(room.api_key), room_name=room.name,
            seats=[seat._asdict() for seat in room.seats])

    async def start_instant(self, run_config: RunConfig, *, api_key: str, model: str,
                            seat_tokens: list[str]) -> GameSession:
        """Start a game that never had a waiting room: the solo and all-AI door,
        POST /games."""
        session = GameSession(
            run_config, api_key=api_key, model=model, seat_tokens=seat_tokens,
            graph=self._graph_runtime.graph, repository=self._repository)
        return await self._launch(
            session, model=model, byok=bool(api_key),
            seats=[{"name": "human", "token": token} for token in seat_tokens])

    async def _launch(self, session: GameSession, **row_fields) -> GameSession:
        """The step both doors share once a game is about to run: put the session in the
        table, write its row (the first write for this game), and start its task."""
        self._register(session)
        await self._repository.upsert_game(session.game_id, status="running", **row_fields)
        session.start()
        return session

    # -- running → dropped, from outside --------------------------------------------------

    async def drop(self, game_id: str, reason: str) -> None:
        """Drop a game nobody is going to finish. A waiting room is removed from the
        registry; it has no row. A running game is stopped and its row marked dropped
        with the reason; it leaves the registry when its last viewer disconnects."""
        entry = self._entries.get(game_id)
        if isinstance(entry, GameLobby):
            del self._entries[game_id]
            return
        if isinstance(entry, GameSession):
            await entry.abandon(reason)
        await self._repository.upsert_game(game_id, status=DROPPED, error=reason)

    # -- row → entry (boot) ---------------------------------------------------------------

    async def revive(self, row: GameRow) -> Entry | None:
        """Rebuild one running game from what was written down, after a restart. Three
        sources are used, each the authority on one thing: the game row holds the identity,
        the seats and the status; the events table holds everything the players were sent;
        the engine checkpoint holds where the game actually is, including the questions it
        was waiting on. Only running rows are rebuilt: a waiting room has no row, so a
        restart closes it.

        A game funded by a player's own key cannot come back, because the key itself was
        never stored: its row is marked dropped with an error saying why, and nothing is
        kept in memory. The same goes for a row still marked running whose engine had in
        fact finished: it is completed and forgotten. Returns None in both cases."""
        if row.status != RUNNING:  # recovery selects running rows; anything else is inert
            return None

        graph = self._graph_runtime.graph
        session = GameSession(
            RunConfig(game_id=row.game_id, human_player=len(row.seats),
                      memory_persistence={"dump_enabled": False}),
            model=row.model, graph=graph,
            seat_tokens=[s["token"] for s in row.seats],
            repository=self._repository)
        session.log = await self._repository.load_events(row.game_id)
        session.translator.hydrate(session.log)
        session.human_players = list(row.human_players)
        session.game_over = any(e.type == "game_over" for e in session.log)
        session._persisted = len(session.log)
        session._persisted_humans = list(row.human_players)
        self._register(session)

        if row.byok:
            await self._repository.upsert_game(
                row.game_id, status=DROPPED, error=_BYOK_EPITAPH)
            await session.abandon(_BYOK_EPITAPH)  # ended and unwatched: leaves at once
            return None

        state = await graph.aget_state(session.config)
        if not state.next:  # the game actually finished; the row was a stale 'running'
            await self._repository.complete_game(
                row.game_id, session.log, len(session.human_players))
            session._end()
            return None

        # Re-park every interrupt the checkpoint holds (the returning-player view),
        # then resume: parked games wait for /turns, mid-generation crashes continue.
        for item in (i for t in state.tasks for i in (t.interrupts or ())):
            request = HumanTurnRequest.model_validate(item.value)
            session.pending_requests[request.player_id] = request
            session._pending_ids[request.player_id] = (
                getattr(item, "id", "") or request.player_id)
            session._promises[request.player_id] = (
                asyncio.get_running_loop().create_future())
            session.clocks.arm(request)  # a no-op for solo tables
        if session.pending_requests:
            # How long the game has been waiting survives the restart: one parked for a
            # day before the reboot is still a day old, not newly parked.
            session.parked_since = row.updated_at or datetime.now(timezone.utc)
        session.start_recovered(waiting_on_humans=bool(session.pending_requests))
        return session

    # -- process end ----------------------------------------------------------------------

    async def shutdown(self) -> None:
        """Cancel every running game's task. What each one had reached is already
        written down, so the next boot picks them up again."""
        sessions = self.sessions
        if sessions:
            logger.info("shutting down %d game session(s)", len(sessions))
            await asyncio.gather(*(s.shutdown() for s in sessions))

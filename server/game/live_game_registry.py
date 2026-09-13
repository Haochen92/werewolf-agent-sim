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
from server.game.key_check import check_key
from server.game.lobby import GameLobby
from server.game.game_session import GameSession
from server.storage.game_repository import GameRepository

logger = logging.getLogger(__name__)

Entry = GameSession | GameLobby


class LiveGameRegistry:
    """Every waiting room and running game in this process, found by game_id, together
    with the methods that move a game from one stage to the next."""

    def __init__(self, repository: GameRepository, graph_runtime, *,
                 check_key=check_key) -> None:
        self._repository = repository
        self._graph_runtime = graph_runtime  # .graph is None when Postgres is unconfigured
        self._check_key = check_key  # the provider probe; tests hand in a fake
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
            await entry.drop(reason)
        await self._repository.upsert_game(game_id, status=DROPPED, error=reason)

    # -- after a restart: rebuild each running row, resume it, or wait for its key ---------

    async def revive(self, row: GameRow) -> Entry | None:
        """Rebuild one game from its database row after a restart, and set it moving
        again if it can be. Only running rows qualify; a waiting room has no row, so a
        restart closes it.

        The game object is put back together from the row (identity, seats, model) and
        the events table (everything the players were sent). If the house paid for the
        game it continues at once. If a player's key paid for it, the key was never
        stored: the game is filed without a task and waits until a seat holder sends the
        key again, through ``resume_with_key``. Returns None for a row whose game had in fact
        already finished; that row is marked completed instead."""
        if row.status != RUNNING:  # recovery selects running rows; anything else is inert
            return None

        session = GameSession(
            RunConfig(game_id=row.game_id, human_player=len(row.seats),
                      memory_persistence={"dump_enabled": False}),
            model=row.model, graph=self._graph_runtime.graph,
            seat_tokens=[s["token"] for s in row.seats],
            repository=self._repository)
        session.reload_history(await self._repository.load_events(row.game_id),
                             row.human_players)
        self._register(session)

        if row.byok:
            # The sweeper's clock runs from the row's last write, as for a parked turn.
            session.awaiting_key = True
            session.parked_since = row.updated_at or datetime.now(timezone.utc)
            logger.info("game %s: revived awaiting its player's key", row.game_id)
            return session
        return await self._resume_from_checkpoint(session, parked_since=row.updated_at)

    async def _resume_from_checkpoint(
            self, session: GameSession, *, parked_since: datetime | None) -> GameSession | None:
        """Start a rebuilt game's task from where the engine checkpoint says it stopped.
        Any question the engine was waiting on when the process died is parked again
        first, so the returning player sees the same prompt. ``parked_since`` is when
        that wait began, so a game parked for a day before the restart is still a day
        old. If the checkpoint shows the game had already finished, the row is marked
        completed and None is returned."""
        graph = self._graph_runtime.graph
        state = await graph.aget_state(session.config)
        if not state.next:  # the game actually finished; the row was a stale 'running'
            await self._repository.complete_game(
                session.game_id, session.log, len(session.human_players))
            session._end()
            return None

        for item in (i for t in state.tasks for i in (t.interrupts or ())):
            session.park(HumanTurnRequest.model_validate(item.value), getattr(item, "id", ""))
        if session.pending_requests:
            session.parked_since = parked_since or datetime.now(timezone.utc)
        session.resume_game(waiting_on_humans=bool(session.pending_requests))
        return session

    async def resume_with_key(self, game_id: str, api_key: str) -> GameSession:
        """Take a seat holder's key for a game that has been waiting for one since a
        restart, and set the game moving again. The key is tried on the provider first:
        if the provider refuses it, ValueError carries the complaint and the game keeps
        waiting. LookupError when the game is not waiting for a key."""
        entry = self._entries.get(game_id)
        if not isinstance(entry, GameSession) or not entry.awaiting_key:
            raise LookupError("this game is not waiting for a key")
        entry.awaiting_key = False  # claimed: a second funder meanwhile gets LookupError
        try:
            await self._check_key(entry.model, api_key)
        except ValueError:
            entry.awaiting_key = True
            raise
        entry.take_key(api_key)
        logger.info("game %s: funded again by a seat holder; resuming", game_id)
        resumed = await self._resume_from_checkpoint(
            entry, parked_since=datetime.now(timezone.utc))
        return resumed if resumed is not None else entry

    # -- process end: suspend every game so the next boot can rebuild it -------------------

    async def shutdown(self) -> None:
        """Cancel every running game's task. What each one had reached is already
        written down, so the next boot picks them up again."""
        sessions = self.sessions
        if sessions:
            logger.info("shutting down %d game session(s)", len(sessions))
            await asyncio.gather(*(s.suspend() for s in sessions))

"""The middle lifecycle: every game this process knows, and how one moves between stages.

    (nothing) ──open_room──▶ waiting ──start──▶ running ──▶ completed | dropped
    (nothing) ──start_instant──────────────────▶ running
    row ──revive──▶ waiting | running                          (boot, via housekeeping)
    running ──drop──▶ dropped                                  (sweep, via housekeeping)

The process owns one registry (built in resources.py, alive as long as the process); each
entry is one game at one stage — a GameLobby while waiting, a GameSession once running.
Transitions that originate OUTSIDE a game live here, and this is the only code that puts
an entry into the table or swaps one: the routes gather inputs and call one method each;
housekeeping calls ``revive`` at boot and ``drop`` on the sweep. The two endings that
originate INSIDE a game — its graph finishing (completed) and its task dying (dropped) —
stay in GameSession, which reports them to the repository itself; the entry then serves
history until the process ends.

What this is not: it never looks inside a session (turns, viewers, clocks, pacing are the
session's), never speaks HTTP (routes translate LookupError → 409 and PermissionError →
403; the dependency layer owns the 404), and never touches events or checkpoints beyond
what a transition must write.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from Agents.config import RunConfig
from Agents.schemas.human_player import HumanTurnRequest

from server.database_models.game import DROPPED, WAITING, GameRow
from server.game.lobby import GameLobby, HumanSeat
from server.game.runtime import GameSession
from server.storage.game_repository import GameRepository

logger = logging.getLogger(__name__)

Entry = GameSession | GameLobby

_BYOK_EPITAPH = ("the game's API key did not survive the server restart "
                 "(keys are never stored) — start a new game")


class GameRegistry:
    """Every waiting room and running game, keyed by game_id, plus the transitions."""

    def __init__(self, repository: GameRepository, graph_runtime) -> None:
        self._repository = repository
        self._graph_runtime = graph_runtime  # .graph is None when Postgres is unconfigured
        self._entries: dict[str, Entry] = {}

    # -- lookup ---------------------------------------------------------------------------

    def get(self, game_id: str) -> Entry | None:
        return self._entries.get(game_id)

    def __len__(self) -> int:
        return len(self._entries)

    def lobbies(self) -> list[GameLobby]:
        return [e for e in self._entries.values() if isinstance(e, GameLobby)]

    def sessions(self) -> list[GameSession]:
        return [e for e in self._entries.values() if isinstance(e, GameSession)]

    def adopt(self, entry: Entry) -> None:
        """Place a prepared entry under its own id (recovery, tests)."""
        self._entries[entry.game_id] = entry

    @property
    def durable(self) -> bool:
        """Whether games persist across restarts (a durable graph is configured)."""
        return self._graph_runtime.graph is not None

    def _lobby(self, game_id: str) -> GameLobby:
        entry = self._entries.get(game_id)
        if entry is None:
            raise LookupError("unknown game")
        if not isinstance(entry, GameLobby):
            raise LookupError("game already started")
        return entry

    # -- nothing → waiting ----------------------------------------------------------------

    async def open_room(self, *, api_key: str = "", model: str = "",
                        name: str = "") -> GameLobby:
        """A lobby whose id stays stable when the game starts: the room and its eventual
        running game share one registry/database identity for their full life."""
        room = GameLobby(api_key=api_key, model=model, name=name)
        self._entries[room.game_id] = room
        await self._repository.upsert_game(
            room.game_id, status=WAITING, host_key=room.host_key, model=model,
            byok=bool(api_key), seats=[], room_name=room.name,
            created_at=room.created_at)
        return room

    async def join(self, game_id: str, name: str) -> tuple[int, str]:
        """Claim a seat; returns (1-based position, the seat's secret token).
        LookupError when the room is locked, full, or already started."""
        room = self._lobby(game_id)
        position, token = room.join(name)
        await self._repository.upsert_game(
            game_id, seats=[seat._asdict() for seat in room.seats])
        return position, token

    async def lock(self, game_id: str, host_key: str, locked: bool) -> GameLobby:
        room = self._lobby(game_id)
        if host_key != room.host_key:
            raise PermissionError("only the host may lock the room")
        room.locked = locked
        await self._repository.upsert_game(game_id, locked=locked)
        return room

    # -- → running ------------------------------------------------------------------------

    async def start(self, game_id: str, host_key: str) -> GameSession:
        """Replace the lobby with a running session under the SAME id. No await sits
        between validating the lobby and the in-memory swap, so another /start or
        /join cannot interleave with it."""
        room = self._lobby(game_id)
        if host_key != room.host_key:
            raise PermissionError("only the host may start the game")
        session = GameSession(
            room.run_config(), api_key=room.api_key, model=room.model,
            seat_tokens=room.tokens, graph=self._graph_runtime.graph,
            repository=self._repository)
        return await self._launch(
            session, seats=[seat._asdict() for seat in room.seats])

    async def start_instant(self, run_config: RunConfig, *, api_key: str, model: str,
                            seat_tokens: list[str]) -> GameSession:
        """Born running: the solo and LLM-only door. No waiting stage exists for it."""
        session = GameSession(
            run_config, api_key=api_key, model=model, seat_tokens=seat_tokens,
            graph=self._graph_runtime.graph, repository=self._repository)
        return await self._launch(
            session, model=model, byok=bool(api_key),
            seats=[{"name": "human", "token": token} for token in seat_tokens])

    async def _launch(self, session: GameSession, **row_fields) -> GameSession:
        """The one 'now it is running' step both doors share: swap in the entry, write
        the row, start the task."""
        self._entries[session.game_id] = session
        await self._repository.upsert_game(session.game_id, status="running", **row_fields)
        session.start()
        return session

    # -- running → dropped, from outside --------------------------------------------------

    async def drop(self, game_id: str, reason: str) -> None:
        """End a game nobody will finish. A session stays in the table as history with
        the reason as its epitaph; a lobby simply disappears."""
        entry = self._entries.get(game_id)
        if isinstance(entry, GameSession):
            await entry.abandon(reason)
        elif isinstance(entry, GameLobby):
            del self._entries[game_id]
        await self._repository.upsert_game(game_id, status=DROPPED, error=reason)

    # -- row → entry (boot) ---------------------------------------------------------------

    async def revive(self, row: GameRow) -> Entry | None:
        """Rebuild one entry from its persisted facts after a restart. Facts come from
        three places, each authoritative for one thing: the game row (identity, seats,
        host_key, status, byok), the events table (the wire log), and the LangGraph
        checkpoint (where the game actually is, parked interrupts included).

        BYOK rows: the key was never stored, so the game cannot be resumed as funded —
        a session revives dead with a clear error (its history still serves); a BYOK
        waiting room is simply marked dropped."""
        if row.status == WAITING:
            if row.byok:
                await self._repository.upsert_game(
                    row.game_id, status=DROPPED, error=_BYOK_EPITAPH)
                return None
            lobby = GameLobby(model=row.model, name=row.room_name)
            lobby.game_id = row.game_id  # identity comes from the row, not fresh uuids
            lobby.host_key = row.host_key
            lobby.locked = row.locked
            if row.created_at is not None:  # keep the original TTL clock, not boot time
                lobby.created_at = row.created_at
            lobby.seats = [HumanSeat(**s) for s in row.seats]
            self._entries[row.game_id] = lobby
            return lobby

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
        self._entries[row.game_id] = session

        if row.byok:
            session.error = _BYOK_EPITAPH
            session._finished.set()  # no task: history is served, play is over
            await self._repository.upsert_game(
                row.game_id, status=DROPPED, error=_BYOK_EPITAPH)
            return session

        state = await graph.aget_state(session.config)
        if not state.next:  # the game actually finished; the row was a stale 'running'
            session._finished.set()
            await self._repository.complete_game(
                row.game_id, session.log, len(session.human_players))
            return session

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
            # The retention clock survives the restart: a row parked for a day before
            # the reboot is still a day old, not newborn (seat_continuity.md §7).
            session.parked_since = row.updated_at or datetime.now(timezone.utc)
        session.start_recovered(waiting_on_humans=bool(session.pending_requests))
        return session

    # -- process end ----------------------------------------------------------------------

    async def shutdown(self) -> None:
        """Cancel every running task; their checkpoints and event tails are recovered
        on the next boot."""
        sessions = self.sessions()
        if sessions:
            logger.info("shutting down %d game session(s)", len(sessions))
            await asyncio.gather(*(s.shutdown() for s in sessions))

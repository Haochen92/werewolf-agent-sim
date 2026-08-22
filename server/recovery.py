"""Boot recovery: rebuild the registry from persisted facts after a restart.

The counterpart of "persistence writes facts down": this module re-creates the living
machinery from them. Facts come from three places, each authoritative for one thing —
the game row (identity: seats/tokens, host_key, status, byok), the events table
(the wire log: SSE replay + the translator rebuild), and the LangGraph checkpoint
(engine state: where the game actually is, including parked interrupts, read via
aget_state — probe-verified recoverable from a fresh process).

Per-row failure policy: recovery of one game must never take the server down or block
the others — a row that fails to revive is marked dead with the reason and skipped.

BYOK rows (ruled): the key was never stored, so the game cannot be resumed as funded —
revived as a dead session with a clear error (status/SSE still serve its history);
a BYOK waiting room is simply marked dead (nothing to serve yet).
"""

from __future__ import annotations

import asyncio
import logging

from Agents.config import RunConfig
from Agents.schemas.human_player import HumanTurnRequest

from server.database_models.game import DROPPED, WAITING, GameRow
from server.game_repository import GameRepository
from server.lobby import GameLobby, HumanSeat
from server.runtime import GameSession

logger = logging.getLogger(__name__)

_BYOK_EPITAPH = ("the game's API key did not survive the server restart "
                 "(keys are never stored) — start a new game")


async def recover_registry(games: dict, repository: GameRepository, graph) -> None:
    """Fill the fresh registry from every waiting/running row. Called by the lifespan
    after the graph runtime starts; a no-op when Postgres is unconfigured."""
    if graph is None:
        return
    rows = await repository.load_recoverable_games()
    for row in rows:
        try:
            entry = await _revive(row, repository, graph)
            if entry is not None:
                games[row.game_id] = entry
        except Exception:
            logger.exception("game %s: recovery failed; marking dead", row.game_id)
            await repository.upsert_game(
                row.game_id, status=DROPPED, error="recovery failed on restart")
    if rows:
        logger.info("recovery: %d open row(s) processed, %d revived",
                    len(rows), len(games))


async def _revive(row: GameRow, repository: GameRepository, graph):
    if row.status == WAITING:
        if row.byok:
            await repository.upsert_game(
                row.game_id, status=DROPPED, error=_BYOK_EPITAPH)
            return None
        lobby = GameLobby(model=row.model, name=row.room_name)
        lobby.game_id = row.game_id  # identity comes from the row, not fresh uuids
        lobby.host_key = row.host_key
        lobby.locked = row.locked
        if row.created_at is not None:  # keep the original TTL clock, not boot time
            lobby.created_at = row.created_at
        lobby.seats = [HumanSeat(**s) for s in row.seats]
        return lobby

    # A running game: rebuild the session shell, then hydrate the three fact sources.
    session = GameSession(
        RunConfig(game_id=row.game_id, human_player=len(row.seats),
                  memory_persistence={"dump_enabled": False}),
        graph=graph,
        seat_tokens=[s["token"] for s in row.seats],
        repository=repository,
    )
    session.log = await repository.load_events(row.game_id)
    session.translator.hydrate(session.log)
    session.human_players = list(row.human_players)
    session.game_over = any(e.type == "game_over" for e in session.log)
    session._persisted = len(session.log)
    session._persisted_humans = list(row.human_players)

    if row.byok:
        session.error = _BYOK_EPITAPH
        session._finished.set()  # no task: history is served, play is over
        await repository.upsert_game(
            row.game_id, status=DROPPED, error=_BYOK_EPITAPH)
        return session

    state = await graph.aget_state(session.config)
    if not state.next:  # the game actually finished; the row was a stale 'running'
        session._finished.set()
        await repository.complete_game(
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
        if len(row.seats) > 1:
            session._arm_afk_timer(request)
    session.start_recovered(waiting_on_humans=bool(session.pending_requests))
    return session

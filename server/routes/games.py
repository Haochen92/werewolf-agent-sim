"""Running-game creation, status, turns, and SSE transport."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Annotated, AsyncIterator, Callable
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Response
from fastapi.responses import StreamingResponse

from Agents.config import RunConfig
from Agents.turn.human_turn import HumanTurnContractError
from server.dependencies import (
    Game,
    GameRepositoryDep,
    GamesRegistry,
    GraphRuntimeDep,
    Room,
    SeatToken,
)
from server.lobby import MAX_HUMAN_SEATS, GameLobby
from server.runtime import GameSession, entitled
from server.schemas.requests import GameCreated, GameStatus, NewGame, TurnAccepted

from ._shared import check_byok, set_seat_cookie

logger = logging.getLogger(__name__)

_HEARTBEAT_SECONDS = 15.0

router = APIRouter(tags=["games"])


@router.post(
    "/games",
    response_model=GameCreated,
    summary="Instant start: solo human (role choice) or LLM-only",
)
async def create_game(
    body: NewGame,
    games: GamesRegistry,
    response: Response,
    repository: GameRepositoryDep,
    graph_runtime: GraphRuntimeDep,
) -> GameCreated:
    check_byok(body.api_key, body.model)
    seat_tokens = [str(uuid4())] if body.human or body.human_role is not None else []
    session = GameSession(
        RunConfig(
            human_player=len(seat_tokens),
            human_role=body.human_role,
            memory_persistence={"dump_enabled": False},
        ),
        api_key=body.api_key,
        model=body.model,
        seat_tokens=seat_tokens,
        graph=graph_runtime.graph,
        repository=repository,
    )
    games[session.game_id] = session
    await repository.upsert_game(
        session.game_id,
        status="running",
        model=body.model,
        byok=bool(body.api_key),
        seats=[{"name": "human", "token": token} for token in seat_tokens],
    )
    session.start()
    if seat_tokens:
        set_seat_cookie(response, session.game_id, seat_tokens[0])
    return GameCreated(
        game_id=session.game_id,
        seat_token=seat_tokens[0] if seat_tokens else None,
    )


@router.get("/games/{game_id}", response_model=GameStatus, summary="Status snapshot")
async def game_status(session: Room, token: SeatToken) -> GameStatus:
    if token and session.position_of(token) is None:
        raise HTTPException(status_code=403, detail="unknown seat token")
    if isinstance(session, GameLobby):
        return GameStatus(
            game_id=session.game_id,
            state="waiting",
            server_time=datetime.now(timezone.utc).isoformat(),
            players=list(session.players),
            max_seats=MAX_HUMAN_SEATS,
            name=session.name,
            locked=session.locked,
        )
    return GameStatus(
        game_id=session.game_id,
        state="finished" if session.game_over else "running",
        server_time=datetime.now(timezone.utc).isoformat(),
        human_players=session.human_players,
        you=(session.seat_for_token(token) or None) if token else None,
        pending_input=bool(session.pending_requests),
        pending_seats=sorted(session.pending_requests),
        deadlines=dict(session.turn_deadlines),
        game_over=session.game_over,
        last_seq=session.log[-1].seq if session.log else 0,
        alive_role_counts=session.public_alive_counts(),
        error=session.error,
    )


@router.post(
    "/games/{game_id}/turns",
    response_model=TurnAccepted,
    summary="Submit the human seat's action",
)
async def submit_turn(session: Game, body: dict, token: SeatToken) -> TurnAccepted:
    if not token:
        raise HTTPException(
            status_code=403,
            detail=(
                "turns require a seat cookie — claim a seat via POST /join "
                "(or restore a lost cookie via POST /rejoin)"
            ),
        )
    seat = session.seat_for_token(token)
    if seat is None:
        raise HTTPException(status_code=403, detail="unknown seat token")
    if not seat:
        raise HTTPException(status_code=409, detail="seats not dealt yet")
    try:
        session.submit_turn(body, seat=seat)
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except HumanTurnContractError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return TurnAccepted()


@router.get("/games/{game_id}/events", summary="SSE event stream")
async def event_stream(
    session: Game,
    token: SeatToken,
    last_seq: int = 0,
    last_event_id: Annotated[str | None, Header()] = None,
) -> StreamingResponse:
    """Stream entitled durable events plus public ephemeral pacing frames.

    ``last_seq`` is the cursor frozen into the original URL. On automatic browser
    reconnection, ``Last-Event-ID`` carries the live cursor and therefore wins when
    valid. Pacing frames have no ID, so they never advance that durable cursor.
    """
    if token and session.seat_for_token(token) is None:
        raise HTTPException(status_code=403, detail="unknown seat token")
    if last_event_id is not None:
        try:
            last_seq = int(last_event_id)
        except ValueError:
            pass

    def viewer_seat() -> str:
        return (session.seat_for_token(token) or "") if token else ""

    return StreamingResponse(
        _sse(session, viewer_seat, last_seq),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _frame(kind: str, event) -> str:
    """Format one durable or ephemeral event as an SSE protocol frame."""
    seq = getattr(event, "seq", None)
    id_line = f"id: {seq}\n" if seq is not None else ""
    return f"{id_line}event: {kind}\ndata: {event.model_dump_json()}\n\n"


async def _sse(
    session: GameSession,
    viewer_seat: Callable[[], str],
    last_seq: int,
) -> AsyncIterator[str]:
    """Subscribe before replaying the log, deduplicate overlap, then stream live.

    Subscribe-first ensures each event reaches either the snapshot or queue; the
    overlap can duplicate, and ``sent`` removes that safely. Snapshot iteration uses
    a list because this generator suspends at every yield while the game appends.
    Entitlement and token-to-seat resolution are evaluated per delivery because
    roles may be dealt after connection and observer-only events unlock at game over.
    The cursor is also entitlement-aware: it cannot claim an event the viewer was
    not allowed to receive while the game was live. Heartbeats keep proxy connections
    alive; they do not impose a player turn timeout.
    """
    q = session.subscribe()
    sent: set[int] = set()
    logger.debug(
        "game %s: viewer connected (seat=%r, cursor=%d)",
        session.game_id,
        viewer_seat(),
        last_seq,
    )

    def may_see(event) -> bool:
        return entitled(event, viewer_seat(), session.translator.roles, session.game_over)

    def cursor_skips(event) -> bool:
        return event.seq <= last_seq and entitled(
            event, viewer_seat(), session.translator.roles, False
        )

    try:
        for event in list(session.log):
            if not cursor_skips(event) and may_see(event):
                sent.add(event.seq)
                yield _frame("game", event)

        while True:
            try:
                kind, event = await asyncio.wait_for(
                    q.get(), timeout=_HEARTBEAT_SECONDS
                )
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
                continue
            if kind == "pacing":
                yield _frame("pacing", event)
                continue
            if event.seq in sent or cursor_skips(event):
                continue
            if may_see(event):
                sent.add(event.seq)
                yield _frame("game", event)
            if event.type == "game_over":
                for held in list(session.log):
                    if held.seq not in sent and not cursor_skips(held):
                        sent.add(held.seq)
                        yield _frame("game", held)
    finally:
        session.unsubscribe(q)
        logger.debug(
            "game %s: viewer disconnected (seat=%r)",
            session.game_id,
            viewer_seat(),
        )

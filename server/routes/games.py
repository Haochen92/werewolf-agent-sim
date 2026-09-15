"""Running-game creation, status, turns, and SSE transport."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Annotated, AsyncIterator
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Response
from fastapi.responses import StreamingResponse

from Agents.config import RunConfig
from Agents.turn.human_turn import HumanTurnContractError
from server.dependencies import House, Game, GamesRegistry, Room, SeatToken
from server.game.lobby import MAX_HUMAN_SEATS, GameLobby
from server.database_models.game import COMPLETED, GameRow
from server.game.entitlement import entitled
from server.game.game_session import GameSession
from server.schemas.requests import FundGame, GameCreated, GameStatus, NewSoloGame, TurnAccepted

from ._shared import authorize_model, set_seat_cookie

logger = logging.getLogger(__name__)

_HEARTBEAT_SECONDS = 15.0

router = APIRouter(tags=["games"])


@router.post(
    "/games",
    response_model=GameCreated,
    summary="Instant start: solo human (role choice) or LLM-only",
)
async def create_game(
    body: NewSoloGame,
    games: GamesRegistry,
    house: House,
    response: Response,
) -> GameCreated:
    model = await authorize_model(house, body.api_key, body.model)
    seat_tokens = [str(uuid4())] if body.human or body.human_role is not None else []
    session = await games.start_instant(
        RunConfig(
            human_player=len(seat_tokens),
            human_role=body.human_role,
            memory_persistence={"dump_enabled": False},
        ),
        api_key=body.api_key,
        model=model,
        seat_tokens=seat_tokens,
    )
    if seat_tokens:
        set_seat_cookie(response, session.game_id, seat_tokens[0])
    return GameCreated(
        game_id=session.game_id,
        seat_token=seat_tokens[0] if seat_tokens else None,
    )


@router.get("/games/{game_id}", response_model=GameStatus, summary="Status snapshot")
async def game_status(session: Room, token: SeatToken) -> GameStatus:
    if isinstance(session, GameRow):
        return _archived_status(session, token)
    if token and not session.owns(token):
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
        awaiting_key=session.awaiting_key,
        pending_input=bool(session.pending_requests),
        pending_seats=sorted(session.pending_requests),
        deadlines=dict(session.turn_deadlines),
        game_over=session.game_over,
        last_seq=session.log[-1].seq if session.log else 0,
        alive_role_counts=session.public_alive_counts,
        error=session.error,
    )


def _archived_status(row: GameRow, token: str) -> GameStatus:
    """The snapshot of a game that has ended and left the live registry: the row says how
    it ended. A stale seat cookie is not an error here; it just names the seat you held."""
    tokens = [seat.get("token", "") for seat in row.seats]
    you = None
    if token and token in tokens:
        i = tokens.index(token)
        you = row.human_players[i] if i < len(row.human_players) else None
    finished = row.status == COMPLETED
    return GameStatus(
        game_id=row.game_id,
        state="finished" if finished else "dropped",
        server_time=datetime.now(timezone.utc).isoformat(),
        human_players=list(row.human_players),
        you=you,
        game_over=finished,
        winner=row.winner,
        error=row.error,
        archived=True,
    )


@router.post(
    "/games/{game_id}/key",
    response_model=GameStatus,
    summary="Resume a key-funded game after a restart by supplying the key again",
)
async def fund_game(session: Game, body: FundGame, token: SeatToken,
                    games: GamesRegistry) -> GameStatus:
    """Any seat holder may fund the resume; spectators may not. The key is tried on the
    provider first (422 with its complaint), then the game continues from its checkpoint.
    409 when the game is not waiting for a key."""
    if not token or not session.owns(token):
        raise HTTPException(status_code=403, detail="only a seat holder may fund this game")
    try:
        await games.resume_with_key(session.game_id, body.api_key)
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return await game_status(session, token)


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

    return StreamingResponse(
        _sse(session, token, last_seq),
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
    token: str,
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
    q = session.subscribe(token)  # also the presence signal for a human seat

    def viewer_seat() -> str:  # re-read per event: seats are dealt after streams open
        return session.seat_of_viewer(token)

    sent: set[int] = set()
    logger.info(
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
        logger.info(
            "game %s: viewer disconnected (seat=%r)",
            session.game_id,
            viewer_seat(),
        )

"""The thin HTTP surface: an APIRouter over the runtime layer, composed by create_app().

GET  /health               -> liveness probe for the container/proxy
GET  /models               -> the BYOK menu: tested game models + their rescue models
POST /games                -> instant start (solo human with optional role choice, or
                              LLM-only; optional BYOK api_key + model from the tested
                              list fund the game's calls — key held in memory only)
POST /rooms                -> create a multiplayer waiting room (BYOK only; humans join
                              via /join, roles always random; response carries host_key)
POST /games/{id}/join      -> claim a human seat in a waiting room (rooms deal
                              random roles; role choice is solo-only, via POST /games)
POST /games/{id}/rejoin    -> restore a lost seat cookie from the token's body copy
POST /games/{id}/start     -> the host starts the room's game (?host_key=); the
                              GameLobby is swapped for a GameSession under the same id
GET  /games/{id}           -> status snapshot (state, lobby roster / human seat,
                              pending input, public census)
GET  /games/{id}/events    -> SSE: tier-filtered durable events (`event: game`, id = seq,
                              catch-up via ?last_seq=) + ephemeral pacing (`event: pacing`).
                              At game_over the withheld observer backlog flushes (R7).
POST /games/{id}/turns     -> the human's action; validated against the pending
                              input_request via the CLI driver's HITL contract, then resumed.

The games registry lives on app.state (created by the lifespan, which also cancels live
game tasks on shutdown); routes resolve it through server.dependencies. CORS origins come
from server.config (the browser frontend is a different origin; it must send requests
with credentials, and must be SAME-SITE with the API — localhost ports in dev, sibling
subdomains deployed — for the SameSite=Lax seat cookie to ride). Viewers identify by a
per-seat secret token minted at /join (or the solo /games door), carried as an HttpOnly
cookie: proof of seat ownership for turns and private event tiers, replacing the old
trust-the-query-string ?seat=. Run: uvicorn server.app:app
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator, Callable
from uuid import uuid4

from fastapi import APIRouter, FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from Agents.config import RunConfig
from Agents.turn.human_turn import HumanTurnContractError

from server import db, replays
from server.config import server_settings
from server.dependencies import Game, GamesRegistry, Room, SeatToken, seat_cookie_name
from server.lobby import MAX_HUMAN_SEATS, GameLobby
from server.runtime import SUPPORTED_GAME_MODELS, GameSession, entitled
from server.schemas.requests import (
    GameCreated,
    GameStatus,
    JoinGame,
    ModelRow,
    ModelsMenu,
    NewGame,
    NewRoom,
    RejoinGame,
    RoomCreated,
    SeatJoined,
    TurnAccepted,
)

logger = logging.getLogger(__name__)

_HEARTBEAT_SECONDS = 15.0

router = APIRouter(tags=["games"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Owns the games registry: created at startup, live game tasks cancelled at shutdown
    (without this, uvicorn exit abandons mid-flight tasks with pending destructor noise)."""
    app.state.games = {}
    yield
    # Only started sessions hold a task; waiting lobbies have nothing to cancel.
    sessions = [s for s in app.state.games.values() if isinstance(s, GameSession)]
    if sessions:
        logger.info("shutting down %d game session(s)", len(sessions))
        await asyncio.gather(*(s.shutdown() for s in sessions))
    await db.dispose()  # the replay archive's pool; safe when never configured


def create_app() -> FastAPI:
    app = FastAPI(title="werewolf-agent-sim server", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=server_settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    app.include_router(replays.router)
    return app


@router.get("/health", summary="Liveness probe")
async def health_check() -> dict:
    return {"status": "healthy"}


@router.get("/models", response_model=ModelsMenu,
            summary="The BYOK selection menu (tested game models only)")
async def supported_models() -> ModelsMenu:
    """Tested game models, display labels, and their same-credential rescue models.
    First entry = the default for a bare key."""
    return ModelsMenu(models=[
        ModelRow(model=model, label=row.label, rescue_model=row.rescue)
        for model, row in SUPPORTED_GAME_MODELS.items()
    ])


_SEAT_COOKIE_MAX_AGE = 24 * 3600  # comfortably outlives any in-memory game


def _set_seat_cookie(response: Response, game_id: str, token: str) -> None:
    """The seat credential's transport (ruled: HttpOnly cookie — EventSource can't
    set headers, but browsers attach cookies to SSE). HttpOnly keeps it out of page
    JavaScript's reach; Path scopes it to this one game; SameSite=Lax requires the
    frontend to be same-site with the API (module docstring)."""
    response.set_cookie(
        key=seat_cookie_name(game_id), value=token,
        max_age=_SEAT_COOKIE_MAX_AGE, path=f"/games/{game_id}",
        httponly=True, samesite="lax",
    )


def _check_byok(api_key: str, model: str) -> None:
    """The BYOK gate, shared by both creation doors."""
    if model and not api_key:
        raise HTTPException(status_code=422, detail="model selection requires api_key")
    if model and model not in SUPPORTED_GAME_MODELS:
        raise HTTPException(
            status_code=422,
            detail=f"unsupported model; pick from GET /models: {sorted(SUPPORTED_GAME_MODELS)}",
        )


@router.post("/games", response_model=GameCreated,
             summary="Instant start: solo human (role choice) or LLM-only")
async def create_game(body: NewGame, games: GamesRegistry, response: Response) -> GameCreated:
    _check_byok(body.api_key, body.model)
    # The solo door mints its one seat token here — same identity mechanism as /join.
    seat_tokens = [str(uuid4())] if body.human or body.human_role is not None else []
    session = GameSession(RunConfig(
        human_player=len(seat_tokens),
        human_role=body.human_role,
        # A served game is never mined into the memory store (the CLI human-game rule).
        memory_persistence={"dump_enabled": False},
    ), api_key=body.api_key, model=body.model, seat_tokens=seat_tokens)
    games[session.game_id] = session
    session.start()
    if seat_tokens:
        _set_seat_cookie(response, session.game_id, seat_tokens[0])
    return GameCreated(game_id=session.game_id,
                       seat_token=seat_tokens[0] if seat_tokens else None)


@router.post("/rooms", response_model=RoomCreated,
             summary="Create a multiplayer waiting room (humans join via /join)")
async def create_room(body: NewRoom, games: GamesRegistry) -> RoomCreated:
    """The multiplayer door: no human/role fields exist in its contract — a room
    seats humans only through POST /join and always deals random roles. All
    per-id routes stay under /games/{id}: the /start swap keeps the id, so the
    room URL is the game URL for its whole life."""
    _check_byok(body.api_key, body.model)
    room = GameLobby(api_key=body.api_key, model=body.model)
    games[room.game_id] = room
    return RoomCreated(game_id=room.game_id, host_key=room.host_key)


@router.post("/games/{game_id}/join", response_model=SeatJoined,
             summary="Claim a human seat in a waiting room")
async def join_game(room: Room, body: JoinGame, response: Response) -> SeatJoined:
    if not isinstance(room, GameLobby):
        raise HTTPException(status_code=409, detail="game already started")
    try:
        position, token = room.join(body.name)
    except LookupError as exc:  # seats full
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _set_seat_cookie(response, room.game_id, token)
    return SeatJoined(position=position, token=token)


@router.post("/games/{game_id}/rejoin", response_model=SeatJoined,
             summary="Restore a lost seat cookie from the token's body copy")
async def rejoin_game(room: Room, body: RejoinGame, response: Response) -> SeatJoined:
    """Cookie-loss recovery (new device, cleared browsing data): the stashed body-copy
    token re-proves seat ownership and re-sets the cookie. Serves both registry phases
    — position_of lives on GameLobby and GameSession alike. A seat lost for good (both
    copies gone) is an AFK seat: the game must not stall on it (slice 4's timer)."""
    position = room.position_of(body.token)
    if position is None:
        raise HTTPException(status_code=403, detail="unknown seat token")
    _set_seat_cookie(response, room.game_id, body.token)
    return SeatJoined(position=position, token=body.token)


@router.post("/games/{game_id}/start", response_model=GameCreated,
             summary="Start the waiting room's game (host only)")
async def start_game(room: Room, games: GamesRegistry, host_key: str = "") -> GameCreated:
    """The registry swap: the GameLobby is replaced by a real GameSession under the
    same game_id (the room URL survives). Check-then-swap is atomic — no await
    between them, so a concurrent /start or /join cannot interleave."""
    if not isinstance(room, GameLobby):
        raise HTTPException(status_code=409, detail="game already started")
    if host_key != room.host_key:
        raise HTTPException(status_code=403, detail="only the host may start the game")
    session = GameSession(room.run_config(), api_key=room.api_key, model=room.model,
                          seat_tokens=room.tokens)
    games[session.game_id] = session
    session.start()
    return GameCreated(game_id=session.game_id)


@router.get("/games/{game_id}", response_model=GameStatus, summary="Status snapshot")
async def game_status(session: Room, token: SeatToken) -> GameStatus:
    # A presented-but-unknown token is a loud 403, never a silent spectator downgrade:
    # status is the poll the client watches, so this is what triggers its rejoin UX.
    if token and session.position_of(token) is None:
        raise HTTPException(status_code=403, detail="unknown seat token")
    if isinstance(session, GameLobby):
        return GameStatus(
            game_id=session.game_id,
            state="waiting",
            players=list(session.players),
            max_seats=MAX_HUMAN_SEATS,
        )
    return GameStatus(
        game_id=session.game_id,
        state="finished" if session.game_over else "running",
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


@router.post("/games/{game_id}/turns", response_model=TurnAccepted,
             summary="Submit the human seat's action")
async def submit_turn(session: Game, body: dict, token: SeatToken) -> TurnAccepted:
    # Body stays an untyped dict on purpose: validation is delegated to the HITL
    # contract (validate_human_response) — the one source of truth for action shapes.
    # The token IS the seat: it resolves to exactly one engine seat, so no addressing
    # parameter exists — you can only ever answer your own turn.
    if not token:
        raise HTTPException(status_code=403, detail=(
            "turns require a seat cookie — claim a seat via POST /join "
            "(or restore a lost cookie via POST /rejoin)"))
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
    session: Game, token: SeatToken, last_seq: int = 0,
    last_event_id: Annotated[str | None, Header()] = None,
) -> StreamingResponse:
    """Endpoint for the SSE connection — the response never ends; _sse yields frames
    for the connection's lifetime.
    token -> the seat cookie: proves which seat the viewer owns (private tiers);
                    "" = spectator (public tier only), unknown token = 403.
    last_seq: int -> the client's own cursor: the last event id it already has; frozen at
                    connection time. First connection to game starts at 0.
    Last-Event-ID header -> the living cursor (ruled 2026-08-18): the browser's auto-
                    reconnect reuses the ORIGINAL url verbatim (query cursor = a fossil
                    from construction) and carries its real position in this header.
                    Header wins when present; only durable seqs ever land in it because
                    pacing frames carry no id line.
    """
    if token and session.seat_for_token(token) is None:
        raise HTTPException(status_code=403, detail="unknown seat token")
    if last_event_id is not None:
        try:
            last_seq = int(last_event_id)
        except ValueError:
            pass  # garbage header -> fall back to the query cursor

    def viewer_seat() -> str:
        # Re-resolved per entitlement check, never frozen at connect time: a player's
        # EventSource connects the moment /start returns, BEFORE INITIALIZE_GAME deals
        # seats — freezing would demote them to spectator for the whole connection.
        return (session.seat_for_token(token) or "") if token else ""

    return StreamingResponse(
        _sse(session, viewer_seat, last_seq),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _frame(kind: str, event) -> str:
    """Format one event as an SSE frame (text protocol: id/event/data + blank line).
    kind: str -> the SSE channel: "game" (durable) or "pacing" (ephemeral)
    event -> the event object; its JSON becomes the data: line
    The id line is conditional: only events with a seq get one — pacing must never
    advance the browser's reconnect cursor (Last-Event-ID).
    """
    seq = getattr(event, "seq", None)
    id_line = f"id: {seq}\n" if seq is not None else ""
    return f"{id_line}event: {kind}\ndata: {event.model_dump_json()}\n\n"


async def _sse(session: GameSession, viewer_seat: Callable[[], str],
               last_seq: int) -> AsyncIterator[str]:
    """Subscribe FIRST, then replay the log, then go live — the sent-set bridges the overlap.

    The load-bearing whys, one per line:
    - Subscribe before replaying: every event lands in the snapshot or the queue (or both);
      the failure mode left possible is duplication, which `sent` erases — a gap would be
      silent and unfixable.
    - list(session.log): we suspend at every yield; the game may append mid-iteration, and
      iterating a mutating list skips or repeats entries. The photo freezes our view.
    - The 15s heartbeat is for the pipes, not the players: proxies kill silent connections
      (30-60s idle defaults), and a failed keep-alive write is how ghost viewers get
      detected and unsubscribed. Players may think for minutes; nothing times out for them.
    - Pacing frames skip the seq/dedupe/entitlement gates: no identity, not in the log,
      public by construction.
    - Entitlement is asked per delivery (never cached), so a post-game connection replays
      everything and a live connection flushes the withheld backlog the moment game_over
      passes through — `sent` doubles as the ledger the R7 flush inverts.
    - The cursor is tier-aware (ruled 2026-08-18): last_seq means "I have every event
      <= N that I was entitled to WHEN IT WAS SENT" — withheld events were never sent,
      so cursor_skips() refuses to skip them in both the replay and the R7 flush.
      Otherwise a reconnecting viewer's reveal silently misses the backlog below their
      cursor (both variants: reconnect after game over, and reconnect mid-game with the
      unlock arriving live).
    - viewer_seat is a CALLABLE, asked per check like the roles map: both identity
      (token -> seat) and roles bind at INITIALIZE_GAME, which may land after connect.
    """
    q = session.subscribe()
    sent: set[int] = set()
    logger.debug("game %s: viewer connected (seat=%r, cursor=%d)",
                 session.game_id, viewer_seat(), last_seq)

    def may_see(event) -> bool:
        return entitled(event, viewer_seat(), session.translator.roles, session.game_over)

    def cursor_skips(event) -> bool:
        # "Client already has this" — true only if it was entitled LIVE (game_over=False):
        # the cursor cannot cover events that were never sent, whatever their seq.
        return (event.seq <= last_seq
                and entitled(event, viewer_seat(), session.translator.roles, False))

    try:
        # reconnection, fast-forward all completed stream events
        for event in list(session.log):
            if not cursor_skips(event) and may_see(event):
                sent.add(event.seq)
                yield _frame("game", event)

        while True:
            try:
                kind, event = await asyncio.wait_for(q.get(), timeout=_HEARTBEAT_SECONDS)
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
                # The R7 unlock: everything withheld during play ships now, in seq order.
                for held in list(session.log):
                    if held.seq not in sent and not cursor_skips(held):
                        sent.add(held.seq)
                        yield _frame("game", held)
    finally:
        session.unsubscribe(q)
        logger.debug("game %s: viewer disconnected (seat=%r)",
                     session.game_id, viewer_seat())


app = create_app()

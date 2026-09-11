"""Waiting-room creation, discovery, seating, and game-start endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response

from server.config import server_settings
from server.database_models.game import GameRow
from server.dependencies import GamesRegistry, Room, ended_detail
from server.game.lobby import MAX_HUMAN_SEATS, GameLobby
from server.schemas.requests import (
    GameCreated,
    JoinGame,
    NewRoom,
    RejoinGame,
    RoomCreated,
    RoomSummary,
    SeatJoined,
)

from ._shared import check_model_access, set_seat_cookie

router = APIRouter(tags=["rooms"])


@router.post(
    "/rooms",
    response_model=RoomCreated,
    summary="Create a multiplayer waiting room (humans join via /join)",
)
async def create_room(body: NewRoom, games: GamesRegistry) -> RoomCreated:
    """Create a lobby whose identifier remains stable when the game starts.

    Humans enter only through ``/join`` and roles remain random.
    """
    check_model_access(body.api_key, body.model)
    room = await games.open_room(api_key=body.api_key, model=body.model, name=body.name)
    return RoomCreated(game_id=room.game_id, host_key=room.host_key)


def _room_summary(room: GameLobby) -> RoomSummary:
    return RoomSummary(
        game_id=room.game_id,
        name=room.name,
        players=list(room.players),
        max_seats=MAX_HUMAN_SEATS,
        locked=room.locked,
        created_at=room.created_at.isoformat(),
    )


@router.get(
    "/rooms",
    response_model=list[RoomSummary],
    summary="Browse waiting rooms (public)",
)
async def list_rooms(games: GamesRegistry) -> list[RoomSummary]:
    """Return non-stale waiting rooms newest first without expiring direct URLs."""
    cutoff = server_settings.ROOM_LIST_TTL_SECONDS
    now = datetime.now(timezone.utc)
    rooms = [
        room for room in games.lobbies()
        if (now - room.created_at).total_seconds() < cutoff
    ]
    return [
        _room_summary(room)
        for room in sorted(rooms, key=lambda item: item.created_at, reverse=True)
    ]


@router.post(
    "/games/{game_id}/lock",
    response_model=RoomSummary,
    summary="Lock or unlock a waiting room (host only)",
)
async def lock_room(
    room: Room,
    games: GamesRegistry,
    host_key: str = "",
    locked: bool = True,
) -> RoomSummary:
    _open(room)
    try:
        room = await games.lock(room.game_id, host_key, locked)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _room_summary(room)


def _open(room) -> None:
    """Every door here acts on a game that has not ended; an archived row is 410."""
    if isinstance(room, GameRow):
        raise HTTPException(status_code=410, detail=ended_detail(room))


@router.post(
    "/games/{game_id}/join",
    response_model=SeatJoined,
    summary="Claim a human seat in a waiting room",
)
async def join_game(
    room: Room,
    body: JoinGame,
    response: Response,
    games: GamesRegistry,
) -> SeatJoined:
    _open(room)
    try:
        token = await games.join(room.game_id, body.name)
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    set_seat_cookie(response, room.game_id, token)
    return SeatJoined(token=token)


@router.post(
    "/games/{game_id}/rejoin",
    response_model=SeatJoined,
    summary="Restore a lost seat cookie from the token's body copy",
)
async def rejoin_game(
    room: Room,
    body: RejoinGame,
    response: Response,
) -> SeatJoined:
    _open(room)
    if not room.owns(body.token):
        raise HTTPException(status_code=403, detail="unknown seat token")
    set_seat_cookie(response, room.game_id, body.token)
    return SeatJoined(token=body.token)


@router.post(
    "/games/{game_id}/start",
    response_model=GameCreated,
    summary="Start the waiting room's game (host only)",
)
async def start_game(
    room: Room,
    games: GamesRegistry,
    host_key: str = "",
) -> GameCreated:
    """Replace the lobby with a running session under the same ID (registry.start)."""
    _open(room)
    try:
        session = await games.start(room.game_id, host_key)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return GameCreated(game_id=session.game_id)

"""Waiting-room creation, discovery, seating, and game-start endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response

from server.config import server_settings
from server.database_models.game import GameRow
from server.dependencies import GamesRegistry, House, Room, SeatToken, ended_detail
from server.game.lobby import MAX_HUMAN_SEATS, GameLobby
from server.schemas.requests import (
    ChooseCharacter,
    GameCreated,
    GameStatus,
    JoinGame,
    NewRoom,
    RejoinGame,
    RoomCreated,
    RoomSummary,
    SeatJoined,
)

from ._shared import authorize_model, clear_seat_cookie, live_status, set_seat_cookie

router = APIRouter(tags=["rooms"])


@router.post(
    "/rooms",
    response_model=RoomCreated,
    summary="Create a multiplayer waiting room (humans join via /join)",
)
async def create_room(body: NewRoom, games: GamesRegistry, house: House) -> RoomCreated:
    """Create a lobby whose identifier remains stable when the game starts.

    Humans enter only through ``/join`` and roles remain random. The model is resolved
    and the house consulted here so the host learns early; the cap is checked again at
    start, which is when the game actually costs anything.
    """
    model = await authorize_model(house, body.api_key, body.model)
    room = await games.open_room(api_key=body.api_key, model=model, name=body.name,
                                 memory=body.memory)
    return RoomCreated(game_id=room.game_id, host_key=room.host_key)


def _room_summary(room: GameLobby) -> RoomSummary:
    return RoomSummary(
        game_id=room.game_id,
        name=room.name,
        players=list(room.players),
        host=room.host,
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
        room for room in games.lobbies
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
    held: SeatToken,
    host_key: str = "",
) -> SeatJoined:
    """A browser already aboard (its seat cookie rides this request) gets its own seat
    back; everyone else gets a new one. The creator boards with the room's host key, which
    marks their seat as the host's."""
    _open(room)
    try:
        token = await games.join(room.game_id, body.name, held, host_key)
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    set_seat_cookie(response, room.game_id, token)
    return SeatJoined(token=token)


@router.post(
    "/games/{game_id}/leave",
    status_code=204,
    summary="Give up your seat in a waiting room",
)
async def leave_room(room: Room, response: Response, games: GamesRegistry,
                     token: SeatToken) -> None:
    """The seat cookie says whose seat; the place opens again and the cookie goes. 409
    for the host (who closes the room instead) or once the game has started; 403 without
    a seat here."""
    _open(room)
    try:
        await games.leave(room.game_id, token)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except LookupError as exc:
        status = 403 if isinstance(room, GameLobby) else 409
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    clear_seat_cookie(response, room.game_id)


@router.post(
    "/games/{game_id}/character",
    response_model=GameStatus,
    summary="Pick the puppet your seat stands as (waiting room)",
)
async def choose_character(room: Room, body: ChooseCharacter, games: GamesRegistry,
                           token: SeatToken) -> GameStatus:
    """The seat cookie says whose seat. First come first served: 409 when another seat
    already stands as that puppet, or once the game has started; 422 for a puppet the
    catalogue does not offer; 403 without a seat here. Null gives the pick up. Answers
    the room's snapshot, with everyone's picks."""
    _open(room)
    if isinstance(room, GameLobby) and not room.owns(token):
        raise HTTPException(status_code=403, detail="you hold no seat in this room")
    try:
        room = await games.choose_character(room.game_id, token, body.character)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return live_status(room, token)


@router.post(
    "/games/{game_id}/close",
    status_code=204,
    summary="Close a waiting room for everyone (host only)",
)
async def close_room(room: Room, games: GamesRegistry, host_key: str = "") -> None:
    """The room goes; its URL answers 410 with the reason from then on."""
    _open(room)
    try:
        await games.close(room.game_id, host_key)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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
    house: House,
    host_key: str = "",
) -> GameCreated:
    """Replace the lobby with a running session under the same ID (registry.start)."""
    _open(room)
    if isinstance(room, GameLobby):  # a started game falls through to the registry's 409
        await authorize_model(house, room.api_key, room.model)  # the moment the house pays
    try:
        session = await games.start(room.game_id, host_key)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return GameCreated(game_id=session.game_id)

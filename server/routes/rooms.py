"""Waiting-room creation, discovery, seating, and game-start endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response

from server.config import server_settings
from server.dependencies import (
    GameRepositoryDep,
    GamesRegistry,
    GraphRuntimeDep,
    Room,
)
from server.lobby import MAX_HUMAN_SEATS, GameLobby
from server.runtime import GameSession
from server.schemas.requests import (
    GameCreated,
    JoinGame,
    NewRoom,
    RejoinGame,
    RoomCreated,
    RoomSummary,
    SeatJoined,
)

from ._shared import check_byok, set_seat_cookie

router = APIRouter(tags=["rooms"])


@router.post(
    "/rooms",
    response_model=RoomCreated,
    summary="Create a multiplayer waiting room (humans join via /join)",
)
async def create_room(
    body: NewRoom,
    games: GamesRegistry,
    repository: GameRepositoryDep,
) -> RoomCreated:
    """Create a lobby whose identifier remains stable when the game starts.

    Humans enter only through ``/join`` and roles remain random. The room and its
    eventual running game share one registry/database identity for their full life.
    """
    check_byok(body.api_key, body.model)
    room = GameLobby(api_key=body.api_key, model=body.model, name=body.name)
    games[room.game_id] = room
    await repository.upsert_game(
        room.game_id,
        status="waiting",
        host_key=room.host_key,
        model=body.model,
        byok=bool(body.api_key),
        seats=[],
        room_name=room.name,
        created_at=room.created_at,
    )
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
        game
        for game in games.values()
        if isinstance(game, GameLobby)
        and (now - game.created_at).total_seconds() < cutoff
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
    repository: GameRepositoryDep,
    host_key: str = "",
    locked: bool = True,
) -> RoomSummary:
    if not isinstance(room, GameLobby):
        raise HTTPException(status_code=409, detail="game already started")
    if host_key != room.host_key:
        raise HTTPException(status_code=403, detail="only the host may lock the room")
    room.locked = locked
    await repository.upsert_game(room.game_id, locked=locked)
    return _room_summary(room)


@router.post(
    "/games/{game_id}/join",
    response_model=SeatJoined,
    summary="Claim a human seat in a waiting room",
)
async def join_game(
    room: Room,
    body: JoinGame,
    response: Response,
    repository: GameRepositoryDep,
) -> SeatJoined:
    if not isinstance(room, GameLobby):
        raise HTTPException(status_code=409, detail="game already started")
    try:
        position, token = room.join(body.name)
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await repository.upsert_game(
        room.game_id, seats=[seat._asdict() for seat in room.seats]
    )
    set_seat_cookie(response, room.game_id, token)
    return SeatJoined(position=position, token=token)


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
    position = room.position_of(body.token)
    if position is None:
        raise HTTPException(status_code=403, detail="unknown seat token")
    set_seat_cookie(response, room.game_id, body.token)
    return SeatJoined(position=position, token=body.token)


@router.post(
    "/games/{game_id}/start",
    response_model=GameCreated,
    summary="Start the waiting room's game (host only)",
)
async def start_game(
    room: Room,
    games: GamesRegistry,
    repository: GameRepositoryDep,
    graph_runtime: GraphRuntimeDep,
    host_key: str = "",
) -> GameCreated:
    """Atomically replace the lobby with a running session under the same ID.

    There is no await between validating the lobby and replacing the registry entry,
    so another ``/start`` or ``/join`` cannot interleave with the in-memory swap.
    """
    if not isinstance(room, GameLobby):
        raise HTTPException(status_code=409, detail="game already started")
    if host_key != room.host_key:
        raise HTTPException(status_code=403, detail="only the host may start the game")
    session = GameSession(
        room.run_config(),
        api_key=room.api_key,
        model=room.model,
        seat_tokens=room.tokens,
        graph=graph_runtime.graph,
        repository=repository,
    )
    games[session.game_id] = session
    await repository.upsert_game(
        session.game_id,
        status="running",
        seats=[seat._asdict() for seat in room.seats],
    )
    session.start()
    return GameCreated(game_id=session.game_id)

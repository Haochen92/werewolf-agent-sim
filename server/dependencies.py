"""Dependency providers + ``Annotated`` aliases for route signatures.

Providers pull shared objects off ``request.app.state`` (populated by the lifespan);
the aliases keep endpoint signatures declarative: ``async def game_status(session:
Game)``. The 404 for an unknown game lives here, once, instead of in every route.

Two doors over one registry key: ``Room`` resolves to whatever the id names (a
waiting GameLobby or a running GameSession — status, join, start), while ``Game``
demands a started session and 409s on a lobby (turns, events).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request

from server.game_repository import GameRepository
from server.graph_runtime import GraphRuntime
from server.lobby import GameLobby
from server.replay_service import ReplayService
from server.resources import AppResources
from server.runtime import GameSession

Entry = GameSession | GameLobby


def get_resources(request: Request) -> AppResources:
    """The one process-lifetime container created by the FastAPI lifespan."""
    return request.app.state.resources


Resources = Annotated[AppResources, Depends(get_resources)]


def get_games(resources: Resources) -> dict[str, Entry]:
    """The app's registry of every waiting room and running game, keyed by game_id.

    The dict belongs to ``AppResources``. It starts empty, is rehydrated from the
    game repository, and is discarded after running tasks stop at shutdown. Inject
    this (rather than the id-resolving providers below) when a route must ADD or
    SWAP an entry: POST /games, POST /rooms, and /start's lobby/session swap."""
    return resources.games


GamesRegistry = Annotated[dict[str, Entry], Depends(get_games)]


def get_game_repository(resources: Resources) -> GameRepository:
    return resources.game_repository


GameRepositoryDep = Annotated[GameRepository, Depends(get_game_repository)]


def get_graph_runtime(resources: Resources) -> GraphRuntime:
    return resources.graph_runtime


GraphRuntimeDep = Annotated[GraphRuntime, Depends(get_graph_runtime)]


def get_replay_service(resources: Resources) -> ReplayService:
    """Return the app-owned replay reader without creating a storage client."""
    return resources.replays


ReplayServiceDep = Annotated[ReplayService, Depends(get_replay_service)]


def get_room(game_id: str, games: GamesRegistry) -> Entry:
    """Resolve the ``{game_id}`` path parameter to its registry entry, or 404."""
    entry = games.get(game_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="unknown game")
    return entry


def get_game(game_id: str, games: GamesRegistry) -> GameSession:
    """Like get_room, but the caller needs a RUNNING game: a lobby is 409."""
    entry = get_room(game_id, games)
    if isinstance(entry, GameLobby):
        raise HTTPException(status_code=409,
                            detail="game not started yet (waiting room)")
    return entry


def seat_cookie_name(game_id: str) -> str:
    """Per-game cookie name — one browser can hold seats in several games at once."""
    return f"seat_{game_id}"


def get_seat_token(game_id: str, request: Request) -> str:
    """The viewer's seat-token cookie for THIS game; "" = no cookie (a spectator).

    The token is minted at /join (or the solo POST /games door), delivered as an
    HttpOnly cookie plus a one-time body copy, and rides back automatically on every
    same-game request — including SSE, which cannot set headers but does send cookies.
    Extraction only: whether the token is KNOWN is the session's call
    (seat_for_token / position_of), made in the routes."""
    return request.cookies.get(seat_cookie_name(game_id), "")


Room = Annotated[Entry, Depends(get_room)]
Game = Annotated[GameSession, Depends(get_game)]
SeatToken = Annotated[str, Depends(get_seat_token)]

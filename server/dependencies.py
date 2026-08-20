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

from server.lobby import GameLobby
from server.runtime import GameSession

Entry = GameSession | GameLobby


def get_games(request: Request) -> dict[str, Entry]:
    """The app's registry of every waiting room and running game, keyed by game_id.

    One plain dict on app.state — created empty by the lifespan at startup, torn
    down by it at shutdown (running game tasks get cancelled). In-memory only: a
    server restart forgets all games. Inject this (rather than the id-resolving
    providers below) when a route must ADD or SWAP an entry: POST /games,
    POST /rooms, and /start's lobby-for-session swap."""
    return request.app.state.games


def get_room(game_id: str, request: Request) -> Entry:
    """Resolve the ``{game_id}`` path parameter to its registry entry, or 404."""
    entry = request.app.state.games.get(game_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="unknown game")
    return entry


def get_game(game_id: str, request: Request) -> GameSession:
    """Like get_room, but the caller needs a RUNNING game: a lobby is 409."""
    entry = get_room(game_id, request)
    if isinstance(entry, GameLobby):
        raise HTTPException(status_code=409,
                            detail="game not started yet (waiting room)")
    return entry


GamesRegistry = Annotated[dict[str, Entry], Depends(get_games)]
Room = Annotated[Entry, Depends(get_room)]
Game = Annotated[GameSession, Depends(get_game)]

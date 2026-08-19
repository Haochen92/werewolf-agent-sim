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
    """The in-process registry of live game machines (see design notes 5b)."""
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

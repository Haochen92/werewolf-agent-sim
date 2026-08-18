"""Dependency providers + ``Annotated`` aliases for route signatures.

Providers pull shared objects off ``request.app.state`` (populated by the lifespan);
the aliases keep endpoint signatures declarative: ``async def game_status(session:
Game)``. The 404 for an unknown game lives here, once, instead of in every route.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request

from server.runtime import GameSession


def get_games(request: Request) -> dict[str, GameSession]:
    """The in-process registry of live game machines (see design notes 5b)."""
    return request.app.state.games


def get_game(game_id: str, request: Request) -> GameSession:
    """Resolve the ``{game_id}`` path parameter to its running session, or 404."""
    session = request.app.state.games.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="unknown game")
    return session


GamesRegistry = Annotated[dict[str, GameSession], Depends(get_games)]
Game = Annotated[GameSession, Depends(get_game)]

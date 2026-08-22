"""FastAPI application composition and process-lifetime resource ownership.

The endpoint implementations live in ``server.routes``. This module owns only the
lifespan, middleware, and router registration, so the server's startup/shutdown
sequence can be understood independently of its HTTP handlers.

Run with ``uvicorn server.app:app``.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.config import server_settings
from server.recovery import recover_registry
from server.resources import app_resources
from server.routes.games import router as games_router
from server.routes.replays import router as replays_router
from server.routes.rooms import router as rooms_router
from server.routes.system import router as system_router
from server.runtime import GameSession

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Compose resources, recover games, then stop tasks before closing storage."""
    async with app_resources() as resources:
        app.state.resources = resources
        await recover_registry(
            resources.games,
            resources.game_repository,
            resources.graph_runtime.graph,
        )
        try:
            yield
        finally:
            sessions = [
                entry
                for entry in resources.games.values()
                if isinstance(entry, GameSession)
            ]
            if sessions:
                logger.info("shutting down %d game session(s)", len(sessions))
                await asyncio.gather(
                    *(session.shutdown() for session in sessions)
                )


def create_app() -> FastAPI:
    """Create the API application and register each domain router."""
    app = FastAPI(title="werewolf-agent-sim server", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=server_settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(system_router)
    app.include_router(games_router)
    app.include_router(rooms_router)
    app.include_router(replays_router)
    return app


app = create_app()

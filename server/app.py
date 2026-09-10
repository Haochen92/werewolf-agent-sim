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
from server.housekeeping.recovery import recover_registry
from server.resources import app_resources
from server.routes.games import router as games_router
from server.routes.replays import router as replays_router
from server.routes.rooms import router as rooms_router
from server.routes.system import router as system_router
from server.housekeeping.sweeper import run_sweeper

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Compose resources, recover games, run the retention sweeper, then stop tasks
    before closing storage."""
    async with app_resources() as resources:
        app.state.resources = resources
        await recover_registry(resources.games, resources.game_repository)
        sweeper = asyncio.create_task(run_sweeper(resources.games), name="park-sweeper")
        try:
            yield
        finally:
            sweeper.cancel()
            await resources.games.shutdown()


def _configure_logging() -> None:
    """Give the app's loggers a handler and level. Uvicorn only configures its own;
    an unconfigured root logger drops everything below WARNING on the floor."""
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=server_settings.LOG_LEVEL.upper(),
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    else:
        root.setLevel(server_settings.LOG_LEVEL.upper())


def create_app() -> FastAPI:
    """Create the API application and register each domain router."""
    _configure_logging()
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

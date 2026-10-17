"""FastAPI application composition and process-lifetime resource ownership.

The endpoint implementations live in ``server.routes``. This module owns only the
lifespan, middleware, and router registration, so the server's startup/shutdown
sequence can be understood independently of its HTTP handlers.

Run with ``uvicorn server.app:app``.
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.config import server_settings
from server.error_reporting import init_error_reporting
from server.housekeeping.catalog_refresh import catalog_dsn, refresh_catalog, run_catalog_refresh
from server.housekeeping.recovery import recover_registry
from server.resources import app_resources
from server.routes.admin import router as admin_router
from server.routes.characters import router as characters_router
from server.routes.games import router as games_router
from server.routes.replays import TOTAL_COUNT_HEADER, router as replays_router
from server.routes.rooms import router as rooms_router
from server.routes.system import router as system_router
from server.housekeeping.sweeper import run_sweeper

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model catalogue, compose resources, recover games, run the retention sweeper
    and the catalogue's refresh, then stop tasks before closing storage."""
    # The graph's nodes are sync and run on the loop's default executor, which has 8 threads on
    # this 4-CPU host: one night step is ~10 model-bound nodes per game, and the checkpointer's
    # own thread work queued behind them, so a human wolf's prompt surfaced seconds late
    # (2026-10-17). The threads mostly wait on the network, so many are cheap.
    asyncio.get_running_loop().set_default_executor(
        ThreadPoolExecutor(max_workers=64, thread_name_prefix="graph"))
    dsn = catalog_dsn(server_settings.WW_POSTGRES_DSN)
    if dsn:
        await refresh_catalog(dsn)  # before recovery: a recovered game needs its rescue model
    async with app_resources() as resources:
        app.state.resources = resources
        await recover_registry(resources.games, resources.game_repository)
        sweeper = asyncio.create_task(run_sweeper(resources.games), name="park-sweeper")
        refresher = (asyncio.create_task(run_catalog_refresh(dsn), name="catalog-refresh")
                     if dsn else None)
        try:
            yield
        finally:
            sweeper.cancel()
            if refresher is not None:
                refresher.cancel()
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
    init_error_reporting()  # before the app exists, so the FastAPI integration hooks it
    app = FastAPI(title="werewolf-agent-sim server", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=server_settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[TOTAL_COUNT_HEADER],  # the replay list's total, read by the page
    )
    app.include_router(system_router)
    app.include_router(games_router)
    app.include_router(rooms_router)
    app.include_router(replays_router)
    app.include_router(characters_router)
    app.include_router(admin_router)
    return app


app = create_app()

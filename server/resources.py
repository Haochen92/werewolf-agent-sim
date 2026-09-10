"""FastAPI composition root for process-lifetime server resources.

Ownership is visible in one place::

    FastAPI lifespan
    └── AppResources
        ├── Database
        ├── GameRepository(Database)
        ├── GraphRuntime(checkpoint DSN)
        ├── ReplayService(Database)
        └── GameRegistry(GameRepository, GraphRuntime)

The lifespan creates this tree once and context-manager nesting closes it in reverse.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from server.config import ServerSettings, server_settings
from server.db import Database, database_resource
from server.game.registry import GameRegistry
from server.graph_runtime import GraphRuntime, graph_runtime_resource
from server.storage.game_repository import GameRepository
from server.storage.replay_service import ReplayService


@dataclass(slots=True)
class AppResources:
    """The resources owned by one FastAPI application instance."""

    database: Database
    game_repository: GameRepository
    graph_runtime: GraphRuntime
    replays: ReplayService
    games: GameRegistry


@asynccontextmanager
async def app_resources(settings: ServerSettings = server_settings
                        ) -> AsyncIterator[AppResources]:
    """Create resources in dependency order and close them in reverse order."""
    database_url = settings.replay_database_url if settings.WW_POSTGRES_DSN else ""
    async with database_resource(database_url) as database:
        async with graph_runtime_resource(settings.WW_POSTGRES_DSN) as graph_runtime:
            repository = GameRepository(database)
            yield AppResources(
                database=database,
                game_repository=repository,
                graph_runtime=graph_runtime,
                replays=ReplayService(database),
                games=GameRegistry(repository, graph_runtime),
            )

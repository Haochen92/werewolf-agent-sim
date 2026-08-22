"""App-owned LangGraph runtime with durable PostgreSQL checkpoints.

One ``GraphRuntime`` is shared by every game in a FastAPI process. The compiled
graph is reusable; each game's ``thread_id`` (its game ID) isolates checkpoint
state inside the shared saver.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

logger = logging.getLogger(__name__)


class GraphRuntime:
    """Own the checkpoint pool, saver, and compiled graph lifecycle."""

    def __init__(self, checkpoint_dsn: str) -> None:
        self._checkpoint_dsn = checkpoint_dsn
        self._pool = None
        self._saver = None
        self._graph = None

    @property
    def graph(self):
        """Durably compiled graph, or ``None`` when Postgres is unconfigured."""
        return self._graph

    async def startup(self) -> None:
        """Open the checkpointer pool and compile the graph exactly once."""
        if not self._checkpoint_dsn or self._graph is not None:
            return
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg.rows import dict_row
        from psycopg_pool import AsyncConnectionPool

        from Agents.graphs.parent import parent_graph
        from Agents.memory import store
        from Agents.memory.checkpointer import durable_serde # translator for checkpoint values to and from stored bytes.

        self._pool = AsyncConnectionPool(
            self._checkpoint_dsn,
            open=False,
            min_size=1,
            max_size=4,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
                "row_factory": dict_row,
            },
        )
        await self._pool.open()
        self._saver = AsyncPostgresSaver(self._pool, serde=durable_serde())
        await self._saver.setup()
        self._graph = parent_graph.compile(store=store, checkpointer=self._saver)
        logger.info("graph runtime up: Postgres checkpointer + compiled graph")

    async def close(self) -> None:
        """Close the checkpoint pool and release the compiled graph."""
        if self._pool is not None:
            await self._pool.close()
        self._pool = None
        self._saver = None
        self._graph = None


@asynccontextmanager
async def graph_runtime_resource(checkpoint_dsn: str) -> AsyncIterator[GraphRuntime]:
    """Lifespan adapter: start and close one graph runtime."""
    runtime = GraphRuntime(checkpoint_dsn)
    try:
        await runtime.startup()
        yield runtime
    finally:
        await runtime.close()

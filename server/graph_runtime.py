"""App-owned LangGraph runtime with durable PostgreSQL checkpoints and the lesson store.

One ``GraphRuntime`` is shared by every game in a FastAPI process. The compiled
graph is reusable; each game's ``thread_id`` (its game ID) isolates checkpoint
state inside the shared saver. The graph is compiled over the database's lesson store
(``Agents/memory/persistence/postgres.py``), so a memory-on game searches the lessons the
last tick published, and nothing is seeded into the process.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

logger = logging.getLogger(__name__)


class GraphRuntime:
    """Own the checkpoint pool, saver, lesson store, and compiled graph lifecycle."""

    def __init__(self, checkpoint_dsn: str) -> None:
        self._checkpoint_dsn = checkpoint_dsn
        self._pool = None
        self._saver = None
        self._memory_store = None
        self._memory_pool = None
        self._graph = None

    @property
    def graph(self):
        """Durably compiled graph, or ``None`` when Postgres is unconfigured."""
        return self._graph

    @property
    def memory_store(self):
        """The lesson store the graph searches, or ``None`` when Postgres is unconfigured."""
        return self._memory_store

    def memory_unavailable_reason(self) -> str | None:
        """Why a memory-on game must not start right now, or None when it may: no database,
        or a store nobody has published to, or one embedded by another model. One indexed
        read; call it off the event loop."""
        if self._memory_store is None:
            return "the server has no database to read lessons from"
        from Agents.memory.persistence.postgres import unready_reason

        return unready_reason(self._memory_store)

    async def startup(self) -> None:
        """Open the checkpointer pool and the lesson store, and compile the graph exactly once."""
        if not self._checkpoint_dsn or self._graph is not None:
            return
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg.rows import dict_row
        from psycopg_pool import AsyncConnectionPool

        from Agents.graphs.parent import parent_graph
        from Agents.memory.checkpointer import durable_serde # translator for checkpoint values to and from stored bytes.
        from Agents.memory.persistence.postgres import open_store

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
        self._memory_store, self._memory_pool = open_store(self._checkpoint_dsn)
        self._graph = parent_graph.compile(store=self._memory_store, checkpointer=self._saver)
        reason = self.memory_unavailable_reason()
        logger.info("graph runtime up: Postgres checkpointer + lesson store (%s) + compiled graph",
                    "ready" if reason is None else f"memory unavailable: {reason}")

    async def close(self) -> None:
        """Close the pools and release the compiled graph."""
        if self._pool is not None:
            await self._pool.close()
        if self._memory_pool is not None:
            self._memory_pool.close()
        self._pool = None
        self._saver = None
        self._memory_store = None
        self._memory_pool = None
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

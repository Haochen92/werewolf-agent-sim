"""App-owned SQLAlchemy resources for the server's Postgres tables.

``Database`` owns exactly one async engine and session factory. It is created by
the FastAPI lifespan, injected into the services that need it, and closed from the
same composition root. No connection is opened at import time, and an empty URL
keeps the server's database-backed features disabled.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """One explicitly-owned async engine and its per-operation sessions."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def configured(self) -> bool:
        return bool(self._database_url)

    @property
    def engine(self) -> AsyncEngine | None:
        return self._engine

    async def startup(self) -> None:
        """Create the pool once. SQLAlchemy opens physical connections on demand."""
        if not self.configured or self._engine is not None:
            return
        self._engine = create_async_engine(self._database_url, pool_pre_ping=True)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False,
        )

    def session(self) -> AsyncSession:
        """Return one unit-of-work session, or fail loudly when unconfigured."""
        if self._session_factory is None:
            raise RuntimeError("WW_POSTGRES_DSN is not set")
        return self._session_factory()

    async def close(self) -> None:
        """Dispose the pool. Safe after partial startup and safe to call twice."""
        if self._engine is not None:
            await self._engine.dispose()
        self._engine = None
        self._session_factory = None


@asynccontextmanager
async def database_resource(database_url: str) -> AsyncIterator[Database]:
    """Lifespan adapter: start and close one ``Database`` instance."""
    database = Database(database_url)
    try:
        await database.startup()
        yield database
    finally:
        await database.close()

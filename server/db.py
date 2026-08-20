"""Async engine/session factory for server-owned Postgres tables.

The replay archive today; live-session durability later — this module is the Postgres
beachhead those slices share. Pattern adopted from dota2pred's DatabaseManager, minus the
class ceremony: a module-level lazily-created singleton engine, DSN from
``server_settings.WW_POSTGRES_DSN`` (shared with the memory tick's database — server
tables are alembic-managed, the tick's raw-psycopg tables are not; ``alembic/env.py``
scopes itself to SQLModel metadata so the two never collide).

No DSN = no engine: the server runs fine without Postgres (dev), archiving no-ops and
the /replays endpoints answer 503. Nothing in this module raises at import time.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from server.config import server_settings

_engine: AsyncEngine | None = None
_sessions: async_sessionmaker[AsyncSession] | None = None


def configured() -> bool:
    return bool(server_settings.WW_POSTGRES_DSN)


def engine() -> AsyncEngine | None:
    """The process-wide engine, created on first use; None when no DSN is set."""
    global _engine, _sessions
    if _engine is None and configured():
        _engine = create_async_engine(server_settings.replay_database_url,
                                      pool_pre_ping=True)
        _sessions = async_sessionmaker(_engine, class_=AsyncSession,
                                       expire_on_commit=False)
    return _engine


def session() -> AsyncSession:
    """One unit-of-work session. Raises when unconfigured — callers gate on
    configured()/engine() first (routes answer 503, the archive hook no-ops)."""
    if engine() is None:
        raise RuntimeError("WW_POSTGRES_DSN is not set")
    assert _sessions is not None
    return _sessions()


async def dispose() -> None:
    """Close the pool (lifespan shutdown). Safe when never configured."""
    global _engine, _sessions
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessions = None

"""The durable live-game plane: Postgres checkpointer + the sessions/events tables.

Slice 6 (ruled 2026-08-20). Three kinds of persistence, one module:

- **The engine checkpoint** — an AsyncPostgresSaver (same serde allowlist as the CLI's
  MemorySaver) behind a connection pool, and the parent graph compiled against it.
  Contracts probe-verified across real process boundaries: pause survives the process
  dying; a fresh process recovers the parked interrupt payload via aget_state; resume
  re-runs the interrupted phase (abort-and-re-execute, exactly the in-process behavior).
- **The events table** — the durable copy of every session's wire log, written
  synchronously per stream part (a crash loses at most the in-flight part's events).
  This is what SSE replay and the translator rebuild from after a restart.
- **The sessions table** — the registry's durable facts: phase, seats (tokens included:
  they are the seat identity and must survive), host_key, model. DELIBERATELY absent:
  the BYOK api_key (ruled: keys live in memory only) — a `byok` flag survives instead,
  so recovery can mark those games dead-with-reason rather than silently unfunded.

Every write helper here is no-raise and no-ops when Postgres is unconfigured: the
durable plane is a bystander to a running game — losing durability must never cost
the game itself (same policy as the replay archive).

Boot-time recovery (rebuilding sessions from these tables) lives in server/recovery.py
— not here, to keep this module import-light for server/runtime.py.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import TIMESTAMP, Column, Text, func
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlmodel import Field, SQLModel, select

from server import db
from server.config import server_settings
from server.schemas import events as ev

logger = logging.getLogger(__name__)

# Created by startup() when Postgres is configured; None otherwise.
_pool = None
_graph = None


# ---- lifecycle (called by the app lifespan) ------------------------------------------------

async def startup() -> None:
    """Open the checkpointer pool, run its setup, compile the durable parent graph."""
    global _pool, _graph
    if not db.configured() or _graph is not None:
        return
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg.rows import dict_row
    from psycopg_pool import AsyncConnectionPool

    from Agents.graphs.parent import parent_graph
    from Agents.memory import store
    from Agents.memory.checkpointer import durable_serde

    # The saver's required connection shape (autocommit, dict rows, no prepared
    # statements) — per langgraph-checkpoint-postgres; a plain pool default breaks it.
    _pool = AsyncConnectionPool(
        server_settings.WW_POSTGRES_DSN, open=False, min_size=1, max_size=4,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )
    await _pool.open()
    saver = AsyncPostgresSaver(_pool, serde=durable_serde())
    await saver.setup()  # its own tables; cohabits ours (alembic ignores them)
    _graph = parent_graph.compile(store=store, checkpointer=saver)
    logger.info("durable plane up: Postgres checkpointer + compiled graph")


async def shutdown() -> None:
    global _pool, _graph
    if _pool is not None:
        await _pool.close()
    _pool = None
    _graph = None


def graph():
    """The durably-checkpointed compiled parent graph; None when unconfigured —
    GameSession then falls back to the in-memory-checkpointed default."""
    return _graph


# ---- tables (schema authority; shipped by alembic revision 0002) ---------------------------

class SessionRow(SQLModel, table=True):
    """One registry entry's durable facts — everything recovery needs that the
    checkpoint and event log cannot supply."""

    __tablename__ = "sessions"

    game_id: str = Field(sa_column=Column(Text, primary_key=True))
    phase: str
    """waiting | running | finished | dead. Recovery only looks at waiting/running."""
    host_key: str = ""
    model: str = ""
    byok: bool = False
    """The key itself is never stored (ruling) — the flag makes recovery mark the
    game dead-with-reason instead of silently continuing on server credentials."""
    seats: list[dict] = Field(default_factory=list, sa_column=Column(JSONB, nullable=False))
    """[{name, token}] in join order — join order IS deal order (the seat identity)."""
    human_players: list[str] = Field(default_factory=list,
                                     sa_column=Column(JSONB, nullable=False))
    room_name: str = ""
    """The waiting room's public title (GET /rooms); "" for solo/instant games."""
    locked: bool = False
    """Host-set join bounce — must survive a restart or the lock silently reopens."""
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False,
                         server_default=func.now()))
    """Room-listing TTL anchor (set by the route from the lobby's own stamp)."""
    error: str | None = None
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False,
                         server_default=func.now()))


class EventRow(SQLModel, table=True):
    """The durable wire log, one row per event (PK game_id+seq = idempotent writes)."""

    __tablename__ = "events"

    game_id: str = Field(sa_column=Column(Text, primary_key=True))
    seq: int = Field(primary_key=True)
    payload: dict = Field(sa_column=Column(JSONB, nullable=False))


# ---- write helpers (no-raise; no-op when unconfigured) --------------------------------------

async def upsert_session(game_id: str, **fields: Any) -> None:
    """INSERT the row or update just the provided fields (partial upsert)."""
    if db.engine() is None:
        return
    try:
        stmt = insert(SessionRow).values({"game_id": game_id, "phase": "waiting", **fields})
        stmt = stmt.on_conflict_do_update(
            index_elements=["game_id"],
            set_={**fields, "updated_at": func.now()},
        )
        async with db.session() as sess:
            await sess.execute(stmt)
            await sess.commit()
    except Exception:
        logger.exception("game %s: session upsert failed (game unaffected)", game_id)


async def record_events(game_id: str, events: Sequence[ev.DurableEvent]) -> None:
    """One INSERT per part's batch; ON CONFLICT DO NOTHING makes replays idempotent."""
    if db.engine() is None or not events:
        return
    try:
        stmt = insert(EventRow).values([
            {"game_id": game_id, "seq": e.seq, "payload": e.model_dump(mode="json")}
            for e in events
        ]).on_conflict_do_nothing(index_elements=["game_id", "seq"])
        async with db.session() as sess:
            await sess.execute(stmt)
            await sess.commit()
    except Exception:
        logger.exception("game %s: event persistence failed (game unaffected)", game_id)


# ---- read helpers (recovery + hydration) ----------------------------------------------------

async def load_open_sessions() -> list[SessionRow]:
    async with db.session() as sess:
        rows = (await sess.execute(
            select(SessionRow).where(SessionRow.phase.in_(("waiting", "running")))
        )).scalars().all()
    return list(rows)


async def load_events(game_id: str) -> list[ev.DurableEvent]:
    async with db.session() as sess:
        rows = (await sess.execute(
            select(EventRow).where(EventRow.game_id == game_id).order_by(EventRow.seq)
        )).scalars().all()
    from pydantic import TypeAdapter
    adapter = TypeAdapter(ev.DurableGameEvent)
    return [adapter.validate_python(r.payload) for r in rows]

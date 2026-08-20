"""The replay archive: finished games become Postgres rows; the frontend replays them.

Ruled 2026-08-20: the archive starts EMPTY and fills with real served games — the batch
backfill (deriving event logs from stored game records instead of stream parts) is a
deferred, separate slice. Only CLEAN finishes are archived: an errored/cancelled game
never emitted game_over, so it has no winner and no ending — not replay content (crash
forensics lives in logs/tracing, not on the public shelf). An archive failure is logged
loudly and never touches the game's own outcome: players finished their game; the
archive is a bystander.

Schema pattern adopted from dota2pred: SQLModel base/table split (ReplayBase is the wire
summary AND the shared column set; Replay adds the payload column), alembic revisions
ship the schema (see alembic/versions/ — no runtime CREATE TABLE). The stored ``events``
is the game's complete durable log, all tiers included: replay is post-game, where the
R7 ruling already makes every event observer-visible, and the X-ray toggle needs the
hidden tiers. The frontend folds it with the same reducer as the live SSE stream.

Endpoints are read-only and public (finished games are public). limit/offset only, by
ruling — server-side filters get added when the row count and the replay-browser UX
make them real. No DSN configured = 503, loud, never an empty-list lie.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Sequence

from fastapi import APIRouter, HTTPException
from sqlalchemy import TIMESTAMP, Column, Text, func
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.orm import defer
from sqlmodel import Field, SQLModel, select

from server import db
from server.schemas import events as ev

logger = logging.getLogger(__name__)

router = APIRouter(tags=["replays"])


# ---- schema (authority: this model; shipped by alembic revisions) ------------------------

class ReplayBase(SQLModel):
    """The metadata half — one row of GET /replays, and the columns both models share."""

    game_id: str
    finished_at: datetime | None = None
    """Stamped by the database (server_default now()) — the one field the INSERT omits."""
    winner: str
    """villagers | wolves | serial_killer — lifted from the game_over event."""
    days: int
    n_events: int
    n_humans: int
    cast_role_counts: dict[str, int]


class Replay(ReplayBase, table=True):
    """The table: metadata columns + the payload. sa_column overrides live here only —
    the base stays a plain wire model (the dota2pred split)."""

    __tablename__ = "replays"

    game_id: str = Field(sa_column=Column(Text, primary_key=True))
    finished_at: datetime | None = Field(default=None, sa_column=Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()))
    cast_role_counts: dict[str, int] = Field(sa_column=Column(JSONB, nullable=False))
    events: list[dict] = Field(default_factory=list,
                               sa_column=Column(JSONB, nullable=False))


class ReplayGame(ReplayBase):
    """GET /replays/{id}: the summary plus the full event log."""

    events: list[dict]


# ---- the archive hook (called by GameSession at a clean finish) ---------------------------

def derive_metadata(log: Sequence[ev.DurableEvent]) -> dict | None:
    """Lift the summary row from the log itself. None = not archivable (no clean
    ending on record) — the caller's cue to skip, not an error."""
    started = next((e for e in log if e.type == "game_started"), None)
    over = next((e for e in log if e.type == "game_over"), None)
    if started is None or over is None:
        return None
    return {
        "winner": over.winner,
        "days": max(e.day for e in log),
        "n_events": len(log),
        "cast_role_counts": dict(started.cast_role_counts),
    }


async def archive_game(game_id: str, log: Sequence[ev.DurableEvent],
                       n_humans: int) -> None:
    """One INSERT, idempotent (ON CONFLICT DO NOTHING). Never raises: the game is
    already over and its players are owed nothing from this code path — a failure
    costs one replay, logged loudly, and nothing else."""
    if db.engine() is None:
        logger.info("game %s: replay archive disabled (no WW_POSTGRES_DSN)", game_id)
        return
    try:
        meta = derive_metadata(log)
        if meta is None:
            logger.warning("game %s: finished without a derivable ending; not archived",
                           game_id)
            return
        stmt = insert(Replay).values(
            game_id=game_id, n_humans=n_humans,
            events=[e.model_dump(mode="json") for e in log], **meta,
        ).on_conflict_do_nothing(index_elements=["game_id"])
        async with db.session() as sess:
            await sess.execute(stmt)
            await sess.commit()
        logger.info("game %s: archived (%d events, winner=%s)",
                    game_id, meta["n_events"], meta["winner"])
    except Exception:
        logger.exception("game %s: replay archiving failed", game_id)


# ---- the read side ------------------------------------------------------------------------

def _require_archive() -> None:
    if db.engine() is None:
        raise HTTPException(status_code=503, detail="replay archive not configured")


@router.get("/replays", response_model=list[ReplayBase],
            summary="Browse finished games (newest first)")
async def list_replays(limit: int = 50, offset: int = 0) -> list[ReplayBase]:
    _require_archive()
    stmt = (select(Replay).options(defer(Replay.events))  # summaries: skip the payload
            .order_by(Replay.finished_at.desc())
            .limit(min(limit, 200)).offset(offset))
    async with db.session() as sess:
        rows = (await sess.execute(stmt)).scalars().all()
    return list(rows)


@router.get("/replays/{game_id}", response_model=ReplayGame,
            summary="One finished game's full event log")
async def get_replay(game_id: str) -> Replay:
    _require_archive()
    async with db.session() as sess:
        row = await sess.get(Replay, game_id)
    if row is None:
        raise HTTPException(status_code=404, detail="unknown replay")
    return row

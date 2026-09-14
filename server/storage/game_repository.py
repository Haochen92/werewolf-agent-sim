"""Persistence operations for the unified game lifecycle and event log.

``GameRepository`` is an app-scoped service over the shared ``Database``. It owns
no connections of its own: every method opens a short-lived SQLAlchemy session for
one unit of work. Write failures remain non-fatal to live gameplay; recovery reads
remain loud so the caller can isolate a row that cannot be revived.
"""

from __future__ import annotations

from datetime import datetime

import logging
from typing import Any, Sequence

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import select, update

from server.database_models.game import (
    COMPLETED,
    DROPPED,
    RECOVERABLE_STATUSES,
    EventRow,
    GameRow,
)
from server.db import Database
from server.schemas import events as ev

logger = logging.getLogger(__name__)


def derive_completion_metadata(log: Sequence[ev.DurableEvent]) -> dict | None:
    """Build replay summary fields from a complete durable event log.

    Args:
        log: The game's authoritative events in sequence order.

    Returns:
        Winner, day count, event count, and cast counts, or ``None`` when the
        log lacks either ``game_started`` or ``game_over``.
    """
    started = next((event for event in log if event.type == "game_started"), None)
    over = next((event for event in log if event.type == "game_over"), None)
    if started is None or over is None:
        return None
    return {
        "winner": over.winner,
        "days": max(event.day for event in log),
        "n_events": len(log),
        "cast_role_counts": dict(started.cast_role_counts),
    }


def event_log_shortfall(expected: int, stored: int, last_seq: int) -> str | None:
    """Say what is wrong with a stored event log, or None when nothing is.

    ``expected`` is the length of the game's own log, ``stored`` the rows on disk and
    ``last_seq`` the highest seq among them. Events are numbered from 1 with no gaps, so
    a complete log has all three equal. A short count means a batch failed to write; a
    matching count with a lower last seq cannot happen; a matching count with a higher
    last seq means a hole that a restart has since hidden, since a revived game rebuilds
    its log from the rows and so counts the hole as if it never existed.
    """
    if stored == expected and last_seq == expected:
        return None
    return (f"event log incomplete: {stored} of {expected} events stored, "
            f"last seq {last_seq}")


class GameRepository:
    """Read and write ``GameRow`` and ``EventRow`` through one shared database."""

    def __init__(self, database: Database) -> None:
        """Bind the repository to the application-owned database resource.

        Args:
            database: The shared engine/session-factory owner used for each unit
                of work.
        """
        self._database = database

    async def upsert_game(self, game_id: str, **fields: Any) -> None:
        """Insert a game or update only the supplied fields on its existing row.

        The first write of a game must carry its ``status``: a row is born ``running``
        at launch (rooms are memory-only and get no row), and there is no default to
        fall back on. Later writes touch only the fields given.

        Args:
            game_id: Stable game identity and primary key.
            **fields: ``GameRow`` columns to insert or update.

        Returns:
            Nothing. An unconfigured database is a no-op; write failures are
            logged and suppressed so persistence cannot stop a live game.
        """
        if not self._database.configured:
            return
        try:
            stmt = insert(GameRow).values({"game_id": game_id, **fields})
            stmt = stmt.on_conflict_do_update(
                index_elements=["game_id"],
                set_={**fields, "updated_at": func.now()},
            )
            async with self._database.session() as session:
                await session.execute(stmt)
                await session.commit()
        except Exception:
            logger.exception("game %s: game-row upsert failed (game unaffected)", game_id)

    async def record_events(
        self,
        game_id: str,
        events: Sequence[ev.DurableEvent],
    ) -> None:
        """Append durable events to one game's ordered event log.

        Args:
            game_id: Parent game for every supplied event.
            events: Typed events to serialize into ``EventRow`` payloads.

        Returns:
            Nothing. Existing ``(game_id, seq)`` rows are left unchanged;
            write failures are logged and suppressed.
        """
        if not self._database.configured or not events:
            return
        try:
            stmt = insert(EventRow).values([
                {
                    "game_id": game_id,
                    "seq": event.seq,
                    "payload": event.model_dump(mode="json"),
                }
                for event in events
            ]).on_conflict_do_nothing(index_elements=["game_id", "seq"])
            async with self._database.session() as session:
                await session.execute(stmt)
                await session.execute(
                    update(GameRow).where(GameRow.game_id == game_id).values(
                        updated_at=func.now(),
                    )
                )
                await session.commit()
        except Exception:
            logger.exception(
                "game %s: event persistence failed (game unaffected)", game_id
            )

    async def complete_game(
        self,
        game_id: str,
        log: Sequence[ev.DurableEvent],
        n_humans: int,
    ) -> None:
        """Finalize a game row so its existing events become replay-visible.

        Args:
            game_id: Game to transition to ``completed``.
            log: Complete authoritative event log used to derive replay metadata.
            n_humans: Number of human-controlled seats in the game.

        Returns:
            Nothing. A log with no clean ending, or one the table holds only part of
            (event writes fail soft during play), marks the game ``dropped`` with the
            reason instead, so it never enters the replay listing; database failures
            are logged and suppressed.
        """
        if not self._database.configured:
            return
        metadata = derive_completion_metadata(log)
        if metadata is None:
            logger.warning("game %s: no clean ending; marking dropped", game_id)
            await self.upsert_game(
                game_id,
                status=DROPPED,
                error="finished without a complete replayable event log",
            )
            return
        try:
            async with self._database.session() as session:
                stored, last_seq = (await session.execute(
                    select(func.count(), func.coalesce(func.max(EventRow.seq), 0))
                    .where(EventRow.game_id == game_id)
                )).one()
            shortfall = event_log_shortfall(len(log), stored, last_seq)
            if shortfall is not None:
                logger.warning("game %s: %s; marking dropped", game_id, shortfall)
                await self.upsert_game(game_id, status=DROPPED, error=shortfall)
                return
            values = {
                "status": COMPLETED,
                "finished_at": func.now(),
                "n_humans": n_humans,
                "error": None,
                **metadata,
            }
            stmt = insert(GameRow).values(game_id=game_id, **values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["game_id"],
                set_={**values, "updated_at": func.now()},
            )
            async with self._database.session() as session:
                await session.execute(stmt)
                await session.commit()
            logger.info(
                "game %s: completed (%d events, winner=%s)",
                game_id,
                metadata["n_events"],
                metadata["winner"],
            )
        except Exception:
            logger.exception("game %s: completion persistence failed", game_id)

    async def load_recoverable_games(self) -> list[GameRow]:
        """Load the games boot recovery must bring back: every row still ``running``.
        Rooms have no row, and a ``waiting`` row from before that ruling is left alone.

        Returns:
            Every ``GameRow`` whose status is in ``RECOVERABLE_STATUSES``.

        Raises:
            Exception: Propagates database failures so recovery can fail loudly.
        """
        async with self._database.session() as session:
            rows = (await session.execute(
                select(GameRow).where(GameRow.status.in_(RECOVERABLE_STATUSES))
            )).scalars().all()
        return list(rows)

    async def count_house_games_since(self, since: datetime) -> int:
        """How many house-funded games (no player key) have started since ``since``.
        The daily cap is measured from the rows themselves; nothing else is kept."""
        if not self._database.configured:
            return 0
        async with self._database.session() as session:
            return (await session.execute(
                select(func.count()).select_from(GameRow)
                .where(GameRow.byok.is_(False), GameRow.created_at >= since)
            )).scalar_one()

    async def load_game(self, game_id: str) -> GameRow | None:
        """Load one game's row, or None when the id is unknown or storage is off. The live
        registry answers first; this is what serves a game after it has ended."""
        if not self._database.configured:
            return None
        async with self._database.session() as session:
            return await session.get(GameRow, game_id)

    async def load_events(self, game_id: str) -> list[ev.DurableEvent]:
        """Load and validate one game's durable events in sequence order.

        Args:
            game_id: Game whose event log should be reconstructed.

        Returns:
            Typed durable events ordered by ascending sequence number.

        Raises:
            Exception: Propagates database and payload-validation failures to
                the recovery caller.
        """
        async with self._database.session() as session:
            rows = (await session.execute(
                select(EventRow)
                .where(EventRow.game_id == game_id)
                .order_by(EventRow.seq)
            )).scalars().all()
        from pydantic import TypeAdapter

        adapter = TypeAdapter(ev.DurableGameEvent)
        return [adapter.validate_python(row.payload) for row in rows]

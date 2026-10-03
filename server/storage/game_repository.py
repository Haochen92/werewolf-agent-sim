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

from server.database_models.cast import GameCastRow
from server.database_models.game import (
    COMPLETED,
    DROPPED,
    RECOVERABLE_STATUSES,
    EventRow,
    GameRow,
    GameStatus,
)
from server.db import Database
from server.game.cast import CastSeat, seat_number
from server.schemas import events as ev

logger = logging.getLogger(__name__)


def derive_completion_metadata(log: Sequence[ev.DurableEvent]) -> dict | None:
    """Build replay summary fields from a complete durable event log.

    Args:
        log: The game's authoritative events in sequence order.

    Returns:
        Winner, day count, the phase the game ended in, event count, and cast
        counts, or ``None`` when the log lacks either ``game_started`` or
        ``game_over``. The ending phase is None for a log with no phase change.
    """
    started = next((event for event in log if event.type == "game_started"), None)
    over = next((event for event in log if event.type == "game_over"), None)
    if started is None or over is None:
        return None
    last_phase = next(
        (event for event in reversed(log) if event.type == "phase_change"), None)
    return {
        "winner": over.winner,
        "days": max(event.day for event in log),
        "ended_phase": last_phase.phase if last_phase is not None else None,
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

    async def create_game(self, game_id: str, *, status: GameStatus, **fields: Any) -> bool:
        """Write a game's first row, including its required status. Rooms have no row;
        the registry calls this when play starts. Existing rows are never overwritten.

        Returns True after a successful write, or when storage is disabled (a successful
        no-op). False means a database failure, logged here without stopping live play.
        """
        if not self._database.configured:
            return True
        try:
            stmt = insert(GameRow).values(game_id=game_id, status=status, **fields)
            async with self._database.session() as session:
                await session.execute(stmt)
                await session.commit()
            return True
        except Exception:
            logger.exception("game %s: game-row creation failed (game unaffected)", game_id)
            return False

    async def update_game(self, game_id: str, **fields: Any) -> bool:
        """Change only the supplied fields on an existing game. A partial update must
        not attempt an INSERT: PostgreSQL checks required columns before a conflict.

        Returns True after commit, or when storage is disabled. A missing row or failed
        write returns False, so callers keep unsaved state for the next attempt.
        """
        if not self._database.configured:
            return True
        try:
            stmt = update(GameRow).where(GameRow.game_id == game_id).values(
                {**fields, "updated_at": func.now()})
            async with self._database.session() as session:
                result = await session.execute(stmt)
                if result.rowcount != 1:
                    logger.warning("game %s: cannot update a missing game row", game_id)
                    return False
                await session.commit()
            return True
        except Exception:
            logger.exception("game %s: game-row update failed (game unaffected)", game_id)
            return False

    async def record_events(
        self,
        game_id: str,
        events: Sequence[ev.DurableEvent],
    ) -> bool:
        """Append durable events to one game's ordered event log.

        Args:
            game_id: Parent game for every supplied event.
            events: Typed events to serialize into ``EventRow`` payloads.

        Returns:
            True after commit, or when storage is disabled or the batch is empty.
            False on a logged write failure: the caller must keep the batch unsaved.
            Existing ``(game_id, seq)`` rows are left unchanged, so retrying is safe.
        """
        if not self._database.configured or not events:
            return True
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
            return True
        except Exception:
            logger.exception(
                "game %s: event persistence failed (game unaffected)", game_id
            )
            return False

    async def record_cast(self, game_id: str, cast: Sequence[CastSeat]) -> bool:
        """Write which puppet stands at each seat, once the engine has dealt the seats.
        One row per seat; rows already there are left alone, so a retry cannot double
        up. True after commit, or when storage is disabled or the cast is empty; False
        on a logged failure, so the session keeps the cast unsaved for the next try."""
        if not self._database.configured or not cast:
            return True
        try:
            stmt = insert(GameCastRow).values([
                {"game_id": game_id, "seat": c.seat, "character_id": c.character,
                 "chosen": c.chosen}
                for c in cast
            ]).on_conflict_do_nothing(index_elements=["game_id", "seat"])
            async with self._database.session() as session:
                await session.execute(stmt)
                await session.commit()
            return True
        except Exception:
            logger.exception("game %s: cast persistence failed (game unaffected)", game_id)
            return False

    async def load_cast(self, game_id: str) -> list[CastSeat]:
        """The puppets a game stored, in seat order; empty for a game recorded before
        casts were stored, or when storage is off."""
        if not self._database.configured:
            return []
        async with self._database.session() as session:
            rows = (await session.execute(
                select(GameCastRow).where(GameCastRow.game_id == game_id)
            )).scalars().all()
        return sorted((CastSeat(r.seat, r.character_id, r.chosen) for r in rows),
                      key=lambda c: seat_number(c.seat))

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
            await self.update_game(
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
                await self.update_game(game_id, status=DROPPED, error=shortfall)
                return
            values = {
                "status": COMPLETED,
                "finished_at": func.now(),
                "n_humans": n_humans,
                "error": None,
                **metadata,
            }
            if not await self.update_game(game_id, **values):
                return
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

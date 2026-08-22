"""Persistence operations for the unified game lifecycle and event log.

``GameRepository`` is an app-scoped service over the shared ``Database``. It owns
no connections of its own: every method opens a short-lived SQLAlchemy session for
one unit of work. Write failures remain non-fatal to live gameplay; recovery reads
remain loud so the caller can isolate a row that cannot be revived.
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import select, update

from server.database_models.game import (
    COMPLETED,
    DROPPED,
    RECOVERABLE_STATUSES,
    WAITING,
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
            stmt = insert(GameRow).values(
                {"game_id": game_id, "status": WAITING, **fields}
            )
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
            Nothing. An incomplete log marks the game ``dropped``; database
            failures are logged and suppressed.
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
        """Load the waiting rooms and running games eligible for boot recovery.

        Returns:
            Every ``GameRow`` whose status is ``waiting`` or ``running``.

        Raises:
            Exception: Propagates database failures so recovery can fail loudly.
        """
        async with self._database.session() as session:
            rows = (await session.execute(
                select(GameRow).where(GameRow.status.in_(RECOVERABLE_STATUSES))
            )).scalars().all()
        return list(rows)

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

"""Packing a finished game's prompts for storage, and the leak audit's reads and verdicts.

Every prompt an AI player is sent holds the whole conversation so far, so a game's prompts run
to megabytes of mostly repeated text; they are stored gzip-compressed, which shrinks them many
times over. The game writes its capture once, when it ends (``GameRepository.record_capture``);
the audit job (server/housekeeping/leak_audit.py) reads captures one at a time through
``CaptureAuditRepository`` and writes its verdict back on the same row.
"""

from __future__ import annotations

import gzip
from datetime import datetime
from typing import Any, NamedTuple, Sequence

from pydantic_core import to_jsonable_python
from sqlalchemy import func
from sqlmodel import select, update

from Agents.turn.eval import TurnCapture
from server.database_models.capture import PromptCaptureRow
from server.db import Database
from server.schemas.leak_audit import GameCapture

# The parts of the final game state the leak checks read (tests/leak_test.py).
LEAK_STATE_FIELDS = ("roles", "dead_roster", "day_channel", "night_actions",
                     "day_summaries", "wolf_channel")


class CaptureListing(NamedTuple):
    """One stored capture, without its (large) contents."""

    game_id: str
    captured_at: datetime
    n_prompts: int
    partial: bool


def build_capture(turns: TurnCapture, state: dict[str, Any], *, partial: bool) -> GameCapture:
    """Put a game's recorded prompts and reads together with the parts of its final state the
    checks need, turned into plain JSON so a later version of the game code can still read it."""
    final_state = {name: state.get(name) for name in LEAK_STATE_FIELDS}
    return GameCapture(
        prompt_log=to_jsonable_python(list(turns.prompts), fallback=str),
        reads_log=to_jsonable_python(list(turns.reads), fallback=str),
        final_state=to_jsonable_python(final_state, fallback=str),
        partial=partial,
    )


def encode_capture(capture: GameCapture) -> bytes:
    return gzip.compress(capture.model_dump_json().encode("utf-8"), compresslevel=6)


def decode_capture(blob: bytes) -> GameCapture:
    return GameCapture.model_validate_json(gzip.decompress(blob))


class CaptureAuditRepository:
    """The audit's side of the captures table: which games to check, and where the verdict goes."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def list_captures(self, *, since: datetime | None = None,
                            game_ids: Sequence[str] = ()) -> list[CaptureListing]:
        """The captures to audit, oldest first: the named games; else every game captured since
        ``since``, audited or not; else every game the audit has not checked yet."""
        query = select(PromptCaptureRow.game_id, PromptCaptureRow.captured_at,
                       PromptCaptureRow.n_prompts, PromptCaptureRow.partial)
        if game_ids:
            query = query.where(PromptCaptureRow.game_id.in_(list(game_ids)))
        elif since is not None:
            query = query.where(PromptCaptureRow.captured_at >= since)
        else:
            query = query.where(PromptCaptureRow.audited_at.is_(None))
        async with self._database.session() as session:
            rows = (await session.execute(query.order_by(PromptCaptureRow.captured_at))).all()
        return [CaptureListing(*row) for row in rows]

    async def load_capture(self, game_id: str) -> GameCapture:
        async with self._database.session() as session:
            blob = (await session.execute(
                select(PromptCaptureRow.capture).where(PromptCaptureRow.game_id == game_id)
            )).scalar_one()
        return decode_capture(blob)

    async def record_verdict(self, game_id: str, leaks: list[str]) -> None:
        async with self._database.session() as session:
            await session.execute(
                update(PromptCaptureRow).where(PromptCaptureRow.game_id == game_id)
                .values(audited_at=func.now(), leaks=leaks))
            await session.commit()

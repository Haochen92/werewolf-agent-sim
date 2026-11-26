"""Packing a finished game's evaluation cases for storage, and reading them back.

An evaluation case is the record of one thing to be judged later, such as one seat's decision
with everything the seat could see (Agents/observability/case_sink.py). A served game builds
its cases in memory as it plays. The game writes them here once, when it ends
(``GameRepository.record_eval_cases``), so that served play can be evaluated without reading
the trace store. ``EvalCaseArchive`` is the reading side: the export command lists and loads
rows, and the server's sweeper deletes rows past their shelf life.

The stored form is the form a batch run writes to its case files: one JSON object per line, each
the record the evaluation code also gets from a trace span. Each case repeats most of the game's
transcript, so the lines are gzip-compressed (a ten-seat game is about 3.4 MB as text and
0.4 MB compressed, measured on batch files, 2026-11-20).
"""

from __future__ import annotations

import gzip
import json
from datetime import datetime
from typing import Any, NamedTuple, Sequence

from pydantic_core import to_jsonable_python
from sqlmodel import delete, select

from server.database_models.eval_cases import GameEvalCasesRow
from server.db import Database

RECORD_FORMAT = "span_record_jsonl_v1"
"""One line is one case record: the span dict that ``freeze_case`` appends to the game's list."""


class EvalCasesListing(NamedTuple):
    """One game's stored cases, without their (large) contents."""

    game_id: str
    saved_at: datetime
    n_cases: int
    partial: bool
    record_format: str


def encode_cases(records: Sequence[dict[str, Any]]) -> bytes:
    lines = (json.dumps(to_jsonable_python(record, fallback=str), sort_keys=True)
             for record in records)
    return gzip.compress("\n".join(lines).encode("utf-8"), compresslevel=6)


def decode_cases(blob: bytes) -> list[dict[str, Any]]:
    text = gzip.decompress(blob).decode("utf-8")
    return [json.loads(line) for line in text.split("\n") if line]


class EvalCaseArchive:
    """The reading and expiring side of the stored cases."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def list_games(self, *, since: datetime | None = None,
                         game_ids: Sequence[str] = ()) -> list[EvalCasesListing]:
        """The games with stored cases, oldest first: the named games, else every game saved
        since ``since``, else every game."""
        query = select(GameEvalCasesRow.game_id, GameEvalCasesRow.saved_at,
                       GameEvalCasesRow.n_cases, GameEvalCasesRow.partial,
                       GameEvalCasesRow.record_format)
        if game_ids:
            query = query.where(GameEvalCasesRow.game_id.in_(list(game_ids)))
        elif since is not None:
            query = query.where(GameEvalCasesRow.saved_at >= since)
        async with self._database.session() as session:
            rows = (await session.execute(query.order_by(GameEvalCasesRow.saved_at))).all()
        return [EvalCasesListing(*row) for row in rows]

    async def load_cases(self, game_id: str) -> list[dict[str, Any]]:
        async with self._database.session() as session:
            blob = (await session.execute(
                select(GameEvalCasesRow.cases).where(GameEvalCasesRow.game_id == game_id)
            )).scalar_one()
        return decode_cases(blob)

    async def delete_saved_before(self, cutoff: datetime) -> int:
        """Delete every game's cases saved before ``cutoff``. Returns how many rows went; 0
        when storage is off."""
        if not self._database.configured:
            return 0
        async with self._database.session() as session:
            result = await session.execute(
                delete(GameEvalCasesRow).where(GameEvalCasesRow.saved_at < cutoff))
            await session.commit()
        return result.rowcount or 0

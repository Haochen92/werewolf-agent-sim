"""Which game a log line belongs to.

Several served games run in one process, and the engine's log lines name a seat but not a game.
Whoever runs a game sets ``GAME_ID`` at the start of its task; LangGraph copies the task's context
into the worker threads that run the engine's steps, so every line logged on the game's behalf can
be stamped with it. ``GameIdFilter`` does the stamping: attached to a log handler, it adds the
attribute ``game_id`` to every record, "-" for a line logged outside any game.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar

GAME_ID: ContextVar[str] = ContextVar("GAME_ID", default="-")


class GameIdFilter(logging.Filter):
    """Adds ``record.game_id`` from the current context. Never drops a record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.game_id = GAME_ID.get()
        return True

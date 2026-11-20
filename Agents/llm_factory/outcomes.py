"""A game's record of the turns that were not decided by its own model.

A game finishes even when a turn's model call does not go as intended: the rescue model can
answer in place of the game's model, a discussion turn can become a pass because every attempt
failed, and a vote or night action can be given a legal move by the engine. In the game's events
such a move looks like any other. This record says which turns they were, so that a result can
be read knowing how much of the play was the intended model's.

One per game, held on the game's models object (``GameModels.outcomes``) beside the stall count.
The turn code notes a turn here at the point it leaves the ordinary path. The seats' turns run on
several threads, so the record takes a lock.
"""

from __future__ import annotations

import threading
from typing import Any

RESCUE = "rescue"
"""The rescue model decided the turn: the game's model stalled, failed, or was being skipped."""
FAILED_PASS = "failed_pass"
"""A discussion turn recorded as a pass because every attempt to generate it failed."""
RANDOM_DEFAULT = "random_default"
"""A vote or night action the engine chose at random among the legal targets."""
NO_ACTION_DEFAULT = "no_action_default"
"""A night role given its no-action choice by the engine."""

PATHS = (RESCUE, FAILED_PASS, RANDOM_DEFAULT, NO_ACTION_DEFAULT)

_MAX_TURNS_LISTED = 1000  # a game has a few hundred turns; the cap only bounds a long process


class TurnOutcomes:
    """Counts by path, and the turns themselves (seat, day, kind of turn, path)."""

    def __init__(self, saved: dict[str, Any] | None = None) -> None:
        """``saved`` is an earlier ``snapshot()``, which a game resumed after a restart
        carries on from."""
        saved = saved or {}
        self._lock = threading.Lock()
        self._counts: dict[str, int] = {path: int((saved.get("counts") or {}).get(path, 0))
                                        for path in PATHS}
        self._turns: list[dict[str, Any]] = list(saved.get("turns") or [])
        self.changed = False
        """True when something was noted since the last ``snapshot()``."""

    def note(self, path: str, *, player: str, day: int | None, turn: str) -> None:
        """Record that ``player``'s turn of kind ``turn`` (the output key: day_votes,
        day_channel, a night role's field) on ``day`` left the ordinary path by ``path``."""
        with self._lock:
            self._counts[path] = self._counts.get(path, 0) + 1
            if len(self._turns) < _MAX_TURNS_LISTED:
                self._turns.append({"player": player, "day": day, "turn": turn, "path": path})
            self.changed = True

    def count(self, path: str) -> int:
        with self._lock:
            return self._counts.get(path, 0)

    def snapshot(self) -> dict[str, Any]:
        """The record as plain JSON, for the game's row. Clears ``changed``."""
        with self._lock:
            self.changed = False
            return {"counts": dict(self._counts), "turns": [dict(turn) for turn in self._turns]}

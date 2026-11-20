"""What an extraction run has paid for, kept in the run's folder so a stopped run can resume.

A Message Batch can take hours and is paid for once it is created. The journal records each batch's
id by stage as soon as it exists, the answer of each game's direct first call (no batch holds it), and
the games the run took, in order. Rerunning the job with the same run name then collects the batches
instead of sending them again (``batch_parse(batch_id=...)``) and skips the direct calls already made.
The request ids are positional (``g{game}_c{call}``), so a resumed run must take the same games in the
same order; the job reads them from here rather than selecting again.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from pydantic import BaseModel


class RunJournal:
    """One run's journal, ``batches.json`` in its folder; with no path it remembers nothing."""

    def __init__(self, path: Path | None = None):
        self.path = path
        self.data: dict = json.loads(path.read_text()) if path and path.exists() else {}

    def _save(self) -> None:
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, indent=2))

    def games(self) -> list[str] | None:
        """The game ids an earlier start of this run took, in order; None for a new run."""
        return self.data.get("games")

    def record_games(self, game_ids: list[str]) -> None:
        self.data["games"] = list(game_ids)
        self._save()

    def batch_id(self, stage: str) -> str | None:
        """The batch an earlier start of this run created for ``stage`` ("extract", "retry", "dehalo")."""
        return self.data.get("batches", {}).get(stage)

    def on_submit(self, stage: str) -> Callable[[str], None]:
        """A callback that records a new batch's id for ``stage`` the moment it is created."""
        def record(batch_id: str) -> None:
            self.data.setdefault("batches", {})[stage] = batch_id
            self._save()
        return record

    def warm_answer(self, key: str, schema: type[BaseModel]) -> BaseModel | None:
        """A direct call's saved answer, or None if this run has not made that call."""
        saved = self.data.get("warm", {}).get(key)
        return None if saved is None else schema.model_validate(saved)

    def save_warm_answer(self, key: str, answer: BaseModel | None) -> None:
        if answer is not None:
            self.data.setdefault("warm", {})[key] = answer.model_dump(mode="json")
            self._save()

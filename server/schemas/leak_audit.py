"""What a served game leaves behind for the leak audit: every prompt its agents were sent, every
private read they made, and the parts of the final game state the checks compare them against.
Saved compressed when the game ends (server/storage/prompt_captures.py); read back by the audit
(server/housekeeping/leak_audit.py)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GameCapture(BaseModel):
    prompt_log: list[dict[str, Any]] = Field(default_factory=list)
    """One entry per prompt an agent was sent, in the shape ``log_prompt`` writes
    (Agents/turn/eval.py): who, which decision, which day, and the full prompt input."""
    reads_log: list[dict[str, Any]] = Field(default_factory=list)
    """One entry per decision that carried private reads: who made them and the reads themselves."""
    final_state: dict[str, Any] = Field(default_factory=dict)
    """The final game state's roles, dead_roster, day_channel, night_actions, day_summaries and
    wolf_channel, as plain JSON. The checks need nothing else from the state."""
    partial: bool = False
    """True when the game was resumed after a server restart: the prompts sent before the restart
    were lost with the old process, so the audit covers only the part played after it."""

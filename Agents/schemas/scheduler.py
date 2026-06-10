"""Pure data types for the sequential-discussion scheduler (Agents.turn.scheduler).

Internal only: the scheduler is deterministic Python with no LLM, so these never reach a model.
Balance is the per-directed-pair obligation ledger entry; ReactiveItem groups one debtor's open
obligations into a single turn; Decision is the scheduler's per-cycle verdict.

Field docstrings are IDE-only — these are never serialized to a model, so they don't leak.
"""

from pydantic import BaseModel
from typing import Literal

from Agents.schemas.game_events import FiringReason


class Balance(BaseModel):
    """One directed (creditor->debtor) obligation in the reactive ledger; see build_reactive_queue."""

    cycles: int = 0
    """Completed open->discharge cycles for this directed (creditor->debtor) pair; the K-cap
    counter. Blocks the (K+1)th open within a burst; reset by the cooldown."""
    open_sequence: int | None = None
    """Seq the current obligation opened at; None = not open. Presence means open, value is its recency."""
    last_touch_sequence: int | None = None
    """Seq of this pair's last activity, stamped on BOTH open and close; drives the cooldown reset."""


class ReactiveItem(BaseModel):
    """A debtor's netted-out open obligations for one turn (it answers all creditors at once)."""

    agent_id: str
    """The obligated agent (debtor); answers all its creditors in one grouped turn."""
    creditors: list[str]
    """Who the debtor owes a response to; names feed FiringReason.owes."""
    latest_sequence: int
    """Max open_sequence over this debtor's open pairs; the reactive sort key (descending)."""


class Decision(BaseModel):
    """The scheduler's per-cycle verdict: fire `speaker` with `firing_reason`, or `terminate`."""

    terminate: bool = False
    """True = end the discussion this cycle; no speaker fires."""
    speaker: str | None = None
    """Next speaker (debtor for reactive, ranked agent for proactive). None iff terminate."""
    firing_reason: FiringReason | None = None
    """Why this turn fired; rides the Send payload and is stamped onto the resulting DayChannel.
    None iff terminate."""
    terminate_reason: Literal["cap", "trailing_passes", "no_eligible"] | None = None
    """Why the discussion ended (trace only). Set iff terminate."""

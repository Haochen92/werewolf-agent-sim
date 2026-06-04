from pydantic import BaseModel, Field
from typing import Literal

from Agents.schemas.game_events import FiringReason


class Balance(BaseModel):
    cycles: int = Field(
        default=0,
        description="Completed open->discharge cycles for this directed (creditor->debtor) pair; the K-cap counter. Blocks the (K+1)th open within a burst; reset by the cooldown.",
    )
    open_sequence: int | None = Field(
        default=None,
        description="Seq the current obligation opened at; None = not open. Presence means open, value is its recency.",
    )
    last_touch_sequence: int | None = Field(
        default=None,
        description="Seq of this pair's last activity, stamped on BOTH open and close; drives the cooldown reset.",
    )


class ReactiveItem(BaseModel):
    agent_id: str = Field(
        description="The obligated agent (debtor); answers all its creditors in one grouped turn.",
    )
    creditors: list[str] = Field(
        description="Who the debtor owes a response to; names feed FiringReason.owes.",
    )
    latest_sequence: int = Field(
        description="Max open_sequence over this debtor's open pairs; the reactive sort key (descending).",
    )


class Decision(BaseModel):
    terminate: bool = Field(
        default=False,
        description="True = end the discussion this cycle; no speaker fires.",
    )
    speaker: str | None = Field(
        default=None,
        description="Next speaker (debtor for reactive, ranked agent for proactive). None iff terminate.",
    )
    firing_reason: FiringReason | None = Field(
        default=None,
        description="Why this turn fired; rides the Send payload and is stamped onto the resulting DayChannel. None iff terminate.",
    )
    terminate_reason: Literal["cap", "trailing_passes", "no_eligible"] | None = Field(
        default=None,
        description="Why the discussion ended (trace only). Set iff terminate.",
    )

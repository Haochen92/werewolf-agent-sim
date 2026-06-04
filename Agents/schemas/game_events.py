from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AddressedTarget(BaseModel):
    target: str = Field(
        description="Player ID or name."
    )

    addressed_form: Literal["question", "response", "mention"] = Field(
        description="question=asks target; response=replies to target; mention=refers to target."
    )

    stance: Literal["accusation", "defense", "agreement", "neutral"] = Field(
        description="accusation=suspects/blames; defense=supports/protects; agreement=agrees; neutral=no clear stance."
    )


class FiringReason(BaseModel):
    tier: Literal["reactive", "proactive"] = Field(
        description="reactive=turn forced by an open obligation; proactive=scheduler-initiated on a quiet cycle.",
    )
    owes: list[str] = Field(
        default_factory=list,
        description="Creditors the speaker owes a response to (reactive only). Empty for proactive.",
    )


class DayChannel(BaseModel):
    day: int
    seq: int
    player: str
    message: str
    addressed_targets: list[AddressedTarget] = Field(default_factory=list)
    passed: bool = Field(default=False, description="True = proactive pass marker (hidden, not counted).")
    firing_reason: FiringReason | None = Field(
        default=None,
        description="Scheduler trace for why this turn fired; observability only, hidden from agents. None for non-scheduler (e.g. legacy/human) messages.",
    )


class DaySummary(BaseModel):
    day: int
    summary: str


class WolfChannel(BaseModel):
    day: int
    round: int
    wolf: str
    message: str
    vote: str


class InvestigatorResult(BaseModel):
    day: int
    player_investigated: str
    role_revealed: str


class DayVote(BaseModel):
    voter: str
    votee: str

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


class DayChannel(BaseModel):
    day: int
    seq: int
    player: str
    message: str
    addressed_targets: list[AddressedTarget] = Field(default_factory=list)


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

from __future__ import annotations

from pydantic import BaseModel, Field


class WolfNightDiscussOutput(BaseModel):
    updated_strategy: str
    message: str
    vote_target: str


class DayDiscussOutput(BaseModel):
    updated_strategy: str
    message: str | None


class DayVoteOutput(BaseModel):
    vote_target: str


class DaySummaryOutput(BaseModel):
    summary: str


class HealerOutput(BaseModel):
    updated_strategy: str
    healer_target: str


class InvestigatorOutput(BaseModel):
    updated_strategy: str
    investigator_target: str


class SituationSummary(BaseModel):
    situations: list[str] = Field(
        description=(
            "1-3 discrete situations the player currently faces, each as a 2-3 "
            "sentence description of a game dynamic suitable for semantic search."
        ),
        min_length=1,
        max_length=3,
    )

from __future__ import annotations

from pydantic import BaseModel, Field


class WolfNightDiscussOutput(BaseModel):
    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    message: str
    vote_target: str
    updated_strategy: str


class DayDiscussOutput(BaseModel):
    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    message: str | None
    updated_strategy: str


class DayVoteOutput(BaseModel):
    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    vote_target: str
    updated_strategy: str


class DaySummaryOutput(BaseModel):
    summary: str


class HealerOutput(BaseModel):
    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    healer_target: str
    updated_strategy: str


class InvestigatorOutput(BaseModel):
    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    investigator_target: str
    updated_strategy: str


class SituationSummary(BaseModel):
    situations: list[str] = Field(
        description=(
            "1-3 discrete situations the player currently faces, each as a 2-3 "
            "sentence description of a game dynamic suitable for semantic search."
        ),
        min_length=1,
        max_length=3,
    )

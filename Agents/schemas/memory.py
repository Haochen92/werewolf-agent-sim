from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from Agents.constants import roles


class Observation(BaseModel):
    perspective: str = Field(
        description=(
            "The role this observation is most useful for: wolf, villager, "
            "healer, or investigator"
        )
    )
    content: str = Field(
        description=(
            "A single observation in Scenario -> Approach -> Outcome format. "
            "Scenario describes players by publicly known role status at the "
            "time; Approach and Outcome may use actual roles. No player IDs. "
            "2-4 sentences."
        )
    )

    @field_validator("perspective")
    def validate_perspective(cls, value: str) -> str:
        if value not in roles:
            raise ValueError(
                f"{value} is not a valid role. Perspective must be one of {roles}"
            )
        return value


class StrategyPoint(BaseModel):
    perspective: str = Field(
        description=(
            "The role this strategy point is most useful for: wolf, villager, "
            "healer, or investigator"
        )
    )
    situation: str = Field(
        description=(
            "The situational trigger for this principle. Start with 'When...' or "
            "'If...'. Must be specific enough for semantic search to match similar "
            "future game states, and describe players by publicly known role "
            "status at the time rather than hidden roles or player IDs."
        )
    )
    action: str = Field(
        description=(
            "The recommended action to take in the described situation. Concrete "
            "and prescriptive; may refer to the role this point is assigned to."
        )
    )

    @field_validator("perspective")
    def validate_perspective(cls, value: str) -> str:
        if value not in roles:
            raise ValueError(
                f"{value} is not a valid role. Perspective must be one of {roles}"
            )
        return value


class GameStrategyOutput(BaseModel):
    observations: list[Observation] = Field(
        description="Key strategic observations extracted from the full game"
    )
    strategy_points: list[StrategyPoint] = Field(
        description=(
            "Tactical strategy principles extracted from the full game, each with "
            "a situational trigger and recommended action"
        )
    )


class StoredStrategy(BaseModel):
    game_id: Optional[str] = ""
    content: str
    created_at: datetime


class StoredObservation(BaseModel):
    observation_count: int
    last_observed: datetime
    game_id: Optional[str] = ""
    content: str


class StoredStrategyPoint(BaseModel):
    observation_count: int
    last_observed: datetime
    game_id: Optional[str] = ""
    content: str
    action: str = ""


class RetrievedObservation(BaseModel):
    key: str
    observation: StoredObservation
    matched_situation: str
    score: float | None = None


class RetrievedStrategyPoint(BaseModel):
    key: str
    strategy_point: StoredStrategyPoint
    matched_situation: str
    score: float | None = None

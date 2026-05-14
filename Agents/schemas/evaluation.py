from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DayVote,
    InvestigatorResult,
    WolfChannel,
)
from Agents.schemas.memory import RetrievedObservation, RetrievedStrategyPoint


ActionType = Literal["discussion", "vote"]


class EvalPrivateContext(BaseModel):
    previous_strategy: str = ""
    day_summaries: list[DaySummary] = Field(default_factory=list)
    wolf_channel: list[WolfChannel] = Field(default_factory=list)
    investigator_results: list[InvestigatorResult] = Field(default_factory=list)
    surviving_players: list[str] = Field(default_factory=list)
    surviving_wolves: list[str] = Field(default_factory=list)
    surviving_villagers: list[str] = Field(default_factory=list)


class EvalCase(BaseModel):
    schema_version: str = "eval_case_v1"
    trace_id: str = ""
    observation_id: str = ""
    span_name: str = ""
    player_id: str
    player_role: str
    day: int
    round: int
    action_type: ActionType
    visible_discussion: list[DayChannel] = Field(default_factory=list)
    private_context: EvalPrivateContext = Field(default_factory=EvalPrivateContext)
    memory_enabled: bool
    retrieval_skipped_reason: str | None = None
    situations: list[str] = Field(default_factory=list)
    retrieved_observations: list[RetrievedObservation] = Field(default_factory=list)
    retrieved_strategy_points: list[RetrievedStrategyPoint] = Field(default_factory=list)
    agent_message: DayChannel | None = None
    agent_vote: DayVote | None = None
    updated_strategy: str = ""

    @property
    def game_phase_key(self) -> tuple[str, str, int, ActionType]:
        return self.trace_id, self.player_role, self.day, self.action_type

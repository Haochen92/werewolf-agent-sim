from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from Agents.constants import ActionPhase
from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DayVote,
    InvestigatorResult,
    WolfChannel,
)
from Agents.schemas.memory import RetrievedObservation, RetrievedStrategyPoint


class EvalPrivateContext(BaseModel):
    previous_strategy: str = ""
    day_summaries: list[DaySummary] = Field(default_factory=list)
    wolf_channel: list[WolfChannel] = Field(default_factory=list)
    investigator_results: list[InvestigatorResult] = Field(default_factory=list)
    surviving_players: list[str] = Field(default_factory=list)
    surviving_wolves: list[str] = Field(default_factory=list)
    surviving_villagers: list[str] = Field(default_factory=list)


class EvalCase(BaseModel):
    schema_version: str = "eval_case_v2"
    trace_id: str = ""
    observation_id: str = ""
    span_name: str = ""
    player_id: str
    player_role: str
    day: int
    round: int
    action_phase: ActionPhase
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
    adopted_strategy_keys: list[int] = Field(default_factory=list)
    adopted_strategy_store_keys: list[str] = Field(default_factory=list)

    @property
    def game_phase_key(self) -> tuple[str, str, int, ActionPhase]:
        return self.trace_id, self.player_role, self.day, self.action_phase


# ---------------------------------------------------------------------------
# Extraction eval case
# ---------------------------------------------------------------------------


class ExtractionCase(BaseModel):
    schema_version: str = "extraction_case_v1"
    trace_id: str = ""
    observation_id: str = ""
    span_name: str = ""
    game_id: str = ""
    game_outcome: str = ""
    roles: dict[str, str] = Field(default_factory=dict)
    formatted_discussions: str = ""
    formatted_strategy_notes: str = ""
    observations: list[dict] = Field(default_factory=list)
    strategy_points: list[dict] = Field(default_factory=list)
    model_used: str = ""


# ---------------------------------------------------------------------------
# Dedup eval case
# ---------------------------------------------------------------------------


class DedupCandidate(BaseModel):
    candidate_number: int
    key: str = ""
    similarity: float = 0.0
    observation_count: int = 1
    situation: str = ""
    action: str | None = None
    approach: str | None = None
    outcome: str | None = None


class DedupCase(BaseModel):
    schema_version: str = "dedup_case_v1"
    trace_id: str = ""
    observation_id: str = ""
    span_name: str = ""
    game_id: str = ""
    item_type: Literal["observation", "strategy_point"] = "strategy_point"
    perspective: str = ""
    action_phase: str = ""
    new_entry: dict = Field(default_factory=dict)
    candidates: list[DedupCandidate] = Field(default_factory=list)
    decision: str = ""
    decision_detail: dict | None = None
    auto: bool = False
    similarity_scores: dict[str, float] | None = None

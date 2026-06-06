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
    vigilante_results: list[str] = Field(default_factory=list)
    surviving_players: list[str] = Field(default_factory=list)
    surviving_wolves: list[str] = Field(default_factory=list)
    surviving_villagers: list[str] = Field(default_factory=list)


class NightAction(BaseModel):
    """A single-target night decision (heal / investigate / kill / shoot).

    The day eval case captures a message or a vote; a night action is a target
    selection instead, so it gets its own field on the eval case. ``target`` is
    ``None`` for a no-op (e.g. the vigilante banking its bullet).
    """

    role: str
    target: str | None = None


class EvalProvenance(BaseModel):
    """Identity of the data/config that produced an eval case.

    The frozen dataset record embeds the ``EvalCase`` but strips it from the
    Langfuse trace, so without this the store/config that conditioned a
    retrieval is only recoverable by rejoining the trace. Stamping it here keeps
    a frozen case self-describing — the same philosophy as the per-record
    ``runtime_fingerprint`` that ``run_batch`` already records. (Model / prompt /
    backend versioning stays at the game level: it's git-versioned code, not data.)
    """

    store_dir: str = ""
    reranking_enabled: bool = False
    filtering_enabled: bool = False


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
    # Pre-rerank candidate pool: the wide retrieval set as embedding search
    # surfaced it, BEFORE filtering/reranking narrowed and reordered it (with
    # per-item embedding scores). Reranker training + retrieval eval need the
    # candidates that entered reranking, not just the final top-k. Empty when no
    # wide retrieval ran (no rerank/filter) — then ``retrieved_*`` IS the pool.
    candidate_observations: list[RetrievedObservation] = Field(default_factory=list)
    candidate_strategy_points: list[RetrievedStrategyPoint] = Field(default_factory=list)
    provenance: EvalProvenance = Field(default_factory=EvalProvenance)
    agent_message: DayChannel | None = None
    agent_vote: DayVote | None = None
    agent_night_action: NightAction | None = None
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


# ---------------------------------------------------------------------------
# Day-summary eval case
# ---------------------------------------------------------------------------


class DaySummaryCase(BaseModel):
    """A frozen day-summary decision, judgeable by ``run_day_summary_judge``.

    The day summary runs in BOTH memory arms (it's pre-memory), so capturing it
    as a case makes day-summary quality evaluable on real games — the judge
    already consumes ``(raw_discussion, summary, day)`` verbatim. ``raw_discussion``
    is the day's transcript as ``{player, round, message}`` dicts.
    """

    schema_version: str = "day_summary_case_v1"
    trace_id: str = ""
    observation_id: str = ""
    span_name: str = ""
    game_id: str = ""
    day: int = 0
    raw_discussion: list[dict] = Field(default_factory=list)
    summary: str = ""
    model_used: str = ""

"""Eval-case schemas: frozen, self-describing records of each decision the pipeline makes.

Storage/tracing artifacts (serialized to Langfuse spans + frozen datasets), NOT structured-output
schemas — they are never sent to a model, so they carry full docstrings/field descriptions freely.
Each case bundles everything needed to re-judge a decision offline; ``schema_version`` gates format
migrations across runs.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from Agents.schemas.roles import ActionPhase
from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DayVote,
    DeathRecord,
    InvestigatorResult,
    WolfChannel,
)
from Agents.schemas.memory import RetrievedObservation, RetrievedStrategyPoint
from Agents.schemas.output import MemoryVerdict, PlayerRead, StrategyVerdict


class EvalPrivateContext(BaseModel):
    """The role-private information set an agent could see at decision time (beyond the public
    channel); embedded in EvalCase so a frozen case reproduces exactly what the agent knew."""

    previous_strategy: str = ""
    day_summaries: list[DaySummary] = Field(default_factory=list)
    wolf_channel: list[WolfChannel] = Field(default_factory=list)
    investigator_results: list[InvestigatorResult] = Field(default_factory=list)
    vigilante_results: list[str] = Field(default_factory=list)
    surviving_players: list[str] = Field(default_factory=list)
    surviving_wolves: list[str] = Field(default_factory=list)
    surviving_villagers: list[str] = Field(default_factory=list)
    dead_roster: list[DeathRecord] = Field(default_factory=list)
    """Public dead roster the turn saw (dead player -> revealed role + when) — the board block the
    reads bundle renders. Public, not private, but captured so a frozen case reproduces the exact
    prompt without rejoining the game record (the T1c study had to rebuild it from run records).
    Empty on pre-2026-07-09 records."""
    cast_role_counts: dict[str, int] = Field(default_factory=dict)
    """Public fixed-cast census (role -> count, no identities) the alive-roles line derives from;
    with dead_roster this reproduces the '== Roles still in play ==' text exactly (see
    format_alive_roles). Empty on pre-2026-07-09 records."""


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
    """One frozen agent-decision case (day message / vote / night action), self-contained for
    offline judging: the visible discussion + private context (the information set), the retrieval
    (final picks + the pre-rerank candidate pool), provenance, and the agent's actual output."""

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
    situation_dimensions: list[dict] = Field(default_factory=list)
    """Structured query-situation dims per situation (the v6 cell situation object's model_dump:
    exposure_class, info_landscape_class, criticality numbers, consensus_direction, ...), parallel to
    `situations`. Empty on the legacy retrieval path / memory-off. Eval-only: lets offline screens gate
    on the QUERY-side enums (dimension-gating efficacy) without re-deriving them with an LLM."""
    retrieved_observations: list[RetrievedObservation] = Field(default_factory=list)
    retrieved_strategy_points: list[RetrievedStrategyPoint] = Field(default_factory=list)
    candidate_observations: list[RetrievedObservation] = Field(default_factory=list)
    """Pre-rerank candidate pool: the wide retrieval set as embedding search
    surfaced it, BEFORE filtering/reranking narrowed and reordered it (with
    per-item embedding scores). Reranker training + retrieval eval need the
    candidates that entered reranking, not just the final top-k. Empty when no
    wide retrieval ran (no rerank/filter) — then ``retrieved_*`` IS the pool."""
    candidate_strategy_points: list[RetrievedStrategyPoint] = Field(default_factory=list)
    provenance: EvalProvenance = Field(default_factory=EvalProvenance)
    agent_message: DayChannel | None = None
    agent_vote: DayVote | None = None
    agent_night_action: NightAction | None = None
    updated_strategy: str = ""
    adopted_strategy_keys: list[int] = Field(default_factory=list)
    """The FOLLOW verdicts' indices (derived from strategy_verdicts) — kept for back-compat analysis."""
    adopted_strategy_store_keys: list[str] = Field(default_factory=list)
    strategy_verdicts: list[StrategyVerdict] = Field(default_factory=list)
    """The agent's per-strategy-point verdicts (follow/override/not_relevant, one per retrieved SP it
    judged), captured from the structured output for offline analysis + the follow-vs-override credit
    signal. Empty when memory was off or no SPs retrieved. See Agents/turn/resolve.py (_strategy_verdicts carrier)."""
    strategy_index_to_key: dict[int, str] = Field(default_factory=dict)
    """1-based prompt index -> stored-SP key for EVERY retrieved strategy point this decision (the
    adoption index_map). Lets each strategy_verdict — follow, override, AND not_relevant — be joined
    to its exact stored SP for replay/credit-assignment, not just the FOLLOWs (those are also in
    adopted_strategy_store_keys). Empty when memory was off or no SPs retrieved."""
    memory_applicability: list[MemoryVerdict] = Field(default_factory=list)
    """The agent's per-observation applicability verdicts (one per retrieved memory it judged),
    captured from the structured output for offline analysis. Empty when memory was off or none
    retrieved. See Agents/turn/resolve.py (the _memory_applicability carrier)."""
    reads: list[PlayerRead] = Field(default_factory=list)
    """The agent's per-player suspicion commitments (player, why, suspected_role, confidence),
    captured from the structured output BEFORE its strategy/action. Empty on legacy records
    (pre-2026-07-09) and on wolf-night turns (out of the shipped scope). See
    Agents/turn/resolve.py (the _reads carrier); consumed by the parked reads-scoring +
    composition-coherence analyses (validation plan T3(b))."""

    @property
    def game_phase_key(self) -> tuple[str, str, int, ActionPhase]:
        return self.trace_id, self.player_role, self.day, self.action_phase


# ---------------------------------------------------------------------------
# Extraction eval case
# ---------------------------------------------------------------------------


class ExtractionCase(BaseModel):
    """A frozen post-game extraction decision: the full-game inputs (discussions, strategy notes,
    outcome) plus the observations/strategy points extracted from them, judgeable offline."""

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
    """One existing-store entry weighed against a new entry during dedup (its similarity + the
    fields the decision saw)."""

    candidate_number: int
    key: str = ""
    similarity: float = 0.0
    observation_count: int = 1
    situation: str = ""
    action: str | None = None
    approach: str | None = None
    outcome: str | None = None


class DedupCase(BaseModel):
    """A frozen dedup decision: the new entry, the candidate pool it was compared against, and the
    verdict (auto-threshold or model), with the similarity scores that drove it."""

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

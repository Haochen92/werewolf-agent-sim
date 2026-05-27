"""Pydantic models for evaluation datasets, judge scores, and result records."""

from __future__ import annotations

from typing import Literal

from Agents.constants import ActionPhase
from pydantic import BaseModel, Field, field_validator

AttributionDirection = Literal["over", "under", "accurate"]


class JudgeScores(BaseModel):
    summary_quality: int = Field(ge=1, le=5)
    retrieval_relevance: int = Field(ge=1, le=5)
    strategy_application: int = Field(ge=1, le=5)
    grounding: int = Field(ge=1, le=5)
    brief_reasoning: str = ""


class EvalResult(BaseModel):
    span_kind: str = "agent_action_eval"
    span_name: str
    trace_id: str
    observation_id: str
    role: str
    day: int
    round: int
    action_phase: ActionPhase
    model: str
    model_type: str
    eval_version: str
    sampling_seed: int
    scores: JudgeScores


class LessonCluster(BaseModel):
    lesson: str
    items: list[int] = Field(min_length=1)
    relevant: bool = True


class RetrievalScores(BaseModel):
    clusters: list[LessonCluster] = Field(default_factory=list)
    relevance: int = Field(ge=1, le=5)
    unique_lessons: int = Field(ge=0)
    efficiency: int = Field(ge=1, le=5)
    brief_reasoning: str = ""


class ApplicationScores(BaseModel):
    action_quality: int = Field(ge=1, le=5)
    strategy_application: int = Field(ge=1, le=5)
    grounding: int = Field(ge=1, le=5)
    adoption_accuracy: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description=(
            "Does the agent's self-reported adoption list match its observable "
            "behavior? null when adoption self-report is not captured."
        ),
    )
    attribution_direction: AttributionDirection | None = Field(
        default=None,
        description=(
            "Direction of adoption mismatch: 'over' if agent claims points it "
            "didn't follow, 'under' if agent omits points it clearly used, "
            "'accurate' if self-report matches behavior. null when adoption "
            "self-report is not captured."
        ),
    )
    fabricated_claims: list[str] = Field(default_factory=list)
    brief_reasoning: str = ""


class CostEstimate(BaseModel):
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int = 0
    cache_read_tokens: int = 0
    total_tokens: int
    estimated_cost_usd: float | None = None
    pricing_version: str
    token_estimation_method: str


class SummaryDimensionScores(BaseModel):
    faithfulness: int = Field(ge=1, le=5)
    specificity: int = Field(ge=1, le=5)
    retrieval_usefulness: int = Field(ge=1, le=5)
    non_redundancy: int = Field(ge=1, le=5)
    role_perspective: int = Field(ge=1, le=5)


class PairwiseJudgeScores(BaseModel):
    output_a: SummaryDimensionScores
    output_b: SummaryDimensionScores
    winner: Literal["a", "b", "tie"]
    confidence: int = Field(ge=1, le=5)
    brief_reasoning: str = ""


class ExtractionScores(BaseModel):
    specificity: int = Field(
        ge=1,
        le=5,
        description=(
            "Do situation descriptions use qualifying detail from the dimensional "
            "framework (information landscape, consensus texture, agent exposure, "
            "game phase) to make them distinctive for semantic search? "
            "1=vague enough to match any game; 5=precisely scoped to specific dynamics"
        ),
    )
    epistemic_compliance: int = Field(
        ge=1,
        le=5,
        description=(
            "Do entries respect the assigned role's knowledge level per the "
            "epistemic status rule? Own findings and system-confirmed roles are "
            "valid; hidden ground truth or omniscient narrator perspective is not. "
            "1=pervasive epistemic violations; 5=every claim at correct certainty level"
        ),
    )
    grounding: int = Field(
        ge=1,
        le=5,
        description=(
            "Is every claim in the extracted items traceable to the game transcript "
            "(discussions, wolf channel, investigator results, strategies)? "
            "1=major fabricated events or dynamics; 5=every detail traceable to source"
        ),
    )
    coverage: int = Field(
        ge=1,
        le=5,
        description=(
            "Do the extracted items collectively cover the key strategic moments "
            "and learnings from this game for each role? "
            "1=misses the most important dynamics; 5=captures all major decision points"
        ),
    )
    diversity: int = Field(
        ge=1,
        le=5,
        description=(
            "Are the extracted items distinct from each other, or is there "
            "redundancy within the set? Same lesson from different examples counts "
            "as redundant. "
            "1=mostly duplicate advice in different words; 5=every item adds a distinct idea"
        ),
    )
    perspective_compliance: int = Field(
        ge=1,
        le=5,
        description=(
            "Are observations written from the assigned role's perspective? "
            "Approach should describe the assigned role's own actions, not the "
            "opposing side's. Situation and outcome should be framed from that "
            "role's viewpoint. Strategy points are exempt from this dimension. "
            "1=approach routinely describes opposing side's actions; "
            "5=every observation consistently framed from assigned role's perspective"
        ),
    )
    strategy_depth: int = Field(
        ge=1,
        le=5,
        description=(
            "Strategy points ONLY — observations exempt (score 5). "
            "Does the action field provide concrete conditions, a specific "
            "recommended action, and reasoning for WHY it works in this context? "
            "1=generic platitude ('be careful', 'don't reveal your role'); "
            "3=concrete action but reasoning is thin or obvious; "
            "5=specific technique with conditions, reasoning, and learned nuance"
        ),
    )
    novelty: int = Field(
        ge=1,
        le=5,
        description=(
            "Does each item capture a non-obvious mechanism or insight, or "
            "restate common-sense fundamentals any experienced player knows? "
            "1=obvious advice ('eliminate active players', 'protect important players'); "
            "3=reasonable insight but not surprising; "
            "5=reframes how you'd approach the situation, surfaces a non-obvious pattern"
        ),
    )
    brief_reasoning: str = ""


class PerRoleExtractionResult(BaseModel):
    role: str
    observation_count: int = 0
    strategy_point_count: int = 0
    scores: ExtractionScores | None = None


class PerRoleExtractionScores(BaseModel):
    role_results: list[PerRoleExtractionResult] = Field(default_factory=list)

    @property
    def aggregate(self) -> dict[str, float]:
        dims = [
            "specificity", "epistemic_compliance", "grounding", "coverage",
            "diversity", "perspective_compliance", "strategy_depth", "novelty",
        ]
        scored = [r for r in self.role_results if r.scores is not None]
        if not scored:
            return {}
        return {
            dim: sum(getattr(r.scores, dim) for r in scored) / len(scored)
            for dim in dims
        }


class PairwiseExtractionScores(BaseModel):
    output_a: ExtractionScores
    output_b: ExtractionScores
    winner: Literal["a", "b", "tie"]
    confidence: int = Field(ge=1, le=5)
    brief_reasoning: str = ""

    @field_validator("winner", mode="before")
    @classmethod
    def normalize_winner(cls, v: str) -> str:
        v = str(v).strip().lower()
        if v in ("output_a", "a"):
            return "a"
        if v in ("output_b", "b"):
            return "b"
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: int) -> int:
        return max(1, min(5, int(v)))


class SituationSummaryScores(BaseModel):
    faithfulness: int = Field(
        ge=1,
        le=5,
        description=(
            "Does the summary avoid fabricating claims, roles, motives, or pressure "
            "not present in the visible discussion and private context? "
            "1=major fabrications; 5=every claim traceable to context"
        ),
    )
    specificity: int = Field(
        ge=1,
        le=5,
        description=(
            "Does the summary capture the current decision-relevant game dynamics "
            "rather than generic facts that could apply to any game state? "
            "1=vague platitudes; 5=precisely scoped to this moment's dynamics"
        ),
    )
    retrieval_usefulness: int = Field(
        ge=1,
        le=5,
        description=(
            "Would these situation descriptions retrieve strategy/observation "
            "memories that match the agent's current role, pressure, and phase? "
            "1=would match irrelevant memories; 5=would retrieve highly targeted advice"
        ),
    )
    non_redundancy: int = Field(
        ge=1,
        le=5,
        description=(
            "Does each listed situation add a distinct retrieval angle, or do "
            "multiple situations describe the same dynamic in different words? "
            "1=mostly redundant; 5=every situation adds a unique angle"
        ),
    )
    role_perspective: int = Field(
        ge=1,
        le=5,
        description=(
            "Does the summary preserve what this role privately knows and needs, "
            "framing situations from the agent's perspective rather than an "
            "omniscient narrator? "
            "1=ignores role-specific knowledge; 5=fully grounded in role perspective"
        ),
    )
    brief_reasoning: str = ""


class DaySummaryScores(BaseModel):
    completeness: int = Field(
        ge=1,
        le=5,
        description=(
            "Does the summary capture all strategically important information "
            "from the raw discussion? Accusations, defenses, claims, alliances, "
            "and pressure dynamics. "
            "1=major omissions; 5=all significant content preserved"
        ),
    )
    accuracy: int = Field(
        ge=1,
        le=5,
        description=(
            "Are attributions correct? Right player IDs, accurate characterization "
            "of who said what, no fabricated claims or misattributed reasoning. "
            "1=major errors; 5=every attribution verifiable in the transcript"
        ),
    )
    evidence_type_clarity: int = Field(
        ge=1,
        le=5,
        description=(
            "Does the summary distinguish the TYPE of evidence driving suspicion — "
            "voting records, communication style, behavioral patterns, or concrete "
            "claims? This is critical for downstream situation characterization. "
            "1=no evidence type distinction; 5=every accusation's evidence basis is explicit"
        ),
    )
    village_dynamics: int = Field(
        ge=1,
        le=5,
        description=(
            "Does the summary characterize overall discussion dynamics: village "
            "alignment (unified/split/fragmented), whether consensus is evidence-driven "
            "or social momentum, and who is driving vs. passive? "
            "1=no dynamics; 5=clear, specific characterization of village state"
        ),
    )
    epistemic_correctness: int = Field(
        ge=1,
        le=5,
        description=(
            "Does the summary treat role claims at the appropriate certainty level? "
            "Unverified claims should not be stated as fact. Confirmed roles should "
            "be distinguished from claimed roles. "
            "1=treats claims as fact; 5=correctly distinguishes certainty levels"
        ),
    )
    brief_reasoning: str = ""


class BatchDedupMergeScores(BaseModel):
    retrieval_coverage: int = Field(
        ge=1,
        le=5,
        description=(
            "Will the merged situation be retrieved by the same queries that "
            "would have matched each original source entry? "
            "1=covers only one sub-situation; 5=full retrieval reach preserved"
        ),
    )
    merge_quality: int = Field(
        ge=1,
        le=5,
        description=(
            "Is the rewritten text well-formed, specific, and an improvement? "
            "1=worse than originals; 5=clearer and more precise than any source"
        ),
    )
    information_preservation: int = Field(
        ge=1,
        le=5,
        description=(
            "Were important nuances preserved? Tactics with counts, specific "
            "conditions, mechanism detail? "
            "1=critical distinctions lost; 5=all meaningful detail retained"
        ),
    )
    fabrication_detected: bool = Field(
        default=False,
        description=(
            "Did the rewrite introduce context not present in source entries?"
        ),
    )
    brief_reasoning: str = ""


class DedupScores(BaseModel):
    decision_correctness: int = Field(
        ge=1,
        le=5,
        description=(
            "Was the correct action chosen? "
            "The test: would a player do anything meaningfully different reading "
            "one entry vs the other? If no, it should be DISCARD/MERGE not KEEP. "
            "1=clearly wrong decision; 5=unambiguously correct"
        ),
    )
    merge_quality: int = Field(
        ge=1,
        le=5,
        description=(
            "For DISCARD with rewrite or MERGE: is the rewritten text "
            "well-formed, standards-compliant, and an improvement? "
            "For KEEP or DISCARD without rewrite: score 5 (not applicable). "
            "1=rewrite is worse than originals; 5=rewrite is clear and precise"
        ),
    )
    information_preservation: int = Field(
        ge=1,
        le=5,
        description=(
            "Were important nuances from the original entries preserved in the "
            "merge/rewrite? For KEEP or DISCARD without rewrite: score 5. "
            "1=critical distinctions lost; 5=all meaningful detail retained"
        ),
    )
    fabrication_detected: bool = Field(
        default=False,
        description=(
            "Did the rewrite introduce game phase, information landscape, "
            "consensus texture, agent exposure, or any other context not "
            "explicitly present in the input entries being compared?"
        ),
    )
    brief_reasoning: str = ""

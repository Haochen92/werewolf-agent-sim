"""Pydantic models for evaluation datasets, judge scores, and result records."""

from __future__ import annotations

from typing import Literal

from Agents.constants import ActionPhase
from pydantic import BaseModel, Field

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


class PairwiseJudgeScores(BaseModel):
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

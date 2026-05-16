from __future__ import annotations

from typing import Literal

from Agents.schemas.evaluation import ActionType
from pydantic import BaseModel, Field


class JudgeScores(BaseModel):
    summary_quality: int = Field(ge=1, le=5)
    retrieval_relevance: int = Field(ge=1, le=5)
    strategy_application: int = Field(ge=1, le=5)
    brief_reasoning: str = ""


class EvalResult(BaseModel):
    span_kind: str = "agent_action_eval"
    span_name: str
    trace_id: str
    observation_id: str
    role: str
    day: int
    round: int
    action_type: ActionType
    model: str
    model_type: str
    eval_version: str
    sampling_seed: int
    scores: JudgeScores


class RedundantPair(BaseModel):
    item_numbers: list[int] = Field(min_length=2, max_length=2)
    reason: str


class RedundancyScores(BaseModel):
    redundancy_score: int = Field(ge=1, le=5)
    unique_idea_count: int = Field(ge=0)
    redundant_pairs: list[RedundantPair] = Field(default_factory=list)
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


class VariantConfig(BaseModel):
    label: str
    model: str
    prompt_id: str = "current"
    temperature: float = 0.0
    thinking_budget: int | None = None
    thinking_level: Literal["minimal", "low", "medium", "high"] | None = None


class JudgeConfig(BaseModel):
    model: str = "gemini-2.5-pro"
    prompt_id: str = "pairwise_summary_v1"
    temperature: float = 0.0


class PairwiseExperimentConfig(BaseModel):
    experiment_id: str
    component: Literal["situation_summary"]
    baseline: VariantConfig
    candidate: VariantConfig
    judge: JudgeConfig = Field(default_factory=JudgeConfig)
    alternate_order: bool = True


class PairwiseJudgeScores(BaseModel):
    winner: Literal["a", "b", "tie"]
    confidence: int = Field(ge=1, le=5)
    brief_reasoning: str = ""

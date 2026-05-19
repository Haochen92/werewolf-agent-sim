"""Pydantic models for evaluation datasets, judge scores, and result records."""

from __future__ import annotations

from typing import Literal

from Agents.schemas.evaluation import ActionType
from pydantic import BaseModel, Field


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
    action_type: ActionType
    model: str
    model_type: str
    eval_version: str
    sampling_seed: int
    scores: JudgeScores


class RedundantPair(BaseModel):
    item_numbers: list[int] = Field(min_length=2, max_length=2)
    reason: str


class RetrievalScores(BaseModel):
    relevance_score: int = Field(ge=1, le=5)
    redundancy_score: int = Field(ge=1, le=5)
    unique_idea_count: int = Field(ge=0)
    redundant_pairs: list[RedundantPair] = Field(default_factory=list)
    brief_reasoning: str = ""


class ApplicationScores(BaseModel):
    action_quality: int = Field(ge=1, le=5)
    strategy_application: int = Field(ge=1, le=5)
    grounding: int = Field(ge=1, le=5)
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

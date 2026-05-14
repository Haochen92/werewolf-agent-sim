from __future__ import annotations

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

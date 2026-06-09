"""Schemas for the downstream per-extraction dedup pipeline (Agents.memory.deduplication).

⚠️ MODEL-VISIBLE / FROZEN: StrategyDiscard / StrategyKeep / StrategyDedupDecisionOutput and the
Observation* equivalents are the structured-output contract for the dedup LLM (passed to
``with_structured_output``); their field descriptions are sent to the model. Do NOT add class
docstrings or edit their fields/descriptions without a prompt-freeze review. DedupAction /
DedupResult / DedupStats are internal (return values / stats), never sent to a model.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schemas — strategy point dedup (unchanged structure)
# ---------------------------------------------------------------------------


class StrategyDiscard(BaseModel):
    decision: Literal["D", "DISCARD"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )
    duplicate_of_candidate: int = Field(
        ge=1,
        description="The 1-based candidate number of the existing entry this duplicates",
    )


class StrategyKeep(BaseModel):
    decision: Literal["K", "KEEP"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )


class StrategyDedupDecisionOutput(BaseModel):
    result: Annotated[
        StrategyDiscard | StrategyKeep,
        Field(discriminator="decision"),
    ]


# ---------------------------------------------------------------------------
# Schemas — observation dedup (structured situation/approach/outcome)
# ---------------------------------------------------------------------------


class ObservationDiscard(BaseModel):
    decision: Literal["D", "DISCARD"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )
    duplicate_of_candidate: int = Field(
        ge=1,
        description="The 1-based candidate number of the existing observation this duplicates",
    )


class ObservationKeep(BaseModel):
    decision: Literal["K", "KEEP"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )


class ObservationDedupDecisionOutput(BaseModel):
    result: Annotated[
        ObservationDiscard
        | ObservationKeep,
        Field(discriminator="decision"),
    ]


# ---------------------------------------------------------------------------
# Common schemas
# ---------------------------------------------------------------------------


class DedupAction(str, Enum):
    """Compact dedup outcome label for stats and return values."""

    DISCARD = "A"
    REPLACE = "B"
    DIFFERENTIATE = "C"
    KEEP = "D"


class DedupResult(BaseModel):
    """Internal result with enough detail to separate auto and LLM paths."""

    action: DedupAction
    auto: bool = False
    candidates: list[dict] = Field(default_factory=list)
    decision_detail: dict | None = None
    similarity_scores: dict[str, float] | None = None


class DedupStats(BaseModel):
    """Summary of dedup outcomes for a batch of memory entries."""

    kept: int = 0
    discarded: int = 0
    replaced: int = 0
    differentiated: int = 0
    failed: int = 0  # Fell back to raw storage
    auto_kept: int = 0
    auto_discarded: int = 0
    embedding_auto_kept: int = 0
    embedding_auto_discarded: int = 0

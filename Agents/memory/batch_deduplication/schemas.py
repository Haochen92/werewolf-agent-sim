"""Schemas for the batch (cluster) dedup pipeline (Agents.memory.batch_deduplication).

⚠️ MODEL-VISIBLE / FROZEN: StrategyBatchOperation / ObservationBatchOperation and the
*BatchDedupOutput wrappers are the structured-output contract for the cluster-dedup LLM
(``with_structured_output``); their field descriptions are sent to the model. Do NOT edit their
fields/descriptions without a prompt-freeze review. NamespaceStats / ClusterPreview /
BatchDedupReport are internal report structures, never sent to a model.

TwoPassConfig is intentionally NOT here — it defaults to batch_deduplication's env-driven config
constants, so it stays colocated with them.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MemoryKind = Literal["observations", "strategy_points"]


class StrategyBatchOperation(BaseModel):
    action: Literal["DISCARD", "KEEP"]
    reasoning: str
    source_keys: list[str] = Field(
        description="Entry numbers in this cluster that the operation applies to",
        min_length=1,
    )
    survivor_key: str | None = Field(
        default=None,
        description="Entry number to preserve for DISCARD",
    )
    merged_situation: str | None = Field(
        default=None,
        description=(
            "Optional improved situation text for the survivor. "
            "Use only when combining elements from multiple entries."
        ),
    )
    merged_action: str | None = Field(
        default=None,
        description=(
            "Optional improved action text for the survivor. "
            "Use only when combining elements from multiple entries."
        ),
    )


class ObservationBatchOperation(BaseModel):
    action: Literal["DISCARD", "MERGE", "KEEP"]
    reasoning: str
    source_keys: list[str] = Field(
        description="Entry numbers in this cluster that the operation applies to",
        min_length=1,
    )
    survivor_key: str | None = Field(
        default=None,
        description="Entry number to preserve for DISCARD or MERGE",
    )
    merged_situation: str | None = Field(
        default=None,
        description="Merged situation text for MERGE",
    )
    merged_approach: str | None = Field(
        default=None,
        description="Merged approach with all tactics and counts for MERGE",
    )
    merged_outcome: str | None = Field(
        default=None,
        description="Merged outcome for MERGE",
    )


class StrategyBatchDedupOutput(BaseModel):
    operations: list[StrategyBatchOperation]


class ObservationBatchDedupOutput(BaseModel):
    operations: list[ObservationBatchOperation]


class NamespaceStats(BaseModel):
    memory_kind: MemoryKind
    role: str
    items: int = 0
    clusters: int = 0
    processed_clusters: int = 0
    skipped_clusters: int = 0
    operations: int = 0
    discarded: int = 0
    replaced: int = 0
    differentiated: int = 0
    merged: int = 0
    kept: int = 0
    frozen: int = 0
    failed: int = 0
    dry_run: bool = True


class ClusterPreview(BaseModel):
    memory_kind: MemoryKind
    role: str
    size: int
    keys: list[str]
    previews: list[str]


class BatchDedupReport(BaseModel):
    apply: bool
    seed_store_dir: str
    dump_store_dir: str
    stats: list[NamespaceStats] = Field(default_factory=list)
    clusters: list[ClusterPreview] = Field(default_factory=list)

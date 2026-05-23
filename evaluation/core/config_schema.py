"""Pydantic models for evaluation config files.

These models describe runnable experiment and dataset-builder configs. Runtime
result schemas live in ``evaluation.core.schemas``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class VariantConfig(BaseModel):
    """Model/prompt settings for a replayed agent component."""

    label: str
    model: str
    prompt_id: str = "current"
    temperature: float = 0.0
    thinking_budget: int | None = None
    thinking_level: Literal["minimal", "low", "medium", "high"] | None = None


class JudgeConfig(BaseModel):
    """Model settings for an LLM judge."""

    model: str = "gemini-2.5-pro"
    prompt_id: str = "pairwise_summary_v1"
    temperature: float = 0.0


class DatasetBuildConfig(BaseModel):
    """Config for freezing Langfuse game traces into a local eval dataset."""

    eval_set_id: str
    session_prefix: str | None = None
    session_id: str | None = None
    session_ids: list[str] | None = None
    batch_results: Path | None = None
    trace_ids: list[str] | None = None
    created_from: str | None = None
    max_games: int = Field(default=5, ge=0)
    per_role_per_phase: int = Field(default=1, ge=1)
    max_samples: int = Field(default=40, ge=0)
    seed: int = 0
    output: Path | None = None
    overwrite: bool = False

    @model_validator(mode="after")
    def require_one_source(self) -> "DatasetBuildConfig":
        """Ensure the dataset has exactly one Langfuse trace source."""
        sources = [
            self.session_prefix,
            self.session_id,
            self.session_ids,
            self.batch_results,
            self.trace_ids,
        ]
        provided_count = sum(source not in (None, "", []) for source in sources)
        if provided_count != 1:
            raise ValueError(
                "Exactly one of session_prefix, session_id, session_ids, "
                "batch_results, or trace_ids must be set."
            )
        return self


class PairwiseExperimentConfig(BaseModel):
    """Config for comparing two variants of a replayed component."""

    experiment_id: str
    component: Literal["situation_summary"]
    dataset: Path | None = None
    baseline: VariantConfig
    candidate: VariantConfig
    judge: JudgeConfig = Field(default_factory=JudgeConfig)
    alternate_order: bool = True
    output: Path | None = None
    max_cases: int = Field(default=0, ge=0)
    sleep_seconds: float = Field(default=0.0, ge=0)


class MemorySnapshotConfig(BaseModel):
    """A pair of exported memory-store JSON files used for replay."""

    label: str
    observations_path: Path
    strategy_points_path: Path


class RetrievalPipelineConfig(BaseModel):
    """Describes which retrieval post-processing steps to apply."""

    label: str
    filtering: bool = False
    reranking: bool = False
    dedup_threshold: float = Field(default=0.92, ge=0.0, le=1.0)
    mmr_lambda: float = Field(default=0.8, ge=0.0, le=1.0)
    mmr_top_k: int = Field(default=5, ge=1)


DEFAULT_RETRIEVAL_PIPELINE = RetrievalPipelineConfig(label="baseline")


class RetrievalExperimentConfig(BaseModel):
    """Config for replaying captured situation queries against memory snapshots."""

    dataset: Path
    snapshots: list[MemorySnapshotConfig] = Field(min_length=1)
    pipelines: list[RetrievalPipelineConfig] = Field(
        default_factory=lambda: [DEFAULT_RETRIEVAL_PIPELINE],
    )
    top_k: int = Field(default=3, ge=1)
    max_retrieved_items: int = Field(default=0, ge=0)
    output: Path | None = None
    max_samples: int = Field(default=0, ge=0)
    judge: bool = False
    judge_model: str = "gemini-2.5-flash"
    judge_thinking_level: str | None = None
    sleep_seconds: float = Field(default=1.0, ge=0)


class ApplicationExperimentConfig(BaseModel):
    """Config for replaying final discussion/vote actions from frozen cases."""

    dataset: Path
    memory_mode: Literal["captured", "none"] = "captured"
    output: Path | None = None
    max_samples: int = Field(default=0, ge=0)
    judge: bool = False
    judge_model: str = "gemini-2.5-pro"
    sleep_seconds: float = Field(default=1.0, ge=0)


class CapturedEvaluationConfig(BaseModel):
    """Config for judging captured EvalCase rows without replaying any stage."""

    dataset: Path
    output: Path | None = None
    max_samples: int = Field(default=0, ge=0)
    judge_model: str = "gemini-2.5-pro"
    sleep_seconds: float = Field(default=1.0, ge=0)


class E2EExperimentConfig(BaseModel):
    """Config for turn-level replay of summary, retrieval, action, and judging."""

    dataset: Path
    snapshots: list[MemorySnapshotConfig] = Field(min_length=1)
    summary: VariantConfig = Field(
        default_factory=lambda: VariantConfig(
            label="summary_current",
            model="gemini-2.5-flash",
        )
    )
    top_k: int = Field(default=3, ge=1)
    max_retrieved_items: int = Field(default=0, ge=0)
    output: Path | None = None
    max_samples: int = Field(default=0, ge=0)
    judge: bool = False
    judge_model: str = "gemini-2.5-pro"
    sleep_seconds: float = Field(default=1.0, ge=0)


# ---------------------------------------------------------------------------
# Extraction & dedup dataset builders
# ---------------------------------------------------------------------------


def _require_one_langfuse_source(model: BaseModel) -> None:
    sources = [
        getattr(model, "session_prefix", None),
        getattr(model, "session_id", None),
        getattr(model, "session_ids", None),
        getattr(model, "batch_results", None),
        getattr(model, "trace_ids", None),
    ]
    provided_count = sum(source not in (None, "", []) for source in sources)
    if provided_count != 1:
        raise ValueError(
            "Exactly one of session_prefix, session_id, session_ids, "
            "batch_results, or trace_ids must be set."
        )


class ExtractionDatasetBuildConfig(BaseModel):
    """Config for freezing extraction spans into a local eval dataset."""

    eval_set_id: str
    session_prefix: str | None = None
    session_id: str | None = None
    session_ids: list[str] | None = None
    batch_results: Path | None = None
    trace_ids: list[str] | None = None
    created_from: str | None = None
    max_games: int = Field(default=5, ge=0)
    max_samples: int = Field(default=40, ge=0)
    seed: int = 0
    output: Path | None = None
    overwrite: bool = False

    @model_validator(mode="after")
    def require_one_source(self) -> "ExtractionDatasetBuildConfig":
        _require_one_langfuse_source(self)
        return self


class DedupDatasetBuildConfig(BaseModel):
    """Config for freezing dedup decision spans into a local eval dataset."""

    eval_set_id: str
    session_prefix: str | None = None
    session_id: str | None = None
    session_ids: list[str] | None = None
    batch_results: Path | None = None
    trace_ids: list[str] | None = None
    created_from: str | None = None
    max_games: int = Field(default=5, ge=0)
    max_samples: int = Field(default=40, ge=0)
    filter_auto: bool = False
    seed: int = 0
    output: Path | None = None
    overwrite: bool = False

    @model_validator(mode="after")
    def require_one_source(self) -> "DedupDatasetBuildConfig":
        _require_one_langfuse_source(self)
        return self


# ---------------------------------------------------------------------------
# Extraction & dedup experiment configs
# ---------------------------------------------------------------------------


class ExtractionExperimentConfig(BaseModel):
    """Config for judging captured extraction cases."""

    dataset: Path
    output: Path | None = None
    max_samples: int = Field(default=0, ge=0)
    judge: bool = True
    judge_model: str = "gemini-2.5-pro"
    sleep_seconds: float = Field(default=1.0, ge=0)


class DedupExperimentConfig(BaseModel):
    """Config for judging captured dedup decision cases."""

    dataset: Path
    output: Path | None = None
    max_samples: int = Field(default=0, ge=0)
    judge: bool = True
    judge_model: str = "gemini-2.5-pro"
    filter_auto: bool = False
    sleep_seconds: float = Field(default=1.0, ge=0)

"""Pydantic models for evaluation config files.

These models describe runnable experiment and dataset-builder configs. Runtime
result schemas live in ``evaluation.core.schemas``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class _DescribedConfig(BaseModel):
    """Base for file-loaded experiment/build configs.

    Adds an optional human note. It is ignored by the runners but embedded
    verbatim into the lineage manifest, so the recorded recipe self-documents
    (a JSON config cannot carry a comment — this field is its stand-in).
    """

    description: str | None = None
    """Free-text note on what this config is for. Humans only; never model-visible."""


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


class DatasetBuildConfig(_DescribedConfig):
    """Config for freezing game traces into a local eval dataset."""

    eval_set_id: str
    session_prefix: str | None = None
    session_id: str | None = None
    session_ids: list[str] | None = None
    batch_results: Path | None = None
    trace_ids: list[str] | None = None
    local_results: Path | None = None
    """run_batch JSONL whose per-game ``eval_cases_path`` sidecars supply the
    cases LOCALLY (no Langfuse read). Preferred source for games run after
    local emission landed; the other five sources fetch from Langfuse."""
    created_from: str | None = None
    max_games: int = Field(default=5, ge=0)
    per_role_per_phase: int = Field(default=1, ge=1)
    max_samples: int = Field(default=40, ge=0)
    seed: int = 0
    action_phases: list[str] | None = None
    """Which action phases are eligible for sampling. None → day-only
    ("day_discussion", "day_vote"). Add "night_action" to include night
    decisions (wolf kill-vote, healer, investigator, SK, vigilante) — in scope
    for Phase B labeling on v5."""
    output: Path | None = None
    overwrite: bool = False

    @model_validator(mode="after")
    def require_one_source(self) -> "DatasetBuildConfig":
        _require_one_case_source(self)
        return self


class PairwiseExperimentConfig(_DescribedConfig):
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


class RetrievalExperimentConfig(_DescribedConfig):
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


class ApplicationExperimentConfig(_DescribedConfig):
    """Config for replaying final discussion/vote actions from frozen cases."""

    dataset: Path
    memory_mode: Literal["captured", "none", "snapshot"] = "captured"
    snapshots: list[MemorySnapshotConfig] | None = None
    top_k: int = Field(default=3, ge=1)
    max_retrieved_items: int = Field(default=0, ge=0)
    output: Path | None = None
    max_samples: int = Field(default=0, ge=0)
    judge: bool = False
    judge_model: str = "gemini-2.5-pro"
    sleep_seconds: float = Field(default=1.0, ge=0)

    @model_validator(mode="after")
    def require_snapshots_for_snapshot_mode(self) -> "ApplicationExperimentConfig":
        if self.memory_mode == "snapshot" and not self.snapshots:
            raise ValueError(
                "snapshots must be provided when memory_mode is 'snapshot'."
            )
        return self


class SummaryExperimentConfig(_DescribedConfig):
    """Config for evaluating situation summaries with a rubric-based judge.

    mode="captured" judges the frozen situations from the EvalCase.
    mode="replay" regenerates situations with the specified variant first.
    """

    dataset: Path
    mode: Literal["captured", "replay"] = "captured"
    variant: VariantConfig | None = None
    output: Path | None = None
    max_samples: int = Field(default=0, ge=0)
    judge: bool = True
    judge_model: str = "gemini-3.1-pro-preview"
    sleep_seconds: float = Field(default=1.0, ge=0)

    @model_validator(mode="after")
    def require_variant_for_replay(self) -> "SummaryExperimentConfig":
        if self.mode == "replay" and not self.variant:
            raise ValueError("variant must be provided when mode is 'replay'.")
        return self


class CapturedEvaluationConfig(_DescribedConfig):
    """Config for judging captured EvalCase rows without replaying any stage."""

    dataset: Path
    output: Path | None = None
    max_samples: int = Field(default=0, ge=0)
    judge_model: str = "gemini-2.5-pro"
    judge_type: Literal["pipeline", "application"] = "pipeline"
    sleep_seconds: float = Field(default=1.0, ge=0)


class E2EExperimentConfig(_DescribedConfig):
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


def _require_one_case_source(model: BaseModel) -> None:
    """Exactly one case source: five Langfuse routes or the local-sidecar route."""
    sources = [
        getattr(model, "session_prefix", None),
        getattr(model, "session_id", None),
        getattr(model, "session_ids", None),
        getattr(model, "batch_results", None),
        getattr(model, "trace_ids", None),
        getattr(model, "local_results", None),
    ]
    provided_count = sum(source not in (None, "", []) for source in sources)
    if provided_count != 1:
        raise ValueError(
            "Exactly one of session_prefix, session_id, session_ids, "
            "batch_results, trace_ids, or local_results must be set."
        )


class ExtractionDatasetBuildConfig(_DescribedConfig):
    """Config for freezing extraction spans into a local eval dataset."""

    eval_set_id: str
    session_prefix: str | None = None
    session_id: str | None = None
    session_ids: list[str] | None = None
    batch_results: Path | None = None
    trace_ids: list[str] | None = None
    local_results: Path | None = None
    """run_batch JSONL whose per-game sidecars supply the cases locally
    (no Langfuse read); see DatasetBuildConfig.local_results."""
    created_from: str | None = None
    max_games: int = Field(default=5, ge=0)
    max_samples: int = Field(default=40, ge=0)
    seed: int = 0
    output: Path | None = None
    overwrite: bool = False

    @model_validator(mode="after")
    def require_one_source(self) -> "ExtractionDatasetBuildConfig":
        _require_one_case_source(self)
        return self


class DedupDatasetBuildConfig(_DescribedConfig):
    """Config for freezing dedup decision spans into a local eval dataset."""

    eval_set_id: str
    session_prefix: str | None = None
    session_id: str | None = None
    session_ids: list[str] | None = None
    batch_results: Path | None = None
    trace_ids: list[str] | None = None
    local_results: Path | None = None
    """run_batch JSONL whose per-game sidecars supply the cases locally
    (no Langfuse read); see DatasetBuildConfig.local_results."""
    created_from: str | None = None
    max_games: int = Field(default=5, ge=0)
    max_samples: int = Field(default=40, ge=0)
    filter_auto: bool = False
    seed: int = 0
    output: Path | None = None
    overwrite: bool = False

    @model_validator(mode="after")
    def require_one_source(self) -> "DedupDatasetBuildConfig":
        _require_one_case_source(self)
        return self


# ---------------------------------------------------------------------------
# Extraction & dedup experiment configs
# ---------------------------------------------------------------------------


class ExtractionExperimentConfig(_DescribedConfig):
    """Config for judging captured extraction cases."""

    dataset: Path
    output: Path | None = None
    max_samples: int = Field(default=0, ge=0)
    judge: bool = True
    judge_model: str = "gemini-2.5-pro"
    sleep_seconds: float = Field(default=1.0, ge=0)


class DedupExperimentConfig(_DescribedConfig):
    """Config for judging captured dedup decision cases."""

    dataset: Path
    output: Path | None = None
    max_samples: int = Field(default=0, ge=0)
    judge: bool = True
    judge_model: str = "gemini-2.5-pro"
    filter_auto: bool = False
    sleep_seconds: float = Field(default=1.0, ge=0)


# ---------------------------------------------------------------------------
# Auto-dedup threshold calibration
# ---------------------------------------------------------------------------


class AutoDedupDatasetBuildConfig(_DescribedConfig):
    """Config for building a dedup threshold calibration dataset.

    Takes extraction JSONL files, builds an in-memory store from ``store_files``,
    then searches each item from ``extraction_files`` against the store.  This
    produces cases across the full similarity spectrum.

    Key experiment axes:
    - **store_files vs extraction_files**: controls cross-model and cross-game overlap.
      Use the same files for both to test within-model dedup; use different models'
      extractions to test cross-model dedup.
    - **top_n**: how many candidates the store returns per query.
    - **min_similarity**: floor for including candidates.  Set to 0 to capture
      the full spectrum including near-zero matches for auto-keep calibration.
    """

    eval_set_id: str
    extraction_files: list[Path] = Field(min_length=1)
    store_files: list[Path] = Field(min_length=1)
    top_n: int = Field(default=5, ge=1)
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    max_samples: int = Field(default=0, ge=0)
    seed: int = 42
    output: Path | None = None
    overwrite: bool = False


class AutoDedupCalibrationConfig(_DescribedConfig):
    """Config for sweeping thresholds against a labeled calibration dataset."""

    dataset: Path
    golden: Path
    cache: Path | None = None
    discard_range: tuple[float, float, float] = (0.80, 1.01, 0.005)
    keep_range: tuple[float, float, float] = (0.50, 0.90, 0.01)
    output: Path | None = None

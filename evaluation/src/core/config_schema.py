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


class _CaseSourceBuildConfig(_DescribedConfig):
    """Shared base for freezing game traces/spans into a local eval dataset.

    Exactly one of the six case sources must be set — five Langfuse routes
    (session/trace selectors) or the local-sidecar route. Subclasses add their
    format-specific sampling fields.
    """

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
    max_samples: int = Field(default=40, ge=0)
    seed: int = 0
    output: Path | None = None
    overwrite: bool = False

    @model_validator(mode="after")
    def _require_one_case_source(self) -> "_CaseSourceBuildConfig":
        sources = [
            self.session_prefix,
            self.session_id,
            self.session_ids,
            self.batch_results,
            self.trace_ids,
            self.local_results,
        ]
        if sum(source not in (None, "", []) for source in sources) != 1:
            raise ValueError(
                "Exactly one of session_prefix, session_id, session_ids, "
                "batch_results, trace_ids, or local_results must be set."
            )
        return self


class DatasetBuildConfig(_CaseSourceBuildConfig):
    """Config for freezing game traces into a local eval dataset."""

    per_role_per_phase: int = Field(default=1, ge=1)
    action_phases: list[str] | None = None
    """Which action phases are eligible for sampling. None → day-only
    ("day_discussion", "day_vote"). Add "night_action" to include night
    decisions (wolf kill-vote, healer, investigator, SK, vigilante) — in scope
    for Phase B labeling on v5."""


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


class TurnEvalConfig(_DescribedConfig):
    """Config for the unified turn eval: optionally replay a stage, then judge.

    Collapses the former captured / application / e2e configs into one shape:
      replay=none    judge the recorded turn as captured
      replay=action  regenerate the final action, then judge
      replay=all     regenerate summary -> retrieval -> action, then judge
    ``judge`` selects the grader independently of depth: application | pipeline | off.
    ``memory_mode`` chooses the action's memory inputs when replay=action.
    """

    dataset: Path
    replay: Literal["none", "action", "all"] = "none"
    memory_mode: Literal["captured", "none", "snapshot"] = "captured"
    snapshots: list[MemorySnapshotConfig] | None = None
    summary: VariantConfig | None = None
    top_k: int = Field(default=3, ge=1)
    max_retrieved_items: int = Field(default=0, ge=0)
    output: Path | None = None
    max_samples: int = Field(default=0, ge=0)
    judge: Literal["off", "application", "pipeline"] = "application"
    judge_model: str = "gemini-2.5-pro"
    sleep_seconds: float = Field(default=1.0, ge=0)

    @model_validator(mode="after")
    def _check_replay_requirements(self) -> "TurnEvalConfig":
        if self.replay == "all":
            if not self.snapshots:
                raise ValueError("snapshots must be provided when replay='all'.")
            if self.summary is None:
                raise ValueError("summary must be provided when replay='all'.")
        if (
            self.replay == "action"
            and self.memory_mode == "snapshot"
            and not self.snapshots
        ):
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


# ---------------------------------------------------------------------------
# Extraction & dedup dataset builders
# ---------------------------------------------------------------------------


class ExtractionDatasetBuildConfig(_CaseSourceBuildConfig):
    """Config for freezing extraction spans into a local eval dataset."""


class DedupDatasetBuildConfig(_CaseSourceBuildConfig):
    """Config for freezing dedup decision spans into a local eval dataset."""

    filter_auto: bool = False


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


_TAGGER_MODE_DEFAULT_GLOB = {
    "accuracy": "batch_results/v6ab_baseline.jsonl batch_results/v6ab_skboth.jsonl",
    "skill": "evidence/v7_final/v2_full/gen*_on.jsonl",
    "deleak": "evidence/v7_final/v2_full/gen*_on.jsonl",
}


class TaggerEvalConfig(_DescribedConfig):
    """Config for the discussion-tagger validation runner (``cli_runner/discussion_tagger_eval.py``).

    One runner, three modes — each reproducing a frozen ``evidence/v7_final`` apparatus:
    ``accuracy`` (per-field tag correctness vs a deterministic self-claim detector + faction
    skews), ``skill`` (game-level wolf/SK partial ``r(disc_verdict, won | deluck[, verbosity])``
    leak/confound guard), ``deleak`` (2x2 outcome-withholding ablation isolating the outcome-leak
    from the mechanical silent-player effect). See the docstrings there and in
    ``evidence/evaluation/discussion_tagger/`` for the methodology.
    """

    mode: Literal["accuracy", "skill", "deleak"]
    batch_glob: str | None = None
    """Whitespace-joined repo-root glob(s) for the batch/game-run JSONL. None → the mode default
    (``accuracy`` reads the v6ab dumps; ``skill``/``deleak`` read the v2 gen*_on dumps)."""
    max_games_per_source: int | None = None
    """``accuracy`` only: keep the first N records of EACH matched file (None → 4, the original cap)."""
    n_games: int | None = None
    """``deleak`` only: stride-subsample to this many games (None → 6, the original count)."""
    tags_cache_dir: Path | None = None
    """Provenance-slugged tag cache (keyed by game_id/slug/outcome/speakers/version). None → tag
    fresh every run. A played game's tags are immutable, so caching makes a re-run within a paid
    revalidation campaign free."""
    tagger_version: str = "v2"
    strict: bool = False
    """Re-raise the first per-day tag failure instead of degrading to empty tags (see ``tag_game``)."""
    pro_model: str | None = "gemini-3.1-flash-lite"
    """Cost guard: pin ``GOOGLE_GENAI_PRO_MODEL``/``_BACKUP`` before any tagging. None → leave env as-is."""
    output: Path | None = None

    @model_validator(mode="after")
    def _fill_mode_default_glob(self) -> "TaggerEvalConfig":
        if self.batch_glob is None:
            self.batch_glob = _TAGGER_MODE_DEFAULT_GLOB[self.mode]
        return self


class AutoDedupCalibrationConfig(_DescribedConfig):
    """Threshold-sweep recipe for the embedding pre-filter calibration.

    Built from CLI args by ``studies/eval_auto_dedup.py`` (argparse →
    validated config), so the sweep keeps its interactive flags while each run
    has one validated recipe. The runner reports to stdout — it writes no
    artifact, so there is no ``output`` field.
    """

    dataset: Path
    golden: Path
    cache: Path | None = None
    discard_range: tuple[float, float, float] = (0.80, 0.96, 0.01)
    keep_range: tuple[float, float, float] = (0.50, 0.76, 0.01)
    show_decisions: bool = False
    obs_keep_mode: Literal["content", "field"] = "content"
    dims: int | None = None
    task_type: str | None = None
    embedding_model: str | None = None

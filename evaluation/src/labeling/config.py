"""Pydantic config models for the labeling pipeline.

Follows the same pattern as ``evaluation.core.config_schema`` — JSON-serializable
configs that fully describe a labeling run.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ModelSpec(BaseModel):
    """A single labeling model with its rate-limit and generation settings."""

    name: str
    rpm_limit: float | None = None
    thinking_level: Literal["minimal", "low", "medium", "high"] | None = None
    temperature: float = 0.0
    max_retries: int = 3


class VotingConfig(BaseModel):
    """How to resolve multi-model disagreements."""

    tiebreaker: str | None = None
    min_for_majority: int = Field(default=2, ge=1)

    @model_validator(mode="after")
    def tiebreaker_consistency(self) -> "VotingConfig":
        return self


class ExportConfig(BaseModel):
    """Config for exporting items for manual labeling."""

    candidates_path: Path
    output_dir: Path
    batch_size: int = Field(default=5, ge=1)
    cases: list[int] | None = None


class LabelingPipelineConfig(BaseModel):
    """End-to-end config for the assembled pipeline (`pipeline.py`, one entry point).

    Drives LABEL (engine panel) → optional EXPORT off-ramp (→ human) → CONSOLIDATE
    (vote across model + human voters → consensus + ties). All stage artifacts
    derive from ``output_dir``; ``models`` may be empty for a pure copy-paste run.
    """

    candidates_path: Path
    adapter: str
    adapter_kwargs: dict = Field(default_factory=dict)
    models: list[ModelSpec] = Field(default_factory=list)
    voting: VotingConfig = Field(default_factory=VotingConfig)
    output_dir: Path
    manual_sources: list[Path] = Field(default_factory=list)
    checkpoint_every: int = Field(default=1, ge=1)
    export_batch_size: int = Field(default=5, ge=1)
    export_instructions: str = ""

    @property
    def scores_path(self) -> Path:
        return self.output_dir / "model_scores.json"

    @property
    def consensus_path(self) -> Path:
        return self.output_dir / "consensus_golden.json"

    @property
    def ties_path(self) -> Path:
        return self.output_dir / "ties.json"

    @property
    def export_dir(self) -> Path:
        return self.output_dir / "export_batches"

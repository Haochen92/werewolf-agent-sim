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


class ManualSourceConfig(BaseModel):
    """Describes human-labeled data to merge with model labels."""

    name: str
    path: Path
    format: Literal["batch_dir", "single_file"] = "single_file"
    key_style: Literal["full", "truncated"] = "full"
    key_truncation_length: int = 12


class LabelingRunConfig(BaseModel):
    """Top-level config for a multi-model labeling run."""

    models: list[ModelSpec] = Field(min_length=1)
    voting: VotingConfig = Field(default_factory=VotingConfig)
    checkpoint_every: int = Field(default=1, ge=1)
    max_retries: int = Field(default=3, ge=1)
    output_dir: Path
    candidates_path: Path


class MergeConfig(BaseModel):
    """Config for merging multiple label sources into consensus."""

    model_label_files: dict[str, Path]
    manual_sources: list[ManualSourceConfig] = Field(default_factory=list)
    candidates_path: Path
    voting: VotingConfig = Field(default_factory=VotingConfig)
    output_path: Path
    dry_run: bool = False


class ExportConfig(BaseModel):
    """Config for exporting items for manual labeling."""

    candidates_path: Path
    output_dir: Path
    batch_size: int = Field(default=5, ge=1)
    cases: list[int] | None = None

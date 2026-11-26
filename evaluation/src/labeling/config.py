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
    keys: list[str] | None = None
    """Export only items whose key is in this list (e.g. the keys of an anchor draw).
    None exports every item that passes the ``cases`` filter."""
    write_answers_template: bool = False
    """Also write ``answers_template.json`` to ``output_dir``: one row per exported item, in export
    order, with the label left null, ready for the person to fill in."""


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


class CalibrationConfig(BaseModel):
    """Config for `pipeline calibrate`: compare model label sources with a person's labels."""

    human_labels_path: Path
    """The person's label file, in the simple-golden shape
    ``{"labeler": "owner", "labels": [{"case_index": 0, "key": "...", "label": "...", "note": ""}]}``."""
    model_label_paths: list[Path]
    """Label files holding the model sources, in either shape `pipeline.load_voters` reads (engine
    output or simple golden). Each model, or each simple-golden ``labeler``, becomes one source."""
    model_sources: list[str]
    """Which sources from ``model_label_paths`` to calibrate, by name (e.g. ``["echo_gate"]``);
    each gets its own report."""
    stratum_path: Path | None = None
    """Optional JSON object mapping each sampled item key to its stratum, e.g.
    ``{"g3:12": "flagged", "g3:14": "unflagged"}``. When given, its keys are also the set of keys
    the person must have labelled. None puts every item in one stratum."""
    allowed_labels: list[str] | None = None
    """The labels the person may use, e.g. ``["accuse", "none"]``. None accepts any non-empty label."""
    positive_label: str | None = None
    """For binary labels, the label counted as "positive" in the directional-bias test
    (e.g. ``"accuse"``). None skips the bias test."""
    min_agreement: float = Field(default=0.80, ge=0.0, le=1.0)
    """The acceptance gate's lowest allowed agreement rate between the model and the person."""
    min_ci_lower: float = Field(default=0.75, ge=0.0, le=1.0)
    """The acceptance gate's lowest allowed lower bound of the agreement rate's 95% interval."""
    bias_alpha: float = Field(default=0.05, gt=0.0, lt=1.0)
    """A directional-bias p-value below this fails the acceptance gate."""
    output_dir: Path
    """Where the markdown and JSON calibration reports are written."""

    @model_validator(mode="after")
    def positive_label_is_allowed(self) -> "CalibrationConfig":
        """Reject a positive label that is not one of the allowed labels.

        Returns:
            The config unchanged. Raises ValueError when both fields are set and disagree.
        """
        if (
            self.positive_label is not None
            and self.allowed_labels is not None
            and self.positive_label not in self.allowed_labels
        ):
            raise ValueError(
                f"positive_label {self.positive_label!r} is not in allowed_labels {self.allowed_labels}"
            )
        return self

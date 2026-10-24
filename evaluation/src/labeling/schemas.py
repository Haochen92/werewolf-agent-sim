"""Types for the labelling pipeline's calibration half: the anchor draw and the calibration report.

The functions that produce these live in ``anchor.py`` and ``calibration.py``. Every report type
is JSON-serialisable (``model_dump_json``) so a report can be written next to its markdown summary.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class StratifiedSample(BaseModel):
    """The result of a seeded stratified draw of item keys for a person to label."""

    drawn_keys: list[str]
    """The drawn item keys, sorted by key (not grouped by stratum, so the order gives no hint)."""
    drawn_count_by_stratum: dict[str, int]
    """How many keys were drawn from each stratum, e.g. ``{"flagged": 20, "unflagged": 20}``."""
    short_stratum_notes: list[str] = Field(default_factory=list)
    """One note per stratum that had fewer candidates than asked for, e.g.
    ``"flagged: asked for 20, only 12 candidates"``. Empty when every stratum was full."""


class LabelRow(BaseModel):
    """How one label was used by the person and by the model, with the model's precision/recall."""

    label: str
    """The label these counts are for, e.g. ``"accuse"``."""
    human_count: int
    """Items the person gave this label."""
    model_count: int
    """Items the model gave this label."""
    both_count: int
    """Items both the person and the model gave this label."""
    precision: float | None
    """Of the items the model gave this label, the share the person also did. None if the model
    never used it."""
    recall: float | None
    """Of the items the person gave this label, the share the model also did. None if the person
    never used it."""


class StratumAgreement(BaseModel):
    """The agreement rate within one stratum of the sample."""

    stratum: str
    """The stratum name, e.g. ``"flagged"``."""
    items: int
    """Items in this stratum that both the person and the model labelled."""
    agreeing_items: int
    """Of those, the items where the two labels match."""
    agreement_rate: float
    """``agreeing_items / items``."""


class Disagreement(BaseModel):
    """One item where the model's label differs from the person's."""

    key: str
    """The item key."""
    stratum: str
    """The item's stratum."""
    human_label: str
    """The person's label (taken as the truth)."""
    model_label: str
    """The model's label."""


class BiasTest(BaseModel):
    """An exact McNemar test of whether the model calls "positive" more or less often than the person."""

    positive_label: str
    """The label counted as positive, e.g. ``"accuse"``."""
    human_positive_rate: float
    """Share of compared items the person labelled positive."""
    model_positive_rate: float
    """Share of compared items the model labelled positive."""
    human_only_positive: int
    """Items the person called positive and the model did not (the model's misses)."""
    model_only_positive: int
    """Items the model called positive and the person did not (the model's false alarms)."""
    p_value: float
    """Two-sided exact McNemar p-value; small means the misses and false alarms are lopsided."""


class GateCondition(BaseModel):
    """One condition of the acceptance gate and whether it held."""

    name: str
    """What is checked, e.g. ``"agreement"``, ``"ci_lower_bound"``, ``"no_directional_bias"``."""
    threshold: float
    """The configured threshold the observed value is compared with."""
    observed: float | None
    """The observed value (a rate, or the bias test's p-value). None when the check did not apply."""
    status: Literal["passed", "failed", "not_applicable"]
    """The outcome; ``not_applicable`` (e.g. a bias test on non-binary labels) never fails the gate."""
    explanation: str
    """One plain sentence saying what was compared, e.g. ``"agreement 0.85 >= 0.80"``."""


class CalibrationReport(BaseModel):
    """How well one model label source agrees with a person's labels, and whether it passes the gate."""

    model_source: str
    """The model source compared, e.g. ``"echo_gate"``."""
    items: int
    """Items both the person and the model labelled (the compared items)."""
    agreeing_items: int
    """Compared items where the model's label equals the person's."""
    agreement_rate: float
    """``agreeing_items / items``."""
    agreement_ci: tuple[float, float]
    """The agreement rate's exact (Clopper–Pearson) 95% interval, ``(low, high)``."""
    cohens_kappa: float
    """Agreement beyond chance: 1.0 perfect, 0.0 chance level, below 0 worse than chance."""
    confusion: dict[str, dict[str, int]]
    """Person label → model label → item count, including zero cells, e.g.
    ``{"accuse": {"accuse": 9, "none": 1}, "none": {"accuse": 2, "none": 8}}``."""
    label_rows: list[LabelRow]
    """One row per label seen or allowed."""
    stratum_rows: list[StratumAgreement]
    """The agreement rate per stratum, sorted by stratum name."""
    disagreements: list[Disagreement]
    """Every compared item where the labels differ, sorted by key."""
    bias_test: BiasTest | None
    """The directional-bias test, or None when it was skipped."""
    bias_test_skipped_reason: str | None
    """Why the bias test was skipped (e.g. labels not binary); None when it ran."""
    keys_without_model_label: list[str]
    """Keys the person labelled but the model did not; they are left out of every number above."""
    gate: list[GateCondition]
    """The acceptance gate's conditions, in a fixed order."""
    accepted: bool
    """True when no gate condition failed."""

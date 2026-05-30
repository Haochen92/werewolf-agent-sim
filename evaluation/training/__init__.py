"""Composable cross-encoder training pipeline.

A small, pluggable harness mirroring ``evaluation.labeling``:

    config   — TrainConfig: hyperparameters + run identity
    base     — TrainingAdapter ABC: the per-task contract (data, model, metrics)
    engine   — the shared training loop (runs inside the Modal GPU container)
    evaluator— standalone metric evaluators (ranking, binary); CPU inference,
               reused for in-loop final metrics and for evaluating a saved model
    manifest — reproducibility record written next to each saved model
    runner/  — modal_runner: the GPU training backend (training is Modal-only)
    adapters/— concrete tasks: reranker (and dedup), with a name→class registry

Training runs on Modal; local machines are inference-only. See ``README.md`` for
the worked example of adding a new adapter.
"""
from __future__ import annotations

from .base import DatasetBundle, TrainingAdapter
from .config import TrainConfig
from .evaluator import (
    BinaryClassificationEvaluator,
    Evaluator,
    RankingEvaluator,
    evaluate_saved,
)

__all__ = [
    "TrainConfig",
    "TrainingAdapter",
    "DatasetBundle",
    "Evaluator",
    "RankingEvaluator",
    "BinaryClassificationEvaluator",
    "evaluate_saved",
]

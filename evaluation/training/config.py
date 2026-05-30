"""Config model for a cross-encoder training run.

Follows the same pattern as ``evaluation.labeling.config`` — a JSON-serializable
object that fully describes one training run and is recorded verbatim in the run
manifest for reproducibility.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class TrainConfig(BaseModel):
    """Hyperparameters and run identity for one cross-encoder training run.

    The adapter supplies *what* to train (data, model, metrics); this supplies
    *how* (epochs, batch size, lr) and *where* (run_name, output_dir, volume).
    """

    base_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    epochs: int = Field(default=10, ge=1)
    batch_size: int = Field(default=16, ge=1)
    lr: float = 2e-5
    warmup_ratio: float = Field(default=0.1, ge=0.0)
    seed: int = 42
    bf16: bool = True

    run_name: str = "run1"
    output_dir: Path
    save_total_limit: int = Field(default=2, ge=1)
    logging_steps: int = Field(default=5, ge=1)

    # When set, overrides the adapter's default checkpoint-selection metric.
    metric_for_best_model: str | None = None

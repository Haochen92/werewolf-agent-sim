"""The shared training loop.

Backend-agnostic and pure-compute: given an adapter + config (+ optionally the
already-read raw payload), it loads the base model, builds datasets, runs the
sentence-transformers ``CrossEncoderTrainer``, selects the best checkpoint,
computes final metrics via the adapter's evaluator, and saves the model.

The same function runs in-process (``runner.local``) or inside a Modal container
(``runner.modal``). It never touches Modal or argument parsing itself.
"""
from __future__ import annotations

import os
from typing import Any

from .base import DatasetBundle, TrainingAdapter
from .config import TrainConfig


def _extract_loss_curve(trainer) -> dict[str, Any]:
    curve: dict[str, Any] = {"train_loss": [], "eval_loss": []}
    for entry in trainer.state.log_history:
        if "loss" in entry and "epoch" in entry:
            curve["train_loss"].append({"epoch": entry["epoch"], "loss": entry["loss"]})
        if "eval_loss" in entry and "epoch" in entry:
            curve["eval_loss"].append({"epoch": entry["epoch"], "loss": entry["eval_loss"]})
    return curve


def _build_args(adapter: TrainingAdapter, config: TrainConfig):
    import torch
    from sentence_transformers.cross_encoder.training_args import (
        CrossEncoderTrainingArguments,
    )

    # bf16 needs a GPU; on CPU (local smoke tests) fall back transparently.
    cuda = torch.cuda.is_available()
    return CrossEncoderTrainingArguments(
        output_dir=str(config.output_dir),
        num_train_epochs=config.epochs,
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=config.batch_size,
        learning_rate=config.lr,
        warmup_ratio=config.warmup_ratio,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=config.save_total_limit,
        load_best_model_at_end=True,
        metric_for_best_model=config.metric_for_best_model or adapter.metric_for_best_model,
        logging_steps=config.logging_steps,
        bf16=config.bf16 and cuda,
        use_cpu=not cuda,
        seed=config.seed,
    )


def train(adapter: TrainingAdapter, config: TrainConfig,
          raw: dict | None = None) -> dict[str, Any]:
    """Run one training job. Returns ``{metrics, loss_curve, stats, output_dir}``."""
    from sentence_transformers.cross_encoder.trainer import CrossEncoderTrainer

    os.environ.setdefault("WANDB_DISABLED", "true")

    if raw is None:
        raw = adapter.read_raw()

    model = adapter.load_model(config.base_model)
    bundle: DatasetBundle = adapter.build_datasets(raw)

    print(f"[{adapter.name}] base={config.base_model} epochs={config.epochs} "
          f"train={len(bundle.train)} eval={len(bundle.eval)}")

    trainer = CrossEncoderTrainer(
        model=model,
        args=_build_args(adapter, config),
        train_dataset=bundle.train,
        eval_dataset=bundle.eval,
        evaluator=adapter.trainer_evaluator(bundle),
    )
    trainer.train()

    metrics = adapter.evaluator.evaluate(model, bundle.eval_raw)
    print(f"[{adapter.name}] final metrics: {metrics}")

    model.save_pretrained(str(config.output_dir))

    return {
        "metrics": metrics,
        "loss_curve": _extract_loss_curve(trainer),
        "stats": bundle.stats,
        "output_dir": str(config.output_dir),
    }

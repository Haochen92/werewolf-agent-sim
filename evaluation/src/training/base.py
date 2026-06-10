"""Base adapter protocol for cross-encoder training tasks.

Each task (reranker relevance regression, dedup binary classification, …)
subclasses ``TrainingAdapter`` to plug domain logic into the generic engine.
The engine owns the training loop, checkpoint selection, saving, and manifest
writing; the adapter owns data, model, the in-loop evaluator, and final metrics.

Data flow is split so the same adapter runs locally or inside a Modal container:

    read_raw()        # disk reads — runs on the LAUNCHING side, returns JSON
       │  (payload shipped to the execution backend verbatim)
    build_datasets()  # pure transform — runs WHEREVER training executes
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from .evaluator import Evaluator


@dataclass
class DatasetBundle:
    """HF Datasets ready for the trainer, plus raw eval records for metrics."""

    train: Any  # datasets.Dataset
    eval: Any  # datasets.Dataset
    eval_raw: list[dict]  # raw eval records, consumed by the standalone Evaluator
    stats: dict[str, Any] = field(default_factory=dict)


class TrainingAdapter(ABC):
    """Plug a cross-encoder training task into the shared engine.

    Minimal contract: implement ``read_raw``, ``build_datasets``, and
    ``evaluator``. Override ``load_model`` / ``trainer_evaluator`` /
    ``metric_for_best_model`` only when the defaults don't fit.
    """

    #: Stable identifier; the runner registry maps this back to the class so a
    #: Modal container can reconstruct the adapter by name.
    name: str = "base"

    @abstractmethod
    def read_raw(self) -> dict:
        """Read training data from disk into a JSON-serializable payload.

        Runs on the launching side (local), so it may touch the repo. The
        payload is shipped to the execution backend (local or Modal) verbatim,
        so it must contain everything ``build_datasets`` needs.
        """

    @abstractmethod
    def build_datasets(self, raw: dict) -> DatasetBundle:
        """Transform the raw payload into a :class:`DatasetBundle`. Pure — runs
        wherever training executes (local process or Modal container)."""

    @property
    @abstractmethod
    def evaluator(self) -> Evaluator:
        """Standalone metrics evaluator (reused for final in-loop eval and for
        evaluating a saved model on a held-out split)."""

    # --- overridable defaults -------------------------------------------------

    def load_model(self, base_model: str):
        """Load the base model. Default: sentence-transformers ``CrossEncoder``."""
        from sentence_transformers.cross_encoder import CrossEncoder

        return CrossEncoder(base_model)

    def trainer_evaluator(self, bundle: DatasetBundle):
        """Optional sentence-transformers evaluator passed to the trainer (e.g.
        ``CEBinaryClassificationEvaluator``). Return ``None`` to select
        checkpoints on eval loss alone."""
        return None

    @property
    def metric_for_best_model(self) -> str:
        """HF Trainer metric key used to pick the best checkpoint."""
        return "eval_loss"

    def held_out_records(self, split: str = "test") -> list[dict]:
        """Raw records for standalone evaluation of a saved model (CPU).

        Default: the in-training eval split. Override when a task keeps a
        separate held-out set (the reranker has train/val/test files)."""
        return self.read_raw()["eval"]

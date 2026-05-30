"""Dedup adapter — binary Keep/Discard cross-encoder.

Trains a CE that scores (memory_A, memory_B) → duplicate? to supplement the
embedding cosine thresholds in the auto-dedup pre-filter. Consumes the
dedup-matched pairs (``evidence/fine_tuning/embedding/pairs_dedup.jsonl``) and
applies the same deterministic 90/10 stratified split as the original training
script, so runs are reproducible.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from evaluation.core.settings import REPO_ROOT

from ..base import DatasetBundle, TrainingAdapter
from ..evaluator import BinaryClassificationEvaluator, Evaluator

_PAIRS_PATH = REPO_ROOT / "evidence" / "fine_tuning" / "embedding" / "pairs_dedup.jsonl"


class DedupAdapter(TrainingAdapter):
    name = "dedup"

    def __init__(self, pairs_path: Path = _PAIRS_PATH, seed: int = 42):
        self.pairs_path = Path(pairs_path)
        self.seed = seed

    def read_raw(self) -> dict:
        rows = [json.loads(l) for l in self.pairs_path.read_text().splitlines() if l.strip()]
        rng = random.Random(self.seed)
        pos = [r for r in rows if float(r["label"]) == 1.0]
        neg = [r for r in rows if float(r["label"]) == 0.0]
        rng.shuffle(pos)
        rng.shuffle(neg)
        ps, ns = int(len(pos) * 0.9), int(len(neg) * 0.9)
        train = pos[:ps] + neg[:ns]
        eval_ = pos[ps:] + neg[ns:]
        rng.shuffle(train)
        rng.shuffle(eval_)
        return {"train": train, "eval": eval_}

    def build_datasets(self, raw: dict) -> DatasetBundle:
        from datasets import Dataset

        def to_ds(rows: list[dict]) -> Dataset:
            return Dataset.from_dict({
                "sentence1": [r["sentence1"] for r in rows],
                "sentence2": [r["sentence2"] for r in rows],
                "label": [float(r["label"]) for r in rows],
            })

        train_raw, eval_raw = raw["train"], raw["eval"]
        stats = {
            "n_train": len(train_raw),
            "n_eval": len(eval_raw),
            "n_pos_eval": sum(1 for r in eval_raw if float(r["label"]) == 1.0),
            "n_neg_eval": sum(1 for r in eval_raw if float(r["label"]) == 0.0),
        }
        return DatasetBundle(train=to_ds(train_raw), eval=to_ds(eval_raw),
                             eval_raw=eval_raw, stats=stats)

    def trainer_evaluator(self, bundle: DatasetBundle):
        from sentence_transformers.cross_encoder.evaluation import (
            CEBinaryClassificationEvaluator,
        )

        return CEBinaryClassificationEvaluator(
            sentence_pairs=[(r["sentence1"], r["sentence2"]) for r in bundle.eval_raw],
            labels=[int(float(r["label"])) for r in bundle.eval_raw],
            name="val",
        )

    @property
    def metric_for_best_model(self) -> str:
        return "val_average_precision"

    @property
    def evaluator(self) -> Evaluator:
        return BinaryClassificationEvaluator()

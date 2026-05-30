"""Reranker adapter — relevance-regression cross-encoder.

Trains a CE that scores (situation_query, memory_text) → graded relevance
(0.0 / 0.25 / 1.0) to replace the LLM reranking call in retrieval. Consumes the
stratified split produced by the reranker evidence scripts
(``training_data/reranker_{train,val,test}.jsonl``).
"""
from __future__ import annotations

import json
from pathlib import Path

from evaluation.core.settings import REPO_ROOT

from ..base import DatasetBundle, TrainingAdapter
from ..evaluator import Evaluator, RankingEvaluator

_DATA_DIR = (
    REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker" / "training_data"
)


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_split(name: str, data_dir: Path = _DATA_DIR) -> list[dict]:
    """Load one split (``train`` / ``val`` / ``test``) as raw records."""
    return _read_jsonl(data_dir / f"reranker_{name}.jsonl")


class RerankerAdapter(TrainingAdapter):
    name = "reranker"

    def __init__(self, data_dir: Path = _DATA_DIR):
        self.data_dir = Path(data_dir)

    def read_raw(self) -> dict:
        split_path = self.data_dir / "reranker_split.json"
        manifest = json.loads(split_path.read_text()) if split_path.exists() else None
        return {
            "train": load_split("train", self.data_dir),
            "eval": load_split("val", self.data_dir),
            "manifest": manifest,
        }

    def build_datasets(self, raw: dict) -> DatasetBundle:
        from datasets import Dataset

        train_raw, eval_raw = raw["train"], raw["eval"]

        def to_ds(rows: list[dict]) -> Dataset:
            return Dataset.from_dict({
                "sentence1": [r["sentence1"] for r in rows],
                "sentence2": [r["sentence2"] for r in rows],
                "label": [float(r["label"]) for r in rows],
            })

        train_cases = sorted({r["case_index"] for r in train_raw})
        eval_cases = sorted({r["case_index"] for r in eval_raw})
        overlap = set(train_cases) & set(eval_cases)
        if overlap:
            raise ValueError(f"train/eval case overlap: {sorted(overlap)}")

        stats = {
            "n_train": len(train_raw),
            "n_eval": len(eval_raw),
            "train_cases": train_cases,
            "eval_cases": eval_cases,
        }
        return DatasetBundle(train=to_ds(train_raw), eval=to_ds(eval_raw),
                             eval_raw=eval_raw, stats=stats)

    def held_out_records(self, split: str = "test") -> list[dict]:
        return load_split(split, self.data_dir)

    @property
    def evaluator(self) -> Evaluator:
        return RankingEvaluator()

"""Standalone metric evaluators for trained cross-encoders.

An ``Evaluator`` scores a loaded model against eval records and returns a metrics
dict. It is deliberately decoupled from the adapter so the *same* code runs in
two places:

* in-loop — the engine calls it once after training to report final metrics;
* standalone — ``evaluate_saved`` loads a saved model and runs it on a held-out
  split (this replaces the old ``eval_*_modal.py`` scripts; cross-encoder
  inference is cheap enough to run on CPU).
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any


class Evaluator(ABC):
    """Scores ``eval_raw`` with ``model`` and returns a metrics dict."""

    @abstractmethod
    def evaluate(self, model, eval_raw: list[dict]) -> dict[str, Any]:
        ...


def _dcg(rels: list[int], k: int) -> float:
    return sum((2 ** rels[i] - 1) / math.log2(i + 2) for i in range(min(k, len(rels))))


def ndcg_at_k(rels: list[int], k: int) -> float:
    ideal = _dcg(sorted(rels, reverse=True), k)
    return _dcg(rels, k) / ideal if ideal > 0 else 1.0


def _bootstrap_ci(values: list[float], n_boot: int = 10000, ci: float = 0.95,
                  seed: int = 42) -> tuple[float, float]:
    import numpy as np

    rng = np.random.RandomState(seed)
    arr = np.array(values)
    if len(arr) == 0:
        return (0.0, 0.0)
    means = np.array([arr[rng.randint(0, len(arr), len(arr))].mean() for _ in range(n_boot)])
    lo = float(np.percentile(means, (1 - ci) / 2 * 100))
    hi = float(np.percentile(means, (1 + ci) / 2 * 100))
    return (lo, hi)


class RankingEvaluator(Evaluator):
    """Per-case NDCG@k (+ MSE, Pearson r) for graded-relevance reranking.

    Groups eval pairs by ``case_index``, ranks each case by predicted score, and
    averages NDCG across cases. Mirrors the metrics from the old
    ``eval_reranker_modal.py``.
    """

    def __init__(self, ks: tuple[int, ...] = (3, 5, 10),
                 label_to_rel: dict[float, int] | None = None):
        self.ks = ks
        self.label_to_rel = label_to_rel or {0.0: 0, 0.25: 1, 1.0: 2}

    def evaluate(self, model, eval_raw: list[dict]) -> dict[str, Any]:
        import numpy as np

        pairs = [(r["sentence1"], r["sentence2"]) for r in eval_raw]
        preds = model.predict(pairs)

        case_items: dict[Any, list[dict]] = defaultdict(list)
        for r, pred in zip(eval_raw, preds):
            case_items[r["case_index"]].append({"label": r["label"], "pred": float(pred)})

        per_k: dict[int, list[float]] = {k: [] for k in self.ks}
        for case_idx in sorted(case_items):
            items = sorted(case_items[case_idx], key=lambda x: x["pred"], reverse=True)
            rels = [self.label_to_rel.get(it["label"], round(it["label"] * 2)) for it in items]
            for k in self.ks:
                per_k[k].append(ndcg_at_k(rels, k))

        true = np.array([r["label"] for r in eval_raw], dtype=float)
        pred = np.array(preds, dtype=float)
        mse = float(np.mean((true - pred) ** 2))
        corr = float(np.corrcoef(true, pred)[0, 1]) if len(true) > 1 else 0.0

        out: dict[str, Any] = {"n_cases": len(case_items), "n_pairs": len(eval_raw)}
        for k in self.ks:
            out[f"ndcg{k}"] = float(np.mean(per_k[k])) if per_k[k] else 0.0
        out["ndcg5_ci95"] = _bootstrap_ci(per_k[5]) if 5 in per_k else None
        out["mse"] = mse
        out["pearson_r"] = corr
        return out


class BinaryClassificationEvaluator(Evaluator):
    """Average precision / best-F1 / accuracy for binary (Keep/Discard) CE.

    Mirrors the discrimination metrics tracked for the dedup pre-filter
    cross-encoder.
    """

    def __init__(self, positive_label: float = 1.0):
        self.positive_label = positive_label

    def evaluate(self, model, eval_raw: list[dict]) -> dict[str, Any]:
        import numpy as np

        pairs = [(r["sentence1"], r["sentence2"]) for r in eval_raw]
        scores = np.array(model.predict(pairs), dtype=float)
        labels = np.array([1 if float(r["label"]) == self.positive_label else 0
                           for r in eval_raw])

        order = np.argsort(-scores)
        s_labels = labels[order]
        tp = np.cumsum(s_labels)
        fp = np.cumsum(1 - s_labels)
        precision = tp / np.maximum(tp + fp, 1)
        recall = tp / max(labels.sum(), 1)
        ap = float(np.sum((recall - np.concatenate([[0], recall[:-1]])) * precision))

        f1s = 2 * precision * recall / np.maximum(precision + recall, 1e-9)
        best = int(np.argmax(f1s)) if len(f1s) else 0
        thr = float(scores[order][best]) if len(scores) else 0.0
        acc = float(((scores >= thr).astype(int) == labels).mean()) if len(scores) else 0.0

        return {
            "n_pairs": len(eval_raw),
            "average_precision": ap,
            "best_f1": float(f1s[best]) if len(f1s) else 0.0,
            "precision_at_best_f1": float(precision[best]) if len(precision) else 0.0,
            "recall_at_best_f1": float(recall[best]) if len(recall) else 0.0,
            "threshold_at_best_f1": thr,
            "accuracy_at_best_f1": acc,
        }


def evaluate_saved(model_path: str, eval_raw: list[dict], evaluator: Evaluator) -> dict[str, Any]:
    """Load a saved cross-encoder and evaluate it on ``eval_raw`` (CPU-friendly)."""
    from sentence_transformers.cross_encoder import CrossEncoder

    model = CrossEncoder(model_path)
    return evaluator.evaluate(model, eval_raw)

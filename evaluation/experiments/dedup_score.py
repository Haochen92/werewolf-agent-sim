"""Score dedup decisions against golden labels (deterministic, no LLM).

Compares LLM dedup decisions from a dataset JSONL against human-annotated
golden labels.  Supports both legacy (A/B/C/D) and current (D/M/K) decision
schemes — auto-detects which scheme the dataset uses.

Usage::

    poetry run python -m evaluation.experiments.dedup_score \
        --dataset eval_sets/dedup_v2_sampled.jsonl \
        --golden eval_sets/dedup_v2_golden_labels.json

    poetry run python -m evaluation.experiments.dedup_score \
        --dataset eval_sets/dedup_replay_gemini_20260525.jsonl \
        --golden eval_sets/dedup_v2_golden_labels.json \
        --output eval_results/dedup_score_gemini.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from evaluation.data.datasets import read_dedup_dataset

LEGACY_TO_CURRENT_OBS = {
    "A": "D",  # DISCARD → DISCARD
    "B": "M",  # REPLACE → MERGE
    "C": "K",  # DIFFERENTIATE → KEEP
}

LEGACY_TO_CURRENT_STRAT = {
    "A": "D",  # DISCARD → DISCARD
    "B": "D",  # REPLACE → DISCARD (strategy points have no merge)
    "C": "K",  # DIFFERENTIATE → KEEP
}

CURRENT_LABELS = {"D", "M", "K"}
LEGACY_LABELS = {"A", "B", "C"}
LABEL_ORDER = ["D", "M", "K"]


def _detect_scheme(decisions: list[str]) -> str:
    has_legacy = any(d in LEGACY_LABELS for d in decisions)
    has_current_only = any(d in ("M", "K") for d in decisions)
    if has_legacy and not has_current_only:
        return "legacy"
    if has_current_only and not has_legacy:
        return "current"
    if has_legacy:
        return "legacy"
    return "current"


def _normalize_decision(
    decision: str, scheme: str, item_type: str
) -> str:
    if scheme == "legacy":
        mapping = (
            LEGACY_TO_CURRENT_OBS
            if item_type == "observation"
            else LEGACY_TO_CURRENT_STRAT
        )
        if decision in mapping:
            return mapping[decision]
        if decision == "D":
            return "K"
    return decision


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


@dataclass
class CaseResult:
    case_index: int
    item_type: str
    golden_label: str
    predicted_label: str
    also_acceptable: str | None
    strict_correct: bool
    lenient_correct: bool
    notes: str | None


@dataclass
class ScoreReport:
    dataset_path: str
    golden_path: str
    scheme: str
    total: int
    strict_correct: int
    lenient_correct: int
    per_label: dict[str, dict[str, float]] = field(default_factory=dict)
    confusion: dict[str, dict[str, int]] = field(default_factory=dict)
    mismatches: list[CaseResult] = field(default_factory=list)
    per_type_accuracy: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def strict_accuracy(self) -> float:
        return self.strict_correct / self.total if self.total else 0.0

    @property
    def lenient_accuracy(self) -> float:
        return self.lenient_correct / self.total if self.total else 0.0


def _compute_per_label(
    results: list[CaseResult],
) -> dict[str, dict[str, float]]:
    unambiguous = [r for r in results if "/" not in r.golden_label]
    metrics: dict[str, dict[str, float]] = {}
    for label in LABEL_ORDER:
        tp = sum(
            1
            for r in unambiguous
            if r.golden_label == label and r.predicted_label == label
        )
        fp = sum(
            1
            for r in unambiguous
            if r.golden_label != label and r.predicted_label == label
        )
        fn = sum(
            1
            for r in unambiguous
            if r.golden_label == label and r.predicted_label != label
        )
        support = tp + fn
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
    return metrics


def _compute_confusion(
    results: list[CaseResult],
) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = {}
    for gold in LABEL_ORDER:
        matrix[gold] = {}
        for pred in LABEL_ORDER:
            matrix[gold][pred] = sum(
                1
                for r in results
                if r.golden_label == gold and r.predicted_label == pred
            )
    return matrix


def _compute_per_type(
    results: list[CaseResult],
) -> dict[str, dict[str, int]]:
    types: set[str] = {r.item_type for r in results}
    per_type: dict[str, dict[str, int]] = {}
    for t in sorted(types):
        subset = [r for r in results if r.item_type == t]
        per_type[t] = {
            "total": len(subset),
            "strict_correct": sum(1 for r in subset if r.strict_correct),
            "lenient_correct": sum(1 for r in subset if r.lenient_correct),
        }
    return per_type


def _match_golden(
    records: list,
    golden_data: dict,
) -> dict[int, dict]:
    """Match records to golden labels by case_id, falling back to index."""
    labels_by_id = {
        g["case_id"]: g
        for g in golden_data["labels"]
        if g.get("case_id")
    }
    labels_by_index = {g["case_index"]: g for g in golden_data["labels"]}

    matched: dict[int, dict] = {}
    used_golden: set[int] = set()
    for idx, record in enumerate(records):
        cid = getattr(record, "case_id", None)
        golden = labels_by_id.get(cid) if cid else None
        if golden is None:
            golden = labels_by_index.get(idx)
        if golden is not None:
            gi = golden["case_index"]
            if gi not in used_golden:
                matched[idx] = golden
                used_golden.add(gi)
    return matched


def _check_correct(
    predicted: str, golden_label: str, also_acceptable: str | None
) -> tuple[bool, bool]:
    """Return (strict_correct, lenient_correct)."""
    if "/" in golden_label:
        acceptable = set(golden_label.split("/"))
        strict = predicted in acceptable
        return strict, strict
    strict = predicted == golden_label
    lenient = strict or (
        also_acceptable is not None and predicted == also_acceptable
    )
    return strict, lenient


def score(
    dataset_path: Path,
    golden_path: Path,
) -> ScoreReport:
    records = read_dedup_dataset(dataset_path)
    with golden_path.open(encoding="utf-8") as f:
        golden_data = json.load(f)

    matched = _match_golden(records, golden_data)

    decisions = [r.dedup_case.decision for r in records]
    scheme = _detect_scheme(decisions)

    results: list[CaseResult] = []
    for idx, record in enumerate(records):
        golden = matched.get(idx)
        if golden is None:
            continue

        predicted = _normalize_decision(
            record.dedup_case.decision, scheme, golden["item_type"]
        )
        golden_label = golden["golden_label"]
        also_acceptable = golden.get("also_acceptable")

        strict_correct, lenient_correct = _check_correct(
            predicted, golden_label, also_acceptable
        )

        result = CaseResult(
            case_index=golden.get("case_index", idx),
            item_type=golden["item_type"],
            golden_label=golden_label,
            predicted_label=predicted,
            also_acceptable=also_acceptable,
            strict_correct=strict_correct,
            lenient_correct=lenient_correct,
            notes=golden.get("notes"),
        )
        results.append(result)

    mismatches = [r for r in results if not r.strict_correct]

    report = ScoreReport(
        dataset_path=str(dataset_path),
        golden_path=str(golden_path),
        scheme=scheme,
        total=len(results),
        strict_correct=sum(1 for r in results if r.strict_correct),
        lenient_correct=sum(1 for r in results if r.lenient_correct),
        per_label=_compute_per_label(results),
        confusion=_compute_confusion(results),
        mismatches=mismatches,
        per_type_accuracy=_compute_per_type(results),
    )
    return report


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------


def print_report(report: ScoreReport) -> None:
    print(f"\nDedup Golden-Label Scoring")
    print("=" * 60)
    print(f"Dataset:  {report.dataset_path}")
    print(f"Golden:   {report.golden_path}")
    print(f"Scheme:   {report.scheme}")
    print(f"Cases:    {report.total}")

    print(f"\nACCURACY")
    print("-" * 30)
    print(
        f"Strict:   {report.strict_correct}/{report.total} "
        f"({report.strict_accuracy:.1%})"
    )
    print(
        f"Lenient:  {report.lenient_correct}/{report.total} "
        f"({report.lenient_accuracy:.1%})"
    )

    for item_type, counts in report.per_type_accuracy.items():
        total = counts["total"]
        strict = counts["strict_correct"]
        lenient = counts["lenient_correct"]
        print(
            f"  {item_type:16s} strict={strict}/{total} "
            f"({strict/total:.1%})  "
            f"lenient={lenient}/{total} ({lenient/total:.1%})"
        )

    print(f"\nPER-LABEL METRICS")
    print("-" * 50)
    print(f"{'Label':>5s}  {'Prec':>6s}  {'Rec':>6s}  {'F1':>6s}  {'Support':>7s}")
    for label in LABEL_ORDER:
        m = report.per_label[label]
        print(
            f"{label:>5s}  {m['precision']:6.2f}  {m['recall']:6.2f}  "
            f"{m['f1']:6.2f}  {m['support']:7.0f}"
        )

    print(f"\nCONFUSION MATRIX (rows=golden, cols=predicted)")
    print("-" * 40)
    header = "       " + "  ".join(f"pred_{l:1s}" for l in LABEL_ORDER)
    print(header)
    for gold in LABEL_ORDER:
        row = f"gold_{gold}  " + "  ".join(
            f"{report.confusion[gold][pred]:6d}" for pred in LABEL_ORDER
        )
        print(row)

    if report.mismatches:
        print(f"\nMISMATCHES ({len(report.mismatches)})")
        print("-" * 70)
        print(
            f"{'Case':>4s}  {'Type':16s}  {'Golden':>6s}  "
            f"{'Pred':>6s}  {'Alt':>4s}  Notes"
        )
        for m in report.mismatches:
            alt = m.also_acceptable or ""
            lenient_tag = " *" if m.lenient_correct else ""
            notes = (m.notes or "")[:50]
            print(
                f"{m.case_index:4d}  {m.item_type:16s}  "
                f"{m.golden_label:>6s}  {m.predicted_label:>6s}  "
                f"{alt:>4s}  {notes}{lenient_tag}"
            )
        if any(m.lenient_correct for m in report.mismatches):
            print("  (* = lenient-correct via also_acceptable)")


def save_report(report: ScoreReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "scored_at": datetime.now().isoformat(),
        "dataset_path": report.dataset_path,
        "golden_path": report.golden_path,
        "scheme": report.scheme,
        "total": report.total,
        "strict_correct": report.strict_correct,
        "lenient_correct": report.lenient_correct,
        "strict_accuracy": round(report.strict_accuracy, 4),
        "lenient_accuracy": round(report.lenient_accuracy, 4),
        "per_type_accuracy": report.per_type_accuracy,
        "per_label": {
            label: {k: round(v, 4) for k, v in metrics.items()}
            for label, metrics in report.per_label.items()
        },
        "confusion_matrix": report.confusion,
        "mismatches": [
            {
                "case_index": m.case_index,
                "item_type": m.item_type,
                "golden_label": m.golden_label,
                "predicted_label": m.predicted_label,
                "also_acceptable": m.also_acceptable,
                "lenient_correct": m.lenient_correct,
                "notes": m.notes,
            }
            for m in report.mismatches
        ],
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"\nSaved report to {path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score dedup decisions against golden labels."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Dedup dataset JSONL (original or replayed).",
    )
    parser.add_argument(
        "--golden",
        type=Path,
        required=True,
        help="Golden labels JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Save structured results to this JSON file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = score(args.dataset, args.golden)
    print_report(report)
    if args.output:
        save_report(report, args.output)


if __name__ == "__main__":
    main()

"""Score and compare all dedup replay files against golden labels.

Finds all replay JSONL files matching a pattern and produces a side-by-side
comparison table with overall accuracy and per-label recall.

Usage::

    poetry run python scripts/dedup_model_comparison.py
    poetry run python scripts/dedup_model_comparison.py --pattern "eval_sets/dedup_v2_replay_*v7*.jsonl"
    poetry run python scripts/dedup_model_comparison.py --golden eval_sets/dedup_v2_golden_labels.json
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

from evaluation.experiments.dedup_score import score, LABEL_ORDER


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare dedup replay files against golden labels."
    )
    parser.add_argument(
        "--pattern",
        default="eval_sets/dedup_v2_replay_*.jsonl",
        help="Glob pattern for replay JSONL files.",
    )
    parser.add_argument(
        "--golden",
        type=Path,
        default=Path("eval_sets/dedup_v2_golden_labels.json"),
        help="Golden labels JSON file.",
    )
    parser.add_argument(
        "--min-cases",
        type=int,
        default=50,
        help="Skip runs with fewer matched cases than this.",
    )
    args = parser.parse_args()

    files = sorted(glob.glob(args.pattern))
    if not files:
        print(f"No files match pattern: {args.pattern}")
        return

    reports = []
    for f in files:
        name = (
            Path(f)
            .stem.replace("dedup_v2_replay_", "")
        )
        report = score(Path(f), args.golden)
        if report.total >= args.min_cases:
            reports.append((name, report))

    if not reports:
        print("No replay files had enough matched cases.")
        return

    labels_to_show = []
    for label in LABEL_ORDER:
        if any(
            label in r.per_label and r.per_label[label]["support"] > 0
            for _, r in reports
        ):
            labels_to_show.append(label)

    header = f"{'Version':<40s} {'N':>3s} {'Accuracy':>8s}"
    for label in labels_to_show:
        header += f"  {label + ' recall':>10s}"
    print(header)
    print("-" * len(header))

    for name, report in reports:
        row = f"{name:<40s} {report.total:>3d} {report.strict_accuracy:>7.1%}"
        for label in labels_to_show:
            m = report.per_label.get(label, {})
            recall = m.get("recall", 0.0)
            support = int(m.get("support", 0))
            row += f"  {recall:>5.0%} ({support:>2d})"
        print(row)


if __name__ == "__main__":
    main()

"""Score captured DedupCase records using an LLM judge."""

from __future__ import annotations

import argparse
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from evaluation.core.config_schema import DedupExperimentConfig
from evaluation.core.io import write_jsonl
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.data.datasets import read_dedup_dataset
from evaluation.judges.dedup import run_dedup_judge

load_project_env()

DECISION_LABELS = {
    # Current per-extraction decisions
    "D": "DISCARD",
    "M": "MERGE",
    "K": "KEEP",
    # Legacy decisions (for evaluating older spans)
    "A": "DISCARD",
    "B": "REPLACE",
    "C": "DIFFERENTIATE",
}


def output_path(requested: Path | None) -> Path:
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"dedup_eval_{timestamp}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Judge captured dedup decision cases."
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def read_config(path: Path) -> DedupExperimentConfig:
    return DedupExperimentConfig.model_validate_json(
        path.read_text(encoding="utf-8")
    )


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    records = read_dedup_dataset(config.dataset)

    if config.filter_auto:
        records = [r for r in records if not r.auto]

    if config.max_samples:
        records = records[: config.max_samples]
    out_path = output_path(config.output)

    print(
        f"Loaded {len(records)} dedup records from {config.dataset}", flush=True
    )
    print(f"Judge model={config.judge_model}", flush=True)
    print(f"Writing results to {out_path}", flush=True)

    written = 0
    decision_counts: Counter[str] = Counter()
    score_totals: dict[str, float] = {}
    fabrication_count = 0

    for index, record in enumerate(records, 1):
        case = record.dedup_case
        decision_label = DECISION_LABELS.get(case.decision, case.decision)
        decision_counts[decision_label] += 1
        print(
            f"[{index}/{len(records)}] {record.case_id} "
            f"{case.item_type} {case.perspective}/{case.action_phase} "
            f"decision={decision_label} auto={case.auto}",
            flush=True,
        )

        scores = None
        if config.judge:
            scores = run_dedup_judge(case, model=config.judge_model)

        result_record = {
            "eval_set_id": record.eval_set_id,
            "case_id": record.case_id,
            "trace_id": record.trace_id,
            "observation_id": record.observation_id,
            "span_name": record.span_name,
            "game_id": case.game_id,
            "item_type": case.item_type,
            "perspective": case.perspective,
            "action_phase": case.action_phase,
            "decision": case.decision,
            "decision_label": decision_label,
            "auto": case.auto,
            "candidate_count": len(case.candidates),
            "source_dataset": str(config.dataset),
            "judge_scores": scores.model_dump(mode="json") if scores else None,
            "judge_model": config.judge_model,
        }
        write_jsonl(out_path, result_record)
        written += 1

        if scores:
            print(
                f"  Scores: correctness={scores.decision_correctness} "
                f"merge={scores.merge_quality} "
                f"preservation={scores.information_preservation} "
                f"fabrication={scores.fabrication_detected}",
                flush=True,
            )
            for dim in (
                "decision_correctness",
                "merge_quality",
                "information_preservation",
            ):
                score_totals[dim] = score_totals.get(dim, 0) + getattr(
                    scores, dim
                )
            if scores.fabrication_detected:
                fabrication_count += 1

        time.sleep(config.sleep_seconds)

    print(f"\nDone. Wrote {written} records to {out_path}", flush=True)
    if decision_counts:
        print("Decision distribution:", flush=True)
        for label, count in decision_counts.most_common():
            print(f"  {label}: {count}", flush=True)
    if score_totals and written:
        print("Averages:", flush=True)
        for dim, total in score_totals.items():
            print(f"  {dim}: {total / written:.2f}", flush=True)
        print(
            f"Fabrication rate: {fabrication_count}/{written} "
            f"({fabrication_count / written:.1%})",
            flush=True,
        )


if __name__ == "__main__":
    main()

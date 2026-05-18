from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from evaluation.components import (
    run_situation_summary_variant,
)
from evaluation.core.io import write_jsonl
from evaluation.data.datasets import EvalDatasetRecord, read_eval_dataset
from evaluation.analysis.pairwise import (
    cost_savings_pct,
    map_judge_winner,
    ordered_outputs,
    quality_delta,
    summarize_pairwise_results,
)
from evaluation.core.schemas import PairwiseExperimentConfig
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.judges.pairwise_summary import run_pairwise_summary_judge


load_project_env()


def read_experiment_config(path: Path) -> PairwiseExperimentConfig:
    try:
        return PairwiseExperimentConfig.model_validate_json(
            path.read_text(encoding="utf-8")
        )
    except ValidationError as exc:
        raise ValueError(f"Invalid pairwise config {path}: {exc}") from exc


def result_output_path(requested: Path | None, experiment_id: str) -> Path:
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"{experiment_id}_{timestamp}.jsonl"


def run_pairwise_case(
    record: EvalDatasetRecord,
    config: PairwiseExperimentConfig,
    index: int,
) -> dict[str, Any]:
    """Run one local fixture through both variants and the pairwise judge."""
    if config.component != "situation_summary":
        raise ValueError(f"Unsupported component: {config.component}")

    baseline = run_situation_summary_variant(record.eval_case, config.baseline)
    candidate = run_situation_summary_variant(record.eval_case, config.candidate)

    swapped, output_a_name, output_a, output_b_name, output_b = ordered_outputs(
        baseline=baseline,
        candidate=candidate,
        index=index,
        alternate_order=config.alternate_order,
    )

    judge_scores, judge_meta = run_pairwise_summary_judge(
        record,
        output_a,
        output_b,
        config.judge,
    )
    winner = map_judge_winner(
        judge_scores.winner,
        output_a_name=output_a_name,
        output_b_name=output_b_name,
    )

    return {
        "experiment_id": config.experiment_id,
        "component": config.component,
        "eval_set_id": record.eval_set_id,
        "case_id": record.case_id,
        "trace_id": record.trace_id,
        "observation_id": record.observation_id,
        "span_name": record.span_name,
        "player_id": record.player_id,
        "player_role": record.player_role,
        "day": record.day,
        "round": record.round,
        "action_type": record.action_type,
        "baseline": baseline,
        "candidate": candidate,
        "judge": {
            **judge_meta,
            "winner_raw": judge_scores.winner,
            "winner": winner,
            "confidence": judge_scores.confidence,
            "brief_reasoning": judge_scores.brief_reasoning,
            "presentation": {
                "swapped": swapped,
                "output_a": output_a_name,
                "output_b": output_b_name,
            },
        },
        "deltas": {
            "cost_savings_pct": cost_savings_pct(baseline, candidate),
            "quality_delta": quality_delta(winner),
        },
    }


def summarize_results(results: list[dict[str, Any]]) -> None:
    summarize_pairwise_results(results, title="SUMMARY PAIRWISE")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run config-driven pairwise component comparisons."
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.0,
        help="Delay after each case to avoid provider rate limits.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = read_experiment_config(args.config)
    records = read_eval_dataset(args.dataset)
    if args.max_cases:
        records = records[: args.max_cases]
    out_path = result_output_path(args.output, config.experiment_id)

    print(f"Loaded {len(records)} records from {args.dataset}")
    print(f"Experiment: {config.experiment_id} ({config.component})")
    print(f"Writing results to {out_path}")

    results: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        print(
            f"[{index + 1}/{len(records)}] {record.case_id} "
            f"role={record.player_role} action={record.action_type}",
            flush=True,
        )
        try:
            result = run_pairwise_case(record, config, index)
        except Exception as exc:
            result = {
                "experiment_id": config.experiment_id,
                "component": config.component,
                "eval_set_id": record.eval_set_id,
                "case_id": record.case_id,
                "trace_id": record.trace_id,
                "observation_id": record.observation_id,
                "error": str(exc),
            }
            print(f"  Error: {exc}", flush=True)
        else:
            print(
                f"  Winner={result['judge']['winner']} "
                f"confidence={result['judge']['confidence']} "
                f"savings={result['deltas']['cost_savings_pct']}",
                flush=True,
            )
        write_jsonl(out_path, result)
        results.append(result)
        if args.sleep_seconds:
            time.sleep(args.sleep_seconds)

    summarize_results(results)


if __name__ == "__main__":
    main()

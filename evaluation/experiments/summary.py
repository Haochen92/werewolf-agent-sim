"""Pairwise comparison of situation-summary variants.

For each frozen ``EvalCase``, this experiment runs a baseline and candidate
summary model/prompt, asks a judge to choose the better retrieval query, and
records quality and cost deltas.
"""

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
from evaluation.core.config_schema import PairwiseExperimentConfig
from evaluation.core.io import write_jsonl
from evaluation.data.datasets import EvalDatasetRecord, read_eval_dataset
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.judges.pairwise_summary import run_pairwise_summary_judge


load_project_env()


def read_experiment_config(path: Path) -> PairwiseExperimentConfig:
    """Load the pairwise summary experiment JSON config."""
    try:
        return PairwiseExperimentConfig.model_validate_json(
            path.read_text(encoding="utf-8")
        )
    except ValidationError as exc:
        raise ValueError(f"Invalid pairwise config {path}: {exc}") from exc


def result_output_path(requested: Path | None, experiment_id: str) -> Path:
    """Return the requested output path or a timestamped default."""
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"{experiment_id}_{timestamp}.jsonl"


def ordered_outputs(
    *,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    index: int,
    alternate_order: bool,
) -> tuple[bool, str, dict[str, Any], str, dict[str, Any]]:
    """Return A/B presentation order, alternating to reduce position bias."""
    swapped = bool(alternate_order and index % 2 == 1)
    if swapped:
        return swapped, "candidate", candidate, "baseline", baseline
    return swapped, "baseline", baseline, "candidate", candidate


def map_judge_winner(
    winner: str,
    *,
    output_a_name: str,
    output_b_name: str,
) -> str:
    """Map the judge's A/B/tie answer back to baseline/candidate/tie."""
    if winner == "tie":
        return "tie"
    return output_a_name if winner == "a" else output_b_name


def quality_delta(winner: str) -> int:
    """Represent candidate quality as +1, baseline quality as -1, tie as 0."""
    if winner == "candidate":
        return 1
    if winner == "baseline":
        return -1
    return 0


def cost_savings_pct(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> float | None:
    """Return candidate cost savings relative to baseline, when cost is known."""
    baseline_cost = baseline.get("cost", {}).get("estimated_cost_usd")
    candidate_cost = candidate.get("cost", {}).get("estimated_cost_usd")
    if baseline_cost in (None, 0) or candidate_cost is None:
        return None
    return 1 - (candidate_cost / baseline_cost)


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
        "action_phase": record.action_phase,
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
    """Print a compact pairwise summary for completed comparisons."""
    completed = [result for result in results if "judge" in result]
    if not completed:
        print("No completed pairwise comparisons.")
        return

    winner_counts = {"baseline": 0, "candidate": 0, "tie": 0}
    savings: list[float] = []
    for result in completed:
        winner = result["judge"]["winner"]
        winner_counts[winner] = winner_counts.get(winner, 0) + 1
        savings_pct = result.get("deltas", {}).get("cost_savings_pct")
        if savings_pct is not None:
            savings.append(savings_pct)

    print("\nSUMMARY PAIRWISE")
    print(f"  Completed: {len(completed)}")
    print(
        "  Winners: "
        f"baseline={winner_counts['baseline']}, "
        f"candidate={winner_counts['candidate']}, "
        f"tie={winner_counts['tie']}"
    )
    if savings:
        avg = sum(savings) / len(savings)
        print(f"  Avg candidate cost savings: {avg:.1%}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run config-driven pairwise component comparisons."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=None,
        help="Override dataset path from config.",
    )
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
    dataset_path = args.dataset or config.dataset
    if dataset_path is None:
        raise ValueError("Dataset path is required in config or via --dataset.")
    max_cases = args.max_cases or config.max_cases
    sleep_seconds = args.sleep_seconds or config.sleep_seconds
    output = args.output or config.output

    records = read_eval_dataset(dataset_path)
    if max_cases:
        records = records[:max_cases]
    out_path = result_output_path(output, config.experiment_id)

    print(f"Loaded {len(records)} records from {dataset_path}")
    print(f"Experiment: {config.experiment_id} ({config.component})")
    print(f"Writing results to {out_path}")

    results: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        print(
            f"[{index + 1}/{len(records)}] {record.case_id} "
            f"role={record.player_role} action={record.action_phase}",
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
        if sleep_seconds:
            time.sleep(sleep_seconds)

    summarize_results(results)


if __name__ == "__main__":
    main()

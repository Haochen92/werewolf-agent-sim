from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from Agents.formatters import format_day_channel
from evaluation.components import (
    make_google_llm,
    run_situation_summary_variant,
)
from evaluation.costs import estimate_cost_from_usage_metadata
from evaluation.datasets import EvalDatasetRecord, read_eval_dataset
from evaluation.formatters import (
    format_eval_private_context,
    format_eval_situations,
)
from evaluation.prompts import (
    PAIRWISE_SUMMARY_SYSTEM_PROMPT,
    PAIRWISE_SUMMARY_USER_PROMPT,
)
from evaluation.schemas import (
    JudgeConfig,
    PairwiseExperimentConfig,
    PairwiseJudgeScores,
)
from evaluation.settings import REPO_ROOT, load_project_env


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


def write_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, sort_keys=True, default=str) + "\n")


def judge_input_for_summary(
    record: EvalDatasetRecord,
    output_a: dict[str, Any],
    output_b: dict[str, Any],
) -> dict[str, Any]:
    case = record.eval_case
    return {
        "player_id": case.player_id,
        "player_role": case.player_role,
        "day": case.day,
        "round": case.round,
        "action_type": case.action_type,
        "day_channel_excerpt": format_day_channel(case.visible_discussion),
        "private_context": format_eval_private_context(case.private_context),
        "output_a_label": output_a["label"],
        "output_b_label": output_b["label"],
        "output_a": format_eval_situations(output_a["situations"]),
        "output_b": format_eval_situations(output_b["situations"]),
    }


def run_pairwise_summary_judge(
    record: EvalDatasetRecord,
    output_a: dict[str, Any],
    output_b: dict[str, Any],
    judge_config: JudgeConfig,
) -> tuple[PairwiseJudgeScores, dict[str, Any]]:
    """Compare two situation-summary outputs and return judge score plus cost."""
    prompt_input = judge_input_for_summary(record, output_a, output_b)
    user_prompt = PAIRWISE_SUMMARY_USER_PROMPT.format(**prompt_input)
    llm = make_google_llm(judge_config)
    chain = llm.with_structured_output(PairwiseJudgeScores, include_raw=True)

    started = time.perf_counter()
    result_bundle = chain.invoke(
        [
            {"role": "system", "content": PAIRWISE_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )
    latency_ms = round((time.perf_counter() - started) * 1000)
    if result_bundle.get("parsing_error"):
        raise ValueError(
            f"Structured pairwise judge parsing failed: "
            f"{result_bundle['parsing_error']}"
        )
    result = result_bundle["parsed"]
    raw_message = result_bundle.get("raw")

    input_text = (
        PAIRWISE_SUMMARY_SYSTEM_PROMPT
        + "\n\n"
        + user_prompt
        + "\n\nSTRUCTURED OUTPUT SCHEMA:\n"
        + json.dumps(PairwiseJudgeScores.model_json_schema(), sort_keys=True)
    )
    output_text = json.dumps(result.model_dump(mode="json"), sort_keys=True)
    cost = estimate_cost_from_usage_metadata(
        judge_config.model,
        getattr(raw_message, "usage_metadata", None),
        fallback_input_text=input_text,
        fallback_output_text=output_text,
    )
    return result, {
        "model": judge_config.model,
        "prompt_id": judge_config.prompt_id,
        "latency_ms": latency_ms,
        "cost": cost.model_dump(mode="json"),
    }


def map_judge_winner(
    winner: str,
    output_a_name: str,
    output_b_name: str,
) -> str:
    if winner == "tie":
        return "tie"
    return output_a_name if winner == "a" else output_b_name


def cost_savings_pct(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> float | None:
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

    swapped = bool(config.alternate_order and index % 2 == 1)
    if swapped:
        output_a_name, output_a = "candidate", candidate
        output_b_name, output_b = "baseline", baseline
    else:
        output_a_name, output_a = "baseline", baseline
        output_b_name, output_b = "candidate", candidate

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
            "quality_delta": (
                1 if winner == "candidate" else -1 if winner == "baseline" else 0
            ),
        },
    }


def summarize_results(results: list[dict[str, Any]]) -> None:
    completed = [result for result in results if "judge" in result]
    if not completed:
        print("No completed pairwise comparisons.")
        return

    winner_counts = {"baseline": 0, "candidate": 0, "tie": 0}
    savings: list[float] = []
    for result in completed:
        winner = result["judge"]["winner"]
        winner_counts[winner] = winner_counts.get(winner, 0) + 1
        savings_pct = result["deltas"].get("cost_savings_pct")
        if savings_pct is not None:
            savings.append(savings_pct)

    print("\nPAIRWISE SUMMARY")
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

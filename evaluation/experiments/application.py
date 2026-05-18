from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from Agents.formatters import format_agent_action
from Agents.schemas.evaluation import EvalCase
from evaluation.components.application import (
    application_case_for_judge,
    run_application_action,
)
from evaluation.core.io import write_jsonl
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.data.datasets import read_eval_dataset
from evaluation.judges.application import (
    DEFAULT_APPLICATION_JUDGE_MODEL,
    run_application_judge,
)


load_project_env()

DEFAULT_JUDGE_MODEL = DEFAULT_APPLICATION_JUDGE_MODEL


def output_path(requested: Path | None) -> Path:
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"application_eval_{timestamp}.jsonl"


def memory_inputs_for_mode(case: EvalCase, mode: str) -> tuple[list[Any], list[Any]]:
    if mode == "captured":
        return case.retrieved_observations, case.retrieved_strategy_points
    if mode == "none":
        return [], []
    raise ValueError(f"Unsupported memory mode: {mode}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay the action/application stage from frozen EvalCase rows."
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--memory-mode",
        choices=("captured", "none"),
        default="captured",
        help="Use captured retrieved memories or clear memory inputs.",
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--judge", action="store_true")
    parser.add_argument("--model", default=DEFAULT_JUDGE_MODEL)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    args = parser.parse_args()
    if args.max_samples < 0:
        parser.error("--max-samples must be 0 or greater")
    return args


def main() -> None:
    args = parse_args()
    records = read_eval_dataset(args.dataset)
    if args.max_samples:
        records = records[: args.max_samples]
    out_path = output_path(args.output)

    print(f"Loaded {len(records)} EvalCase records from {args.dataset}", flush=True)
    print(f"Application memory mode={args.memory_mode}", flush=True)
    print(f"Writing replay results to {out_path}", flush=True)

    written = 0
    for index, record in enumerate(records, 1):
        case = record.eval_case
        retrieved_observations, strategy_points = memory_inputs_for_mode(
            case,
            args.memory_mode,
        )
        print(
            f"[{index}/{len(records)}] {record.case_id} "
            f"role={case.player_role} action={case.action_type}",
            flush=True,
        )
        try:
            result, agent_message, agent_vote, updated_strategy = run_application_action(
                case,
                retrieved_observations=retrieved_observations,
                strategy_points=strategy_points,
            )
            judged_case = application_case_for_judge(
                case,
                agent_message=agent_message,
                agent_vote=agent_vote,
                updated_strategy=updated_strategy,
            )
        except Exception as exc:
            replay_record = {
                "eval_set_id": record.eval_set_id,
                "case_id": record.case_id,
                "error": str(exc),
            }
            print(f"  Error: {exc}", flush=True)
        else:
            scores = run_application_judge(judged_case, model=args.model) if args.judge else None
            replay_record = {
                "eval_set_id": record.eval_set_id,
                "case_id": record.case_id,
                "trace_id": record.trace_id,
                "observation_id": record.observation_id,
                "span_name": record.span_name,
                "role": case.player_role,
                "day": case.day,
                "round": case.round,
                "action_type": case.action_type,
                "memory_mode": args.memory_mode,
                "retrieved_observation_count": len(retrieved_observations),
                "retrieved_strategy_point_count": len(strategy_points),
                "action_result": result,
                "agent_decision": format_agent_action(
                    case.action_type,
                    message=agent_message,
                    vote=agent_vote,
                ),
                "updated_strategy": updated_strategy,
                "application_scores": (
                    scores.model_dump(mode="json") if scores else None
                ),
                "judge_model": args.model if args.judge else None,
            }
            if scores:
                print(
                    f"  Scores: action={scores.action_quality} "
                    f"application={scores.strategy_application}",
                    flush=True,
                )
            if args.judge:
                time.sleep(args.sleep_seconds)

        write_jsonl(out_path, replay_record)
        written += 1

    print(f"Done. Wrote {written} records to {out_path}", flush=True)


if __name__ == "__main__":
    main()

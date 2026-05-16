from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from evaluation.settings import REPO_ROOT, load_project_env

load_project_env()

from evaluation.judge import (  # noqa: E402
    DEFAULT_JUDGE_MODEL,
    run_judge,
)
from evaluation.langfuse_client import (  # noqa: E402
    EVAL_VERSION,
    fetch_eval_cases,
    fetch_trace_ids_for_session_id,
    fetch_trace_ids_for_session_ids,
    fetch_trace_ids_for_session_prefix,
    flush_langfuse,
    push_judge_scores,
    read_session_ids_from_batch_results,
)
from evaluation.sampling import (  # noqa: E402
    print_sample_plan,
    sample_cases,
)
from Agents.schemas.evaluation import EvalCase  # noqa: E402
from evaluation.schemas import EvalResult  # noqa: E402


def resolve_trace_ids(args: argparse.Namespace) -> list[str]:
    if args.trace_ids:
        return args.trace_ids
    if args.session_id:
        print(f"Fetching traces for session ID: {args.session_id}")
        return fetch_trace_ids_for_session_id(args.session_id)
    if args.session_ids:
        print(f"Fetching traces for {len(args.session_ids)} exact session IDs.")
        return fetch_trace_ids_for_session_ids(args.session_ids)
    if args.batch_results:
        session_ids = read_session_ids_from_batch_results(args.batch_results)
        print(
            f"Fetching traces for {len(session_ids)} session IDs from "
            f"{args.batch_results}"
        )
        return fetch_trace_ids_for_session_ids(session_ids)

    print(
        f"Fetching traces for session prefix: {args.session_prefix} "
        "(prefix mode scans Langfuse sessions first)."
    )
    return fetch_trace_ids_for_session_prefix(args.session_prefix)


def write_result_record(path: Path, record: BaseModel) -> None:
    """Append a single evaluation result as JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record.model_dump(mode="json"), sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval relevance via LLM-as-judge."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--session-prefix",
        help="Evaluate all traces whose session_id starts with this prefix.",
    )
    group.add_argument("--session-id", help="Evaluate one exact Langfuse session ID.")
    group.add_argument(
        "--session-ids",
        nargs="+",
        help="Evaluate one or more exact Langfuse session IDs.",
    )
    group.add_argument(
        "--batch-results",
        type=Path,
        help="Read exact session IDs from a scripts/run_batch.py JSONL output file.",
    )
    group.add_argument("--trace-ids", nargs="+", help="Evaluate specific trace IDs.")
    parser.add_argument(
        "--max-games",
        type=int,
        default=5,
        help="Max games to sample from (default: 5, evenly spaced).",
    )
    parser.add_argument(
        "--per-role-per-phase",
        type=int,
        default=1,
        help=(
            "Samples per role per game phase per action type per game "
            "(default: 1)."
        ),
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=30,
        help=(
            "Hard cap on total judge calls. The cap is applied round-robin "
            "across stratified buckets to preserve diversity. Use 0 for no "
            "cap (default: 30)."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed for deterministic sampling within strata (default: 0).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_JUDGE_MODEL,
        help=f"Judge model name (default: {DEFAULT_JUDGE_MODEL}).",
    )
    parser.add_argument(
        "--model-type",
        default=None,
        help="Metadata label for the judge model family/type. Defaults to --model.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "JSONL output path for per-sample results. "
            "Defaults to eval_results/<timestamp>.jsonl."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be evaluated without calling the judge. This is the default.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Call the judge and write scores to Langfuse.",
    )
    args = parser.parse_args()
    if args.dry_run and args.write:
        parser.error("--dry-run and --write are mutually exclusive")
    if args.per_role_per_phase < 1:
        parser.error("--per-role-per-phase must be at least 1")
    if args.max_samples < 0:
        parser.error("--max-samples must be 0 or greater")
    return args


def results_output_path(requested: Path | None) -> Path:
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"eval_{timestamp}.jsonl"


def summarize_results(results: list[EvalResult], model: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"EVALUATION SUMMARY ({len(results)} samples, model={model})")
    print(f"{'=' * 60}")

    dimensions = ["summary_quality", "retrieval_relevance", "strategy_application"]
    for dimension in dimensions:
        values = [
            getattr(result.scores, dimension)
            for result in results
            if getattr(result.scores, dimension, None) is not None
        ]
        if values:
            avg = sum(values) / len(values)
            print(f"  {dimension}: avg={avg:.2f} (min={min(values)}, max={max(values)})")

    roles = {result.role for result in results if result.role}
    if roles:
        print("\nBy role:")
        for role in sorted(roles):
            role_results = [result for result in results if result.role == role]
            for dimension in dimensions:
                values = [
                    getattr(result.scores, dimension)
                    for result in role_results
                    if getattr(result.scores, dimension, None) is not None
                ]
                if values:
                    avg = sum(values) / len(values)
                    print(f"  {role} - {dimension}: avg={avg:.2f} (n={len(values)})")

    action_types = {result.action_type for result in results if result.action_type}
    if action_types:
        print("\nBy action type:")
        for action_type in sorted(action_types):
            action_results = [
                result for result in results if result.action_type == action_type
            ]
            for dimension in dimensions:
                values = [
                    getattr(result.scores, dimension)
                    for result in action_results
                    if getattr(result.scores, dimension, None) is not None
                ]
                if values:
                    avg = sum(values) / len(values)
                    print(
                        f"  {action_type} - {dimension}: "
                        f"avg={avg:.2f} (n={len(values)})"
                    )


def select_games(trace_ids: list[str], max_games: int) -> list[str]:
    if len(trace_ids) <= max_games:
        return trace_ids
    step = len(trace_ids) / max_games
    return [trace_ids[int(i * step)] for i in range(max_games)]


def fetch_cases_for_games(games_to_sample: list[str]) -> tuple[
    list[EvalCase],
    dict[str, int],
]:
    cases: list[EvalCase] = []
    game_lengths: dict[str, int] = {}

    for trace_id in games_to_sample:
        game_cases = fetch_eval_cases(trace_id)
        cases.extend(game_cases)
        game_lengths[trace_id] = max((case.day for case in game_cases), default=1)

    return cases, game_lengths


def evaluate_samples(
    sampled: list[EvalCase],
    args: argparse.Namespace,
    out_path: Path,
    model_type: str,
) -> list[EvalResult]:
    results: list[EvalResult] = []
    for i, case in enumerate(sampled):
        print(
            f"\n[{i + 1}/{len(sampled)}] Evaluating {case.span_name} "
            f"(role={case.player_role}, day={case.day}, "
            f"action={case.action_type})"
        )

        scores = run_judge(case, model=args.model)
        if not scores:
            print("  Skipping - judge call failed.")
            continue

        print(
            f"  Scores: summary={scores.summary_quality} "
            f"relevance={scores.retrieval_relevance} "
            f"application={scores.strategy_application}"
        )
        print(f"  Reasoning: {scores.brief_reasoning}")

        push_judge_scores(
            case.trace_id,
            case.observation_id,
            scores.model_dump(mode="json"),
            args.model,
            model_type,
        )
        result_record = EvalResult(
            span_name=case.span_name,
            trace_id=case.trace_id,
            observation_id=case.observation_id,
            role=case.player_role,
            day=case.day,
            round=case.round,
            action_type=case.action_type,
            model=args.model,
            model_type=model_type,
            eval_version=EVAL_VERSION,
            sampling_seed=args.seed,
            scores=scores,
        )
        results.append(result_record)
        write_result_record(out_path, result_record)
        time.sleep(1)

    return results


def main() -> None:
    args = parse_args()
    trace_ids = resolve_trace_ids(args)

    if not trace_ids:
        print("No traces found.")
        return

    print(f"Found {len(trace_ids)} traces.")

    games_to_sample = select_games(trace_ids, args.max_games)
    print(f"Sampling from {len(games_to_sample)} games.")

    cases, game_lengths = fetch_cases_for_games(games_to_sample)
    print(f"Found {len(cases)} candidate eval cases across sampled games.")

    sampled = sample_cases(
        cases,
        game_lengths,
        games_to_sample=games_to_sample,
        per_role_per_phase=args.per_role_per_phase,
        max_samples=args.max_samples or None,
        seed=args.seed,
    )
    print(f"Sampled {len(sampled)} spans for evaluation.")

    if args.dry_run or not args.write:
        print_sample_plan(sampled, game_lengths)
        if not args.write:
            print("\nDry run only. Pass --write to call the judge and push scores.")
        return

    model_type = args.model_type or args.model
    out_path = results_output_path(args.output)
    print(f"Judge model: {args.model}")
    print(f"Judge model type: {model_type}")
    print(f"Sampling seed: {args.seed}")
    print(f"Writing per-sample results to: {out_path}")

    results = evaluate_samples(sampled, args, out_path, model_type)
    flush_langfuse()

    if not results:
        print("\nNo evaluations completed.")
        return

    summarize_results(results, args.model)
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()

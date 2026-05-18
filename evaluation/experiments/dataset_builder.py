from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from Agents.schemas.evaluation import EvalCase
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.data.datasets import EvalDatasetRecord, record_from_case, write_eval_dataset
from evaluation.data.langfuse import (
    fetch_eval_cases,
    fetch_trace_ids_for_session_id,
    fetch_trace_ids_for_session_ids,
    fetch_trace_ids_for_session_prefix,
    read_session_ids_from_batch_results,
)
from evaluation.data.sampling import sample_cases


load_project_env()


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

    print(f"Fetching traces for session prefix: {args.session_prefix}")
    return fetch_trace_ids_for_session_prefix(args.session_prefix)


def select_games(trace_ids: list[str], max_games: int) -> list[str]:
    if max_games <= 0 or len(trace_ids) <= max_games:
        return trace_ids
    step = len(trace_ids) / max_games
    return [trace_ids[int(i * step)] for i in range(max_games)]


def fetch_cases_for_games(
    trace_ids: list[str],
) -> tuple[list[EvalCase], dict[str, int]]:
    cases: list[EvalCase] = []
    game_lengths: dict[str, int] = {}
    for trace_id in trace_ids:
        game_cases = fetch_eval_cases(trace_id)
        cases.extend(game_cases)
        game_lengths[trace_id] = max((case.day for case in game_cases), default=1)
    return cases, game_lengths


def build_dataset_records(args: argparse.Namespace) -> list[EvalDatasetRecord]:
    """Fetch Langfuse traces once and freeze sampled EvalCase payloads locally."""
    trace_ids = resolve_trace_ids(args)
    if not trace_ids:
        return []

    games_to_sample = select_games(trace_ids, args.max_games)
    print(f"Found {len(trace_ids)} traces; sampling from {len(games_to_sample)} games.")

    cases, game_lengths = fetch_cases_for_games(games_to_sample)
    print(f"Found {len(cases)} candidate eval cases.")

    sampled = sample_cases(
        cases,
        game_lengths,
        games_to_sample=games_to_sample,
        per_role_per_phase=args.per_role_per_phase,
        max_samples=args.max_samples or None,
        seed=args.seed,
    )
    print(f"Sampled {len(sampled)} cases for local dataset.")

    return [
        record_from_case(
            case,
            eval_set_id=args.eval_set_id,
            created_from=args.created_from,
        )
        for case in sampled
    ]


def default_output_path(eval_set_id: str) -> Path:
    return REPO_ROOT / "eval_sets" / f"{eval_set_id}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a local frozen EvalCase dataset from Langfuse traces."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--session-prefix")
    group.add_argument("--session-id")
    group.add_argument("--session-ids", nargs="+")
    group.add_argument("--batch-results", type=Path)
    group.add_argument("--trace-ids", nargs="+")
    parser.add_argument("--eval-set-id", required=True)
    parser.add_argument(
        "--created-from",
        default=None,
        help="Human label for the source run/batch used to create this dataset.",
    )
    parser.add_argument("--max-games", type=int, default=5)
    parser.add_argument("--per-role-per-phase", type=int, default=1)
    parser.add_argument("--max-samples", type=int, default=40)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing dataset file.",
    )
    args = parser.parse_args()
    if args.per_role_per_phase < 1:
        parser.error("--per-role-per-phase must be at least 1")
    if args.max_samples < 0:
        parser.error("--max-samples must be 0 or greater")
    return args


def write_manifest(path: Path, records: list[EvalDatasetRecord], args: Any) -> None:
    manifest = {
        "eval_set_id": args.eval_set_id,
        "created_at": datetime.now().isoformat(),
        "created_from": args.created_from,
        "dataset_path": str(path),
        "case_count": len(records),
        "seed": args.seed,
        "max_games": args.max_games,
        "per_role_per_phase": args.per_role_per_phase,
        "max_samples": args.max_samples,
    }
    manifest_path = path.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    out_path = args.output or default_output_path(args.eval_set_id)
    if out_path.exists() and not args.overwrite:
        raise FileExistsError(
            f"Dataset already exists: {out_path}. Pass --overwrite to replace it."
        )

    records = build_dataset_records(args)
    if not records:
        print("No records written.")
        return

    write_eval_dataset(out_path, records)
    write_manifest(out_path, records, args)
    print(f"Wrote {len(records)} EvalCase records to {out_path}")


if __name__ == "__main__":
    main()

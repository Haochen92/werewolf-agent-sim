from __future__ import annotations

import argparse
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from langgraph.store.memory import InMemoryStore

from evaluation.components.retrieval import (
    build_store_from_snapshots,
    keep_top_scored_items,
    parse_snapshot,
    redundancy_ratio,
)
from evaluation.core.io import write_jsonl
from evaluation.core.settings import REPO_ROOT, load_project_env

load_project_env()

from Agents.memory import (  # noqa: E402
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
)
from evaluation.core.formatters import (  # noqa: E402
    format_eval_retrieved_observations,
    format_eval_retrieved_strategy_points,
)
from evaluation.data.datasets import read_eval_dataset  # noqa: E402
from evaluation.judges.retrieval import (  # noqa: E402
    DEFAULT_RETRIEVAL_JUDGE_MODEL,
    run_retrieval_judge,
)


DEFAULT_JUDGE_MODEL = DEFAULT_RETRIEVAL_JUDGE_MODEL


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay fixed EvalCase retrieval queries against memory snapshots "
            "and optionally judge relevance and redundancy of retrieved items."
        )
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help=(
            "Local EvalCase dataset JSONL created by "
            "evaluation.experiments.dataset_builder."
        ),
    )
    parser.add_argument(
        "--snapshot",
        nargs=3,
        action="append",
        metavar=("LABEL", "OBSERVATIONS_JSON", "STRATEGY_POINTS_JSON"),
        required=True,
        help=(
            "Memory snapshot to test. Can be passed multiple times, for example: "
            "--snapshot pre Agents/data/werewolf_observations_pre_dedup.json "
            "Agents/data/werewolf_strategy_points_pre_dedup.json"
        ),
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help=(
            "Per-situation retrieval limit passed to the production retrieval "
            "helpers (default: 3)."
        ),
    )
    parser.add_argument(
        "--max-retrieved-items",
        type=int,
        default=0,
        help=(
            "Optional final cap on retrieved items judged per item type, after "
            "deduping by memory key and sorting by score. Use 0 for no cap."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output path. Defaults to eval_results/retrieval_eval_<timestamp>.jsonl.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=0,
        help="Limit number of eval rows to replay. Use 0 for all rows.",
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Call the LLM retrieval judge. Without this, only replay retrieval.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_JUDGE_MODEL,
        help=f"Judge model name (default: {DEFAULT_JUDGE_MODEL}).",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=1.0,
        help="Delay between judge calls when --judge is used.",
    )
    args = parser.parse_args()
    if args.max_samples < 0:
        parser.error("--max-samples must be 0 or greater")
    if args.top_k < 1:
        parser.error("--top-k must be at least 1")
    if args.max_retrieved_items < 0:
        parser.error("--max-retrieved-items must be 0 or greater")
    return args


def output_path(requested: Path | None) -> Path:
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"retrieval_eval_{timestamp}.jsonl"


def summarize_records(records: list[dict[str, Any]]) -> None:
    if not records:
        return

    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        buckets[(record["snapshot"], record["item_type"])].append(record)

    print("\nRETRIEVAL SUMMARY", flush=True)
    for (snapshot, item_type), rows in sorted(buckets.items()):
        judged = [row for row in rows if row.get("retrieval_quality") is not None]
        retrieved_counts = [row["retrieved_count"] for row in rows]
        ratios = [
            row["redundancy_ratio"]
            for row in rows
            if row.get("redundancy_ratio") is not None
        ]
        high_redundancy = [
            row
            for row in judged
            if row["retrieval_quality"].get("redundancy_score", 0) >= 4
        ]
        avg_retrieved = sum(retrieved_counts) / len(retrieved_counts)
        print(
            f"  {snapshot} / {item_type}: "
            f"n={len(rows)} avg_retrieved={avg_retrieved:.2f}",
            flush=True,
        )
        if judged:
            avg_relevance = sum(
                row["retrieval_quality"]["relevance_score"] for row in judged
            ) / len(judged)
            avg_redundancy = sum(
                row["retrieval_quality"]["redundancy_score"] for row in judged
            ) / len(judged)
            avg_unique = sum(
                row["retrieval_quality"]["unique_idea_count"] for row in judged
            ) / len(judged)
            avg_ratio = sum(ratios) / len(ratios) if ratios else 0.0
            print(
                f"    judged={len(judged)} avg_relevance={avg_relevance:.2f} "
                f"avg_redundancy={avg_redundancy:.2f} "
                f"avg_unique={avg_unique:.2f} avg_redundancy_ratio={avg_ratio:.1%} "
                f"high_redundancy={len(high_redundancy)}",
                flush=True,
            )


def main() -> None:
    args = parse_args()
    dataset_records = read_eval_dataset(args.dataset)
    if args.max_samples:
        dataset_records = dataset_records[: args.max_samples]
    snapshots = [parse_snapshot(raw) for raw in args.snapshot]
    out_path = output_path(args.output)
    max_retrieved_items = args.max_retrieved_items or None

    print(f"Loaded {len(dataset_records)} EvalCase records from {args.dataset}", flush=True)
    print(f"Testing {len(snapshots)} memory snapshot(s)", flush=True)
    print(
        f"Retrieval top_k={args.top_k}; "
        f"max_retrieved_items={max_retrieved_items or 'all'}",
        flush=True,
    )
    print(f"Writing replay results to {out_path}", flush=True)

    stores: dict[str, InMemoryStore] = {}
    for label, observations_path, strategy_points_path in snapshots:
        print(f"Loading snapshot '{label}'", flush=True)
        stores[label] = build_store_from_snapshots(
            observations_path,
            strategy_points_path,
        )

    written = 0
    output_records: list[dict[str, Any]] = []
    for record_index, dataset_record in enumerate(dataset_records, 1):
        case = dataset_record.eval_case
        role = case.player_role
        situations = case.situations
        if not role or not situations:
            print(
                f"[{record_index}/{len(dataset_records)}] Missing role or situations "
                f"for {dataset_record.case_id}; skipping",
                flush=True,
            )
            continue

        print(
            f"[{record_index}/{len(dataset_records)}] {case.span_name} "
            f"role={role} situations={len(situations)}",
            flush=True,
        )

        for label, store in stores.items():
            observations = keep_top_scored_items(
                retrieve_observations_for_agent(
                    store,
                    role,
                    situations,
                    top_k=args.top_k,
                ),
                max_retrieved_items,
            )
            strategy_points = keep_top_scored_items(
                retrieve_strategy_points_for_agent(
                    store,
                    role,
                    situations,
                    top_k=args.top_k,
                ),
                max_retrieved_items,
            )

            item_groups = [
                (
                    "observations",
                    observations,
                    format_eval_retrieved_observations(observations),
                ),
                (
                    "strategy_points",
                    strategy_points,
                    format_eval_retrieved_strategy_points(strategy_points),
                ),
            ]

            for item_type, items, formatted_items in item_groups:
                scores = None
                if args.judge:
                    scores = run_retrieval_judge(
                        item_type=item_type,
                        situations=situations,
                        items_formatted=formatted_items,
                        item_count=len(items),
                        model=args.model,
                    )
                    time.sleep(args.sleep_seconds)

                replay_record = {
                    "eval_set_id": dataset_record.eval_set_id,
                    "case_id": dataset_record.case_id,
                    "snapshot": label,
                    "source_dataset": str(args.dataset),
                    "trace_id": dataset_record.trace_id,
                    "observation_id": dataset_record.observation_id,
                    "span_name": case.span_name,
                    "role": role,
                    "day": case.day,
                    "round": case.round,
                    "action_type": case.action_type,
                    "situations": situations,
                    "top_k": args.top_k,
                    "max_retrieved_items": max_retrieved_items,
                    "item_type": item_type,
                    "retrieved_count": len(items),
                    "retrieved_items": [
                        item.model_dump(mode="json") for item in items
                    ],
                    "retrieval_quality": (
                        scores.model_dump(mode="json") if scores else None
                    ),
                    "redundancy_ratio": redundancy_ratio(len(items), scores),
                    "judge_model": args.model if args.judge else None,
                }
                write_jsonl(out_path, replay_record)
                output_records.append(replay_record)
                written += 1

                print(
                    f"  {label}/{item_type}: retrieved={len(items)} "
                    f"rel={scores.relevance_score if scores else None} "
                    f"red={scores.redundancy_score if scores else None}",
                    flush=True,
                )

    summarize_records(output_records)
    print(f"Done. Wrote {written} records to {out_path}", flush=True)


if __name__ == "__main__":
    main()

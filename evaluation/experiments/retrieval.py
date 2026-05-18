"""Replay captured retrieval queries against one or more memory snapshots.

This experiment uses the situation summaries frozen in each ``EvalCase`` and
tests how different exported observation/strategy memory stores affect the
retrieved items. Optional judging scores relevance and redundancy.
"""

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
    redundancy_ratio,
)
from evaluation.core.config_schema import RetrievalExperimentConfig
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
from evaluation.judges.retrieval import run_retrieval_judge  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay fixed EvalCase retrieval queries against memory snapshots "
            "and optionally judge relevance and redundancy of retrieved items."
        )
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def read_config(path: Path) -> RetrievalExperimentConfig:
    """Load the retrieval experiment JSON config."""
    return RetrievalExperimentConfig.model_validate_json(
        path.read_text(encoding="utf-8")
    )


def output_path(requested: Path | None) -> Path:
    """Return the requested output path or a timestamped default."""
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"retrieval_eval_{timestamp}.jsonl"


def summarize_records(records: list[dict[str, Any]]) -> None:
    """Print aggregate retrieval quality metrics grouped by snapshot and item type."""
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
    config = read_config(args.config)
    dataset_records = read_eval_dataset(config.dataset)
    if config.max_samples:
        dataset_records = dataset_records[: config.max_samples]
    snapshots = [
        (snapshot.label, snapshot.observations_path, snapshot.strategy_points_path)
        for snapshot in config.snapshots
    ]
    out_path = output_path(config.output)
    max_retrieved_items = config.max_retrieved_items or None

    print(f"Loaded {len(dataset_records)} EvalCase records from {config.dataset}", flush=True)
    print(f"Testing {len(snapshots)} memory snapshot(s)", flush=True)
    print(
        f"Retrieval top_k={config.top_k}; "
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
                    top_k=config.top_k,
                ),
                max_retrieved_items,
            )
            strategy_points = keep_top_scored_items(
                retrieve_strategy_points_for_agent(
                    store,
                    role,
                    situations,
                    top_k=config.top_k,
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
                if config.judge:
                    scores = run_retrieval_judge(
                        item_type=item_type,
                        situations=situations,
                        items_formatted=formatted_items,
                        item_count=len(items),
                        model=config.judge_model,
                    )
                    time.sleep(config.sleep_seconds)

                replay_record = {
                    "eval_set_id": dataset_record.eval_set_id,
                    "case_id": dataset_record.case_id,
                    "snapshot": label,
                    "source_dataset": str(config.dataset),
                    "trace_id": dataset_record.trace_id,
                    "observation_id": dataset_record.observation_id,
                    "span_name": case.span_name,
                    "role": role,
                    "day": case.day,
                    "round": case.round,
                    "action_type": case.action_type,
                    "situations": situations,
                    "top_k": config.top_k,
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
                    "judge_model": config.judge_model if config.judge else None,
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

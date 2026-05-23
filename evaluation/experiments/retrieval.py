"""Replay captured retrieval queries against one or more memory snapshots.

This experiment uses the situation summaries frozen in each ``EvalCase`` and
tests how different exported observation/strategy memory stores affect the
retrieved items.  Retrieval pipeline variants (filtering, reranking) can be
compared side-by-side.  Optional judging scores relevance and redundancy.
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
from evaluation.core.config_schema import (
    RetrievalExperimentConfig,
    RetrievalPipelineConfig,
)
from evaluation.core.io import write_jsonl
from evaluation.core.report import generate_retrieval_report
from evaluation.core.settings import REPO_ROOT, load_project_env

load_project_env()

from Agents.memory import (  # noqa: E402
    RETRIEVAL_KEEP_PER_SITUATION,
    embeddings as memory_embeddings,
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
)
from Agents.reranker import (  # noqa: E402
    RERANK_TOP_K,
    rerank_observations,
    rerank_strategy_points,
)
from Agents.retrieval_filters import cap_per_situation, dedup_gate, embed_texts, mmr_filter  # noqa: E402
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
    """Print aggregate retrieval quality metrics grouped by snapshot, pipeline, and item type."""
    if not records:
        return

    buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        buckets[
            (record["snapshot"], record["pipeline"], record["item_type"])
        ].append(record)

    print("\nRETRIEVAL SUMMARY", flush=True)
    for (snapshot, pipeline, item_type), rows in sorted(buckets.items()):
        judged = [row for row in rows if row.get("retrieval_quality") is not None]
        retrieved_counts = [row["retrieved_count"] for row in rows]
        ratios = [
            row["redundancy_ratio"]
            for row in rows
            if row.get("redundancy_ratio") is not None
        ]
        low_efficiency = [
            row
            for row in judged
            if row["retrieval_quality"].get("efficiency", 5) <= 2
        ]
        avg_retrieved = sum(retrieved_counts) / len(retrieved_counts)
        print(
            f"  {snapshot} / {pipeline} / {item_type}: "
            f"n={len(rows)} avg_retrieved={avg_retrieved:.2f}",
            flush=True,
        )
        if judged:
            avg_relevance = sum(
                row["retrieval_quality"]["relevance"] for row in judged
            ) / len(judged)
            avg_efficiency = sum(
                row["retrieval_quality"]["efficiency"] for row in judged
            ) / len(judged)
            avg_unique = sum(
                row["retrieval_quality"]["unique_lessons"] for row in judged
            ) / len(judged)
            avg_ratio = sum(ratios) / len(ratios) if ratios else 0.0
            print(
                f"    judged={len(judged)} avg_relevance={avg_relevance:.2f} "
                f"avg_efficiency={avg_efficiency:.2f} "
                f"avg_unique_lessons={avg_unique:.2f} avg_redundancy_ratio={avg_ratio:.1%} "
                f"low_efficiency={len(low_efficiency)}",
                flush=True,
            )


def _effective_top_k(base_top_k: int, pipeline: RetrievalPipelineConfig) -> int:
    if pipeline.filtering or pipeline.reranking:
        return max(base_top_k, RERANK_TOP_K)
    return base_top_k


def _apply_pipeline(
    observations: list,
    strategy_points: list,
    situations: list[str],
    pipeline: RetrievalPipelineConfig,
) -> tuple[list, list]:
    if pipeline.filtering:
        observations = sorted(
            observations, key=lambda o: o.score or 0.0, reverse=True,
        )
        strategy_points = sorted(
            strategy_points, key=lambda sp: sp.score or 0.0, reverse=True,
        )

        if len(observations) > 1:
            obs_embeddings = embed_texts(
                [o.observation.situation for o in observations],
                memory_embeddings,
            )
            observations = dedup_gate(
                observations,
                obs_embeddings,
                similarity_threshold=pipeline.dedup_threshold,
            )

        if len(strategy_points) > 1:
            sp_embeddings = embed_texts(
                [sp.strategy_point.situation for sp in strategy_points],
                memory_embeddings,
            )
            sp_scores = [sp.score or 0.0 for sp in strategy_points]
            strategy_points = mmr_filter(
                strategy_points,
                sp_embeddings,
                sp_scores,
                lambda_=pipeline.mmr_lambda,
                top_k=pipeline.mmr_top_k,
            )

    if pipeline.reranking:
        from Agents.agents import get_llm
        llm = get_llm()
        observations = rerank_observations(llm, situations, observations)
        strategy_points = rerank_strategy_points(llm, situations, strategy_points)

    return observations, strategy_points


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
    pipelines = config.pipelines
    out_path = output_path(config.output)
    max_retrieved_items = config.max_retrieved_items or None

    print(f"Loaded {len(dataset_records)} EvalCase records from {config.dataset}", flush=True)
    print(f"Testing {len(snapshots)} memory snapshot(s)", flush=True)
    print(
        f"Testing {len(pipelines)} pipeline(s): "
        f"{', '.join(p.label for p in pipelines)}",
        flush=True,
    )
    print(
        f"Retrieval base top_k={config.top_k}; "
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

        for snapshot_label, store in stores.items():
            for pipeline in pipelines:
                top_k = _effective_top_k(config.top_k, pipeline)

                raw_observations = retrieve_observations_for_agent(
                    store, role, case.action_phase, situations, top_k=top_k,
                )
                raw_strategy_points = retrieve_strategy_points_for_agent(
                    store, role, case.action_phase, situations, top_k=top_k,
                )

                observations, strategy_points = _apply_pipeline(
                    raw_observations, raw_strategy_points, situations, pipeline,
                )

                observations = keep_top_scored_items(
                    observations, max_retrieved_items,
                )
                strategy_points = keep_top_scored_items(
                    strategy_points, max_retrieved_items,
                )

                observations = cap_per_situation(
                    observations,
                    get_situation=lambda o: o.matched_situation,
                    get_score=lambda o: o.score or 0.0,
                    keep=RETRIEVAL_KEEP_PER_SITUATION,
                )
                strategy_points = cap_per_situation(
                    strategy_points,
                    get_situation=lambda sp: sp.matched_situation,
                    get_score=lambda sp: sp.score or 0.0,
                    keep=RETRIEVAL_KEEP_PER_SITUATION,
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
                            thinking_level=config.judge_thinking_level,
                        )
                        time.sleep(config.sleep_seconds)

                    replay_record = {
                        "eval_set_id": dataset_record.eval_set_id,
                        "case_id": dataset_record.case_id,
                        "snapshot": snapshot_label,
                        "pipeline": pipeline.label,
                        "pipeline_filtering": pipeline.filtering,
                        "pipeline_reranking": pipeline.reranking,
                        "dedup_threshold": pipeline.dedup_threshold,
                        "mmr_lambda": pipeline.mmr_lambda,
                        "mmr_top_k": pipeline.mmr_top_k,
                        "source_dataset": str(config.dataset),
                        "trace_id": dataset_record.trace_id,
                        "observation_id": dataset_record.observation_id,
                        "span_name": case.span_name,
                        "role": role,
                        "day": case.day,
                        "round": case.round,
                        "action_phase": case.action_phase,
                        "situations": situations,
                        "top_k": top_k,
                        "max_retrieved_items": max_retrieved_items,
                        "item_type": item_type,
                        "pre_pipeline_count": (
                            len(raw_observations)
                            if item_type == "observations"
                            else len(raw_strategy_points)
                        ),
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
                        f"  {snapshot_label}/{pipeline.label}/{item_type}: "
                        f"retrieved={len(items)} "
                        f"rel={scores.relevance if scores else None} "
                        f"eff={scores.efficiency if scores else None}",
                        flush=True,
                    )

    summarize_records(output_records)
    print(f"Done. Wrote {written} records to {out_path}", flush=True)

    report_path = generate_retrieval_report(out_path, dataset_path=config.dataset)
    print(f"Report: {report_path}", flush=True)


if __name__ == "__main__":
    main()

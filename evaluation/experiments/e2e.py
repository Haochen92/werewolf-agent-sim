"""Turn-level replay of the episodic memory path.

For each frozen ``EvalCase`` this experiment regenerates the situation summary,
retrieves memories from a configured snapshot, reruns the final action prompt,
and optionally judges the combined result.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from evaluation.components.application import (
    application_case_for_judge,
    run_application_action,
)
from evaluation.components.retrieval import (
    build_store_from_snapshots,
    keep_top_scored_items,
)
from evaluation.components.situation_summary import run_situation_summary_variant
from evaluation.core.config_schema import E2EExperimentConfig, VariantConfig
from evaluation.core.io import write_jsonl
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.data.datasets import read_eval_dataset
from evaluation.judges.pipeline import run_judge

from Agents.memory import (
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
)
from Agents.schemas.evaluation import EvalCase


load_project_env()


def output_path(requested: Path | None) -> Path:
    """Return the requested output path or a timestamped default."""
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"e2e_eval_{timestamp}.jsonl"


def case_without_memory(case: EvalCase) -> EvalCase:
    """Clear memory-derived fields before regenerating the situation summary."""
    return case.model_copy(
        update={
            "retrieved_observations": [],
            "retrieved_strategy_points": [],
            "situations": [],
        }
    )


def run_e2e_case(
    case: EvalCase,
    *,
    store: Any,
    snapshot_label: str,
    summary_config: VariantConfig,
    top_k: int,
    max_retrieved_items: int | None,
    judge: bool,
    judge_model: str,
) -> dict[str, Any]:
    """Replay one frozen turn through summary, retrieval, action, and judge."""
    summary = run_situation_summary_variant(
        case_without_memory(case),
        summary_config,
    )
    situations = summary["situations"]
    observations = keep_top_scored_items(
        retrieve_observations_for_agent(
            store,
            case.player_role,
            situations,
            top_k=top_k,
        ),
        max_retrieved_items,
    )
    strategy_points = keep_top_scored_items(
        retrieve_strategy_points_for_agent(
            store,
            case.player_role,
            situations,
            top_k=top_k,
        ),
        max_retrieved_items,
    )

    replay_case = case.model_copy(
        update={
            "memory_enabled": True,
            "retrieval_skipped_reason": None,
            "situations": situations,
            "retrieved_observations": observations,
            "retrieved_strategy_points": strategy_points,
        }
    )
    action_result, agent_message, agent_vote, updated_strategy = run_application_action(
        replay_case,
        retrieved_observations=observations,
        strategy_points=strategy_points,
    )
    judged_case = application_case_for_judge(
        replay_case,
        agent_message=agent_message,
        agent_vote=agent_vote,
        updated_strategy=updated_strategy,
    )
    scores = run_judge(judged_case, model=judge_model) if judge else None

    return {
        "snapshot": snapshot_label,
        "summary": summary,
        "situations": situations,
        "retrieved_observation_count": len(observations),
        "retrieved_strategy_point_count": len(strategy_points),
        "retrieved_observations": [
            item.model_dump(mode="json") for item in observations
        ],
        "retrieved_strategy_points": [
            item.model_dump(mode="json") for item in strategy_points
        ],
        "action_result": action_result,
        "updated_strategy": updated_strategy,
        "judge_scores": scores.model_dump(mode="json") if scores else None,
        "judge_model": judge_model if judge else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay the dataset E2E memory path: summary -> retrieval -> action."
        )
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def read_config(path: Path) -> E2EExperimentConfig:
    """Load the E2E experiment JSON config."""
    return E2EExperimentConfig.model_validate_json(
        path.read_text(encoding="utf-8")
    )


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    records = read_eval_dataset(config.dataset)
    if config.max_samples:
        records = records[: config.max_samples]
    snapshots = [
        (snapshot.label, snapshot.observations_path, snapshot.strategy_points_path)
        for snapshot in config.snapshots
    ]
    stores = {
        label: build_store_from_snapshots(observations_path, strategy_points_path)
        for label, observations_path, strategy_points_path in snapshots
    }
    summary_config = config.summary
    max_retrieved_items = config.max_retrieved_items or None
    out_path = output_path(config.output)

    print(f"Loaded {len(records)} EvalCase records from {config.dataset}", flush=True)
    print(f"Testing {len(stores)} snapshot(s)", flush=True)
    print(f"Summary model={summary_config.model}", flush=True)
    print(f"Writing E2E replay results to {out_path}", flush=True)

    written = 0
    for index, record in enumerate(records, 1):
        case = record.eval_case
        print(
            f"[{index}/{len(records)}] {record.case_id} "
            f"role={case.player_role} action={case.action_type}",
            flush=True,
        )
        for snapshot_label, store in stores.items():
            try:
                result = run_e2e_case(
                    case,
                    store=store,
                    snapshot_label=snapshot_label,
                    summary_config=summary_config,
                    top_k=config.top_k,
                    max_retrieved_items=max_retrieved_items,
                    judge=config.judge,
                    judge_model=config.judge_model,
                )
            except Exception as exc:
                result = {
                    "snapshot": snapshot_label,
                    "error": str(exc),
                }
                print(f"  {snapshot_label}: error: {exc}", flush=True)
            else:
                scores = result.get("judge_scores")
                if scores:
                    print(
                        f"  {snapshot_label}: summary={scores['summary_quality']} "
                        f"relevance={scores['retrieval_relevance']} "
                        f"application={scores['strategy_application']} "
                        f"grounding={scores['grounding']}",
                        flush=True,
                    )
                else:
                    print(
                        f"  {snapshot_label}: situations={len(result['situations'])} "
                        f"obs={result['retrieved_observation_count']} "
                        f"strategy={result['retrieved_strategy_point_count']}",
                        flush=True,
                    )
                if config.judge:
                    time.sleep(config.sleep_seconds)

            write_jsonl(
                out_path,
                {
                    "eval_set_id": record.eval_set_id,
                    "case_id": record.case_id,
                    "trace_id": record.trace_id,
                    "observation_id": record.observation_id,
                    "span_name": record.span_name,
                    "role": case.player_role,
                    "day": case.day,
                    "round": case.round,
                    "action_type": case.action_type,
                    "top_k": config.top_k,
                    "max_retrieved_items": max_retrieved_items,
                    **result,
                },
            )
            written += 1

    print(f"Done. Wrote {written} records to {out_path}", flush=True)


if __name__ == "__main__":
    main()

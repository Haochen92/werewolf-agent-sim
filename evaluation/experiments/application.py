"""Replay the final action stage from frozen ``EvalCase`` records.

This experiment keeps the turn context fixed and changes the memory inputs
used by the discussion/vote prompt. It is useful for checking whether captured
memories improve the final action compared with no memory.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from Agents.formatters import format_agent_action
from Agents.memory import retrieve_observations_for_agent, retrieve_strategy_points_for_agent
from Agents.schemas.evaluation import EvalCase
from evaluation.components.application import (
    application_case_for_judge,
    run_application_action,
)
from evaluation.components.retrieval import build_store_from_snapshots, keep_top_scored_items
from evaluation.core.config_schema import ApplicationExperimentConfig
from evaluation.core.io import write_jsonl
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.data.datasets import read_eval_dataset
from evaluation.judges.application import run_application_judge


load_project_env()


def output_path(requested: Path | None) -> Path:
    """Return the requested output path or a timestamped default."""
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"application_eval_{timestamp}.jsonl"


def memory_inputs_for_mode(case: EvalCase, mode: str) -> tuple[list[Any], list[Any]]:
    """Choose which memory inputs should be supplied to the replayed action."""
    if mode == "captured":
        return case.retrieved_observations, case.retrieved_strategy_points
    if mode == "none":
        return [], []
    raise ValueError(f"Unsupported memory mode: {mode}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay the action/application stage from frozen EvalCase rows."
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def read_config(path: Path) -> ApplicationExperimentConfig:
    """Load the application experiment JSON config."""
    return ApplicationExperimentConfig.model_validate_json(
        path.read_text(encoding="utf-8")
    )


def _retrieve_from_snapshot(
    store: Any,
    case: EvalCase,
    top_k: int,
    max_retrieved_items: int | None,
) -> tuple[list[Any], list[Any]]:
    """Re-retrieve observations and strategy points from a snapshot store."""
    observations = keep_top_scored_items(
        retrieve_observations_for_agent(
            store, case.player_role, case.action_phase, case.situations, top_k=top_k,
        ),
        max_retrieved_items,
    )
    strategy_points = keep_top_scored_items(
        retrieve_strategy_points_for_agent(
            store, case.player_role, case.action_phase, case.situations, top_k=top_k,
        ),
        max_retrieved_items,
    )
    return observations, strategy_points


def _run_and_judge_case(
    case: EvalCase,
    record: Any,
    *,
    retrieved_observations: list[Any],
    strategy_points: list[Any],
    config: ApplicationExperimentConfig,
    snapshot_label: str | None = None,
) -> dict[str, Any]:
    """Replay one case's action, judge it, and return the result record."""
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
        print(f"  Error: {exc}", flush=True)
        return {
            "eval_set_id": record.eval_set_id,
            "case_id": record.case_id,
            "error": str(exc),
        }

    scores = (
        run_application_judge(judged_case, model=config.judge_model)
        if config.judge
        else None
    )
    replay_record: dict[str, Any] = {
        "eval_set_id": record.eval_set_id,
        "case_id": record.case_id,
        "trace_id": record.trace_id,
        "observation_id": record.observation_id,
        "span_name": record.span_name,
        "role": case.player_role,
        "day": case.day,
        "round": case.round,
        "action_phase": case.action_phase,
        "memory_mode": config.memory_mode,
        "retrieved_observation_count": len(retrieved_observations),
        "retrieved_strategy_point_count": len(strategy_points),
        "action_result": result,
        "agent_decision": format_agent_action(
            case.action_phase,
            message=agent_message,
            vote=agent_vote,
        ),
        "updated_strategy": updated_strategy,
        "application_scores": (
            scores.model_dump(mode="json") if scores else None
        ),
        "judge_model": config.judge_model if config.judge else None,
    }
    if snapshot_label is not None:
        replay_record["snapshot"] = snapshot_label
    if scores:
        print(
            f"  Scores: action={scores.action_quality} "
            f"application={scores.strategy_application} "
            f"grounding={scores.grounding} "
            f"adoption={scores.adoption_accuracy} "
            f"direction={scores.attribution_direction}",
            flush=True,
        )
    if config.judge:
        time.sleep(config.sleep_seconds)
    return replay_record


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    records = read_eval_dataset(config.dataset)
    if config.max_samples:
        records = records[: config.max_samples]
    out_path = output_path(config.output)

    stores: dict[str, Any] = {}
    if config.memory_mode == "snapshot" and config.snapshots:
        for snap in config.snapshots:
            print(f"Loading snapshot '{snap.label}'...", flush=True)
            stores[snap.label] = build_store_from_snapshots(
                snap.observations_path, snap.strategy_points_path,
            )

    print(f"Loaded {len(records)} EvalCase records from {config.dataset}", flush=True)
    print(f"Application memory mode={config.memory_mode}", flush=True)
    if stores:
        print(f"Snapshots: {list(stores.keys())}", flush=True)
    print(f"Writing replay results to {out_path}", flush=True)

    max_items = config.max_retrieved_items or None
    written = 0
    for index, record in enumerate(records, 1):
        case = record.eval_case
        print(
            f"[{index}/{len(records)}] {record.case_id} "
            f"role={case.player_role} action={case.action_phase}",
            flush=True,
        )

        if config.memory_mode == "snapshot":
            for label, store in stores.items():
                observations, strategy_points = _retrieve_from_snapshot(
                    store, case, config.top_k, max_items,
                )
                print(
                    f"  {label}: obs={len(observations)} sp={len(strategy_points)}",
                    flush=True,
                )
                replay_record = _run_and_judge_case(
                    case, record,
                    retrieved_observations=observations,
                    strategy_points=strategy_points,
                    config=config,
                    snapshot_label=label,
                )
                write_jsonl(out_path, replay_record)
                written += 1
        else:
            observations, strategy_points = memory_inputs_for_mode(
                case, config.memory_mode,
            )
            replay_record = _run_and_judge_case(
                case, record,
                retrieved_observations=observations,
                strategy_points=strategy_points,
                config=config,
            )
            write_jsonl(out_path, replay_record)
            written += 1

    print(f"Done. Wrote {written} records to {out_path}", flush=True)


if __name__ == "__main__":
    main()

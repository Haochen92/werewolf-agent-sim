"""One runner over a frozen ``EvalCase``: optionally replay a stage, then judge it.

Collapses the old captured / application / e2e CLIs — they were a single axis
(judge the final action, differing only by how much upstream gets regenerated):

    replay=none    judge the turn exactly as recorded          (was: captured)
    replay=action  regenerate the final action, then judge     (was: application)
    replay=all     regenerate summary -> retrieval -> action    (was: e2e)

``judge`` selects the grader independently of depth: ``application`` (action
rubric), ``pipeline`` (summary+retrieval+action rubric), or ``off``. Memory inputs
for a replayed action come from ``memory_mode`` (captured | none | snapshot);
``replay=all`` always retrieves from a snapshot store.

    poetry run eval-turn --config evaluation/config/e2e/e2e_v2_memory.json
    # or override the depth: --replay none|action|all
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from Agents.memory import (
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
)
from Agents.prompts.prompt_formatters import format_agent_action
from Agents.schemas.evaluation import EvalCase
from evaluation.src.core.config_schema import TurnEvalConfig, VariantConfig
from evaluation.src.core.io import write_jsonl
from evaluation.src.core.settings import REPO_ROOT, load_project_env
from evaluation.src.data.frozen_sets import read_eval_dataset
from evaluation.src.judges.turn_action import run_application_judge
from evaluation.src.judges.turn_pipeline import run_judge
from evaluation.src.replay.turn_action import (
    application_case_for_judge,
    run_application_action,
)
from evaluation.src.replay.retrieval import (
    build_store_from_snapshots,
    keep_top_scored_items,
)
from evaluation.src.replay.situation_summary import run_situation_summary_variant

load_project_env()


def output_path(requested: Path | None) -> Path:
    """Return the requested output path or a timestamped default."""
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "evaluation" / "eval_results" / f"turn_eval_{timestamp}.jsonl"


def _judge_scores(case: EvalCase, judge: str, judge_model: str):
    """Run the selected judge on a (captured or replayed) case; None if off."""
    if judge == "application":
        return run_application_judge(case, model=judge_model)
    if judge == "pipeline":
        return run_judge(case, model=judge_model)
    return None


def _print_scores(scores: Any, judge: str) -> None:
    if not scores:
        return
    if judge == "application":
        print(
            f"  Scores: action={scores.action_quality} "
            f"application={scores.strategy_application} "
            f"grounding={scores.grounding} "
            f"adoption={scores.adoption_accuracy} "
            f"direction={scores.attribution_direction}",
            flush=True,
        )
    else:
        print(
            f"  Scores: summary={scores.summary_quality} "
            f"retrieval={scores.retrieval_relevance} "
            f"application={scores.strategy_application} "
            f"grounding={scores.grounding}",
            flush=True,
        )


# ---------------------------------------------------------------------------
# replay=none — judge the turn as captured (no regeneration)
# ---------------------------------------------------------------------------


def judge_captured_case(case: EvalCase, record: Any, config: TurnEvalConfig) -> dict[str, Any]:
    scores = _judge_scores(case, config.judge, config.judge_model)
    _print_scores(scores, config.judge)
    return {
        "eval_set_id": record.eval_set_id,
        "case_id": record.case_id,
        "trace_id": record.trace_id,
        "observation_id": record.observation_id,
        "span_name": record.span_name,
        "role": case.player_role,
        "day": case.day,
        "round": case.round,
        "action_phase": case.action_phase,
        "replay": "none",
        "judge": config.judge,
        "source_dataset": str(config.dataset),
        "situations": case.situations,
        "retrieved_observation_count": len(case.retrieved_observations),
        "retrieved_strategy_point_count": len(case.retrieved_strategy_points),
        "agent_decision": format_agent_action(
            case.action_phase, message=case.agent_message, vote=case.agent_vote,
        ),
        "updated_strategy": case.updated_strategy,
        "judge_scores": scores.model_dump(mode="json") if scores else None,
        "judge_model": config.judge_model if config.judge != "off" else None,
    }


# ---------------------------------------------------------------------------
# replay=action — regenerate the final action, then judge
# ---------------------------------------------------------------------------


def memory_inputs_for_mode(case: EvalCase, mode: str) -> tuple[list[Any], list[Any]]:
    """Choose which memory inputs feed the replayed action (captured | none)."""
    if mode == "captured":
        return case.retrieved_observations, case.retrieved_strategy_points
    if mode == "none":
        return [], []
    raise ValueError(f"Unsupported memory mode: {mode}")


def _retrieve_from_snapshot(
    store: Any, case: EvalCase, top_k: int, max_retrieved_items: int | None,
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


def replay_action_case(
    case: EvalCase,
    record: Any,
    *,
    retrieved_observations: list[Any],
    strategy_points: list[Any],
    config: TurnEvalConfig,
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
            case.model_copy(update={
                "retrieved_observations": retrieved_observations,
                "retrieved_strategy_points": strategy_points,
            }),
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

    scores = _judge_scores(judged_case, config.judge, config.judge_model)
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
        "replay": "action",
        "memory_mode": config.memory_mode,
        "retrieved_observation_count": len(retrieved_observations),
        "retrieved_strategy_point_count": len(strategy_points),
        "action_result": result,
        "agent_decision": format_agent_action(
            case.action_phase, message=agent_message, vote=agent_vote,
        ),
        "updated_strategy": updated_strategy,
        "judge": config.judge,
        "judge_scores": scores.model_dump(mode="json") if scores else None,
        "judge_model": config.judge_model if config.judge != "off" else None,
    }
    if snapshot_label is not None:
        replay_record["snapshot"] = snapshot_label
    _print_scores(scores, config.judge)
    if config.judge != "off":
        time.sleep(config.sleep_seconds)
    return replay_record


# ---------------------------------------------------------------------------
# replay=all — regenerate summary -> retrieval -> action, then judge
# ---------------------------------------------------------------------------


def _case_without_memory(case: EvalCase) -> EvalCase:
    """Clear memory-derived fields before regenerating the situation summary."""
    return case.model_copy(update={
        "retrieved_observations": [],
        "retrieved_strategy_points": [],
        "situations": [],
    })


def replay_full_case(
    case: EvalCase,
    *,
    store: Any,
    snapshot_label: str,
    summary_config: VariantConfig,
    config: TurnEvalConfig,
) -> dict[str, Any]:
    """Replay one frozen turn through summary, retrieval, action, then judge."""
    max_retrieved_items = config.max_retrieved_items or None
    summary = run_situation_summary_variant(_case_without_memory(case), summary_config)
    situations = summary["situations"]
    observations = keep_top_scored_items(
        retrieve_observations_for_agent(
            store, case.player_role, case.action_phase, situations, top_k=config.top_k,
        ),
        max_retrieved_items,
    )
    strategy_points = keep_top_scored_items(
        retrieve_strategy_points_for_agent(
            store, case.player_role, case.action_phase, situations, top_k=config.top_k,
        ),
        max_retrieved_items,
    )

    replay_case = case.model_copy(update={
        "memory_enabled": True,
        "retrieval_skipped_reason": None,
        "situations": situations,
        "retrieved_observations": observations,
        "retrieved_strategy_points": strategy_points,
    })
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
    scores = _judge_scores(judged_case, config.judge, config.judge_model)

    return {
        "snapshot": snapshot_label,
        "replay": "all",
        "summary": summary,
        "situations": situations,
        "retrieved_observation_count": len(observations),
        "retrieved_strategy_point_count": len(strategy_points),
        "retrieved_observations": [i.model_dump(mode="json") for i in observations],
        "retrieved_strategy_points": [i.model_dump(mode="json") for i in strategy_points],
        "action_result": action_result,
        "updated_strategy": updated_strategy,
        "judge": config.judge,
        "judge_scores": scores.model_dump(mode="json") if scores else None,
        "judge_model": config.judge_model if config.judge != "off" else None,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Judge a frozen turn, optionally replaying summary/retrieval/action first."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--replay", choices=["none", "action", "all"], default=None,
        help="Override the config's replay depth.",
    )
    return parser.parse_args()


def read_config(path: Path) -> TurnEvalConfig:
    return TurnEvalConfig.model_validate_json(path.read_text(encoding="utf-8"))


def _run_none(records, config, out_path) -> int:
    written = 0
    for index, record in enumerate(records, 1):
        case = record.eval_case
        print(
            f"[{index}/{len(records)}] {record.case_id} "
            f"role={case.player_role} action={case.action_phase}",
            flush=True,
        )
        write_jsonl(out_path, judge_captured_case(case, record, config))
        written += 1
        if config.judge != "off":
            time.sleep(config.sleep_seconds)
    return written


def _run_action(records, config, out_path) -> int:
    stores: dict[str, Any] = {}
    if config.memory_mode == "snapshot" and config.snapshots:
        for snap in config.snapshots:
            print(f"Loading snapshot '{snap.label}'...", flush=True)
            stores[snap.label] = build_store_from_snapshots(
                snap.observations_path, snap.strategy_points_path,
            )
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
                print(f"  {label}: obs={len(observations)} sp={len(strategy_points)}", flush=True)
                write_jsonl(out_path, replay_action_case(
                    case, record,
                    retrieved_observations=observations,
                    strategy_points=strategy_points,
                    config=config, snapshot_label=label,
                ))
                written += 1
        else:
            observations, strategy_points = memory_inputs_for_mode(case, config.memory_mode)
            write_jsonl(out_path, replay_action_case(
                case, record,
                retrieved_observations=observations,
                strategy_points=strategy_points,
                config=config,
            ))
            written += 1
    return written


def _run_all(records, config, out_path) -> int:
    stores = {
        snap.label: build_store_from_snapshots(snap.observations_path, snap.strategy_points_path)
        for snap in config.snapshots
    }
    print(f"Testing {len(stores)} snapshot(s), summary model={config.summary.model}", flush=True)
    written = 0
    for index, record in enumerate(records, 1):
        case = record.eval_case
        print(
            f"[{index}/{len(records)}] {record.case_id} "
            f"role={case.player_role} action={case.action_phase}",
            flush=True,
        )
        for snapshot_label, store in stores.items():
            try:
                result = replay_full_case(
                    case, store=store, snapshot_label=snapshot_label,
                    summary_config=config.summary, config=config,
                )
            except Exception as exc:
                result = {"snapshot": snapshot_label, "replay": "all", "error": str(exc)}
                print(f"  {snapshot_label}: error: {exc}", flush=True)
            else:
                if result.get("judge_scores"):
                    s = result["judge_scores"]
                    print(
                        f"  {snapshot_label}: summary={s['summary_quality']} "
                        f"relevance={s['retrieval_relevance']} "
                        f"application={s['strategy_application']} grounding={s['grounding']}",
                        flush=True,
                    )
                else:
                    print(
                        f"  {snapshot_label}: situations={len(result['situations'])} "
                        f"obs={result['retrieved_observation_count']} "
                        f"strategy={result['retrieved_strategy_point_count']}",
                        flush=True,
                    )
                if config.judge != "off":
                    time.sleep(config.sleep_seconds)
            write_jsonl(out_path, {
                "eval_set_id": record.eval_set_id,
                "case_id": record.case_id,
                "trace_id": record.trace_id,
                "observation_id": record.observation_id,
                "span_name": record.span_name,
                "role": case.player_role,
                "day": case.day,
                "round": case.round,
                "action_phase": case.action_phase,
                "top_k": config.top_k,
                "max_retrieved_items": config.max_retrieved_items or None,
                **result,
            })
            written += 1
    return written


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    if args.replay:
        config = config.model_copy(update={"replay": args.replay})

    records = read_eval_dataset(config.dataset)
    if config.max_samples:
        records = records[: config.max_samples]
    out_path = output_path(config.output)

    print(f"Loaded {len(records)} EvalCase records from {config.dataset}", flush=True)
    print(f"replay={config.replay}  judge={config.judge}  model={config.judge_model}", flush=True)
    print(f"Writing turn-eval results to {out_path}", flush=True)

    if config.replay == "none":
        written = _run_none(records, config, out_path)
    elif config.replay == "action":
        written = _run_action(records, config, out_path)
    else:
        written = _run_all(records, config, out_path)

    print(f"Done. Wrote {written} records to {out_path}", flush=True)


if __name__ == "__main__":
    main()

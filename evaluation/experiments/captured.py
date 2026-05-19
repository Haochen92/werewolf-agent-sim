"""Score captured EvalCase records without replaying generation or retrieval.

This evaluation keeps the dataset exactly as captured: situation summaries,
retrieved memories, final action, and strategy update all come from the frozen
EvalCase row. The only model call is the judge.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path

from Agents.formatters import format_agent_action
from evaluation.core.config_schema import CapturedEvaluationConfig
from evaluation.core.io import write_jsonl
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.data.datasets import read_eval_dataset
from evaluation.judges.pipeline import run_judge


load_project_env()


def output_path(requested: Path | None) -> Path:
    """Return the requested output path or a timestamped default."""
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"captured_eval_{timestamp}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Judge captured EvalCase rows without replaying any pipeline stage."
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def read_config(path: Path) -> CapturedEvaluationConfig:
    """Load the captured evaluation JSON config."""
    return CapturedEvaluationConfig.model_validate_json(
        path.read_text(encoding="utf-8")
    )


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    records = read_eval_dataset(config.dataset)
    if config.max_samples:
        records = records[: config.max_samples]
    out_path = output_path(config.output)

    print(f"Loaded {len(records)} EvalCase records from {config.dataset}", flush=True)
    print(f"Judge model={config.judge_model}", flush=True)
    print(f"Writing captured evaluation results to {out_path}", flush=True)

    written = 0
    for index, record in enumerate(records, 1):
        case = record.eval_case
        print(
            f"[{index}/{len(records)}] {record.case_id} "
            f"role={case.player_role} action={case.action_type}",
            flush=True,
        )

        scores = run_judge(case, model=config.judge_model)
        result_record = {
            "eval_set_id": record.eval_set_id,
            "case_id": record.case_id,
            "trace_id": record.trace_id,
            "observation_id": record.observation_id,
            "span_name": record.span_name,
            "role": case.player_role,
            "day": case.day,
            "round": case.round,
            "action_type": case.action_type,
            "source_dataset": str(config.dataset),
            "situations": case.situations,
            "retrieved_observation_count": len(case.retrieved_observations),
            "retrieved_strategy_point_count": len(case.retrieved_strategy_points),
            "agent_decision": format_agent_action(
                case.action_type,
                message=case.agent_message,
                vote=case.agent_vote,
            ),
            "updated_strategy": case.updated_strategy,
            "judge_scores": scores.model_dump(mode="json") if scores else None,
            "judge_model": config.judge_model,
        }
        write_jsonl(out_path, result_record)
        written += 1

        if scores:
            print(
                f"  Scores: summary={scores.summary_quality} "
                f"retrieval={scores.retrieval_relevance} "
                f"application={scores.strategy_application} "
                f"grounding={scores.grounding}",
                flush=True,
            )
        time.sleep(config.sleep_seconds)

    print(f"Done. Wrote {written} records to {out_path}", flush=True)


if __name__ == "__main__":
    main()

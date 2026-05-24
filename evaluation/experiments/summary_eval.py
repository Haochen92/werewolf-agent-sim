"""Evaluate situation summaries with a rubric-based judge.

Supports two modes:

- **captured**: Judge the frozen situations already in the EvalCase.
- **replay**: Regenerate situations with a different model/config, then judge.

Usage::

    # Judge captured situations
    poetry run python -m evaluation.experiments.summary_eval \\
        --config eval_configs/summary/captured.json

    # Replay with a different model, then judge
    poetry run python -m evaluation.experiments.summary_eval \\
        --config eval_configs/summary/replay_flash35.json
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from evaluation.components.situation_summary import run_situation_summary_variant
from evaluation.core.config_schema import SummaryExperimentConfig
from evaluation.core.io import write_jsonl
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.data.datasets import read_eval_dataset
from evaluation.judges.summary import run_summary_judge

load_project_env()

DIMS = ["faithfulness", "specificity", "retrieval_usefulness", "non_redundancy", "role_perspective"]


def output_path(requested: Path | None) -> Path:
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"summary_eval_{timestamp}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate situation summaries with a rubric-based judge."
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def read_config(path: Path) -> SummaryExperimentConfig:
    return SummaryExperimentConfig.model_validate_json(
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
    print(f"Mode: {config.mode}", flush=True)
    if config.mode == "replay" and config.variant:
        print(f"Variant: {config.variant.label} ({config.variant.model})", flush=True)
    print(f"Judge: {config.judge_model}", flush=True)
    print(f"Output: {out_path}", flush=True)
    print("", flush=True)

    score_totals: dict[str, float] = {d: 0.0 for d in DIMS}
    written = 0

    for index, record in enumerate(records, 1):
        case = record.eval_case
        print(
            f"[{index}/{len(records)}] {record.case_id} "
            f"role={case.player_role} action={case.action_phase}",
            flush=True,
        )

        replay_output: dict[str, Any] | None = None
        if config.mode == "replay" and config.variant:
            try:
                replay_output = run_situation_summary_variant(case, config.variant)
                situations = replay_output["situations"]
                print(
                    f"  Replay: {len(situations)} situations, "
                    f"{replay_output['latency_ms']}ms",
                    flush=True,
                )
            except Exception as exc:
                print(f"  Replay error: {exc}", flush=True)
                write_jsonl(out_path, {
                    "eval_set_id": record.eval_set_id,
                    "case_id": record.case_id,
                    "error": str(exc),
                })
                written += 1
                continue
        else:
            situations = list(case.situations)

        scores = None
        if config.judge:
            scores = run_summary_judge(
                case, situations, model=config.judge_model,
            )

        result_record: dict[str, Any] = {
            "eval_set_id": record.eval_set_id,
            "case_id": record.case_id,
            "trace_id": record.trace_id,
            "observation_id": record.observation_id,
            "span_name": record.span_name,
            "role": case.player_role,
            "day": case.day,
            "round": case.round,
            "action_phase": case.action_phase,
            "mode": config.mode,
            "situation_count": len(situations),
            "situations": situations,
            "summary_scores": scores.model_dump(mode="json") if scores else None,
            "judge_model": config.judge_model if config.judge else None,
        }
        if config.mode == "replay" and config.variant:
            result_record["variant"] = config.variant.label
            result_record["variant_model"] = config.variant.model
        if replay_output:
            result_record["latency_ms"] = replay_output.get("latency_ms")
            result_record["cost"] = replay_output.get("cost")

        write_jsonl(out_path, result_record)
        written += 1

        if scores:
            print(
                f"  Scores: faith={scores.faithfulness} "
                f"spec={scores.specificity} retr={scores.retrieval_usefulness} "
                f"nred={scores.non_redundancy} role={scores.role_perspective}",
                flush=True,
            )
            for d in DIMS:
                score_totals[d] += getattr(scores, d)

        if config.judge:
            time.sleep(config.sleep_seconds)

    print(f"\nDone. Wrote {written} records to {out_path}", flush=True)
    if written and config.judge:
        print("Averages:", flush=True)
        for d in DIMS:
            print(f"  {d}: {score_totals[d] / written:.2f}", flush=True)


if __name__ == "__main__":
    main()

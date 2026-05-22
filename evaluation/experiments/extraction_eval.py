"""Score captured ExtractionCase records using an LLM judge."""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path

from evaluation.core.config_schema import ExtractionExperimentConfig
from evaluation.core.io import write_jsonl
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.data.datasets import read_extraction_dataset
from evaluation.judges.extraction import run_extraction_judge

load_project_env()


def output_path(requested: Path | None) -> Path:
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"extraction_eval_{timestamp}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Judge captured extraction cases."
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def read_config(path: Path) -> ExtractionExperimentConfig:
    return ExtractionExperimentConfig.model_validate_json(
        path.read_text(encoding="utf-8")
    )


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    records = read_extraction_dataset(config.dataset)
    if config.max_samples:
        records = records[: config.max_samples]
    out_path = output_path(config.output)

    print(
        f"Loaded {len(records)} extraction records from {config.dataset}",
        flush=True,
    )
    print(f"Judge model={config.judge_model}", flush=True)
    print(f"Writing results to {out_path}", flush=True)

    written = 0
    score_totals: dict[str, float] = {}
    for index, record in enumerate(records, 1):
        case = record.extraction_case
        print(
            f"[{index}/{len(records)}] {record.case_id} "
            f"game={case.game_id} outcome={case.game_outcome} "
            f"obs={len(case.observations)} sp={len(case.strategy_points)}",
            flush=True,
        )

        scores = None
        if config.judge:
            scores = run_extraction_judge(case, model=config.judge_model)

        result_record = {
            "eval_set_id": record.eval_set_id,
            "case_id": record.case_id,
            "trace_id": record.trace_id,
            "observation_id": record.observation_id,
            "span_name": record.span_name,
            "game_id": case.game_id,
            "game_outcome": case.game_outcome,
            "model_used": case.model_used,
            "observation_count": len(case.observations),
            "strategy_point_count": len(case.strategy_points),
            "source_dataset": str(config.dataset),
            "judge_scores": scores.model_dump(mode="json") if scores else None,
            "judge_model": config.judge_model,
        }
        write_jsonl(out_path, result_record)
        written += 1

        if scores:
            print(
                f"  Scores: specificity={scores.specificity} "
                f"epistemic={scores.epistemic_compliance} "
                f"grounding={scores.grounding} "
                f"coverage={scores.coverage} "
                f"diversity={scores.diversity}",
                flush=True,
            )
            for dim in (
                "specificity",
                "epistemic_compliance",
                "grounding",
                "coverage",
                "diversity",
            ):
                score_totals[dim] = score_totals.get(dim, 0) + getattr(scores, dim)

        time.sleep(config.sleep_seconds)

    print(f"\nDone. Wrote {written} records to {out_path}", flush=True)
    if score_totals and written:
        print("Averages:", flush=True)
        for dim, total in score_totals.items():
            print(f"  {dim}: {total / written:.2f}", flush=True)


if __name__ == "__main__":
    main()

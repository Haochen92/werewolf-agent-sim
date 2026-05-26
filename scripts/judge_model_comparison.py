"""Judge extraction outputs from model comparison using a specified judge model."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from Agents.schemas.evaluation import ExtractionCase
from evaluation.data.datasets import read_extraction_dataset
from evaluation.judges.extraction import run_extraction_judge

REPO_ROOT = Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) < 3:
        print("Usage: judge_model_comparison.py <judge_model> <extraction_jsonl> [extraction_jsonl2 ...]")
        sys.exit(1)

    judge_model = sys.argv[1]
    extraction_files = [Path(p) for p in sys.argv[2:]]

    # Load original dataset for game inputs (discussions, roles, etc.)
    dataset_path = REPO_ROOT / "eval_sets" / "extraction_v1.jsonl"
    original_records = read_extraction_dataset(dataset_path)
    game_inputs = {}
    for record in original_records:
        case = record.extraction_case
        game_inputs[case.game_id] = case

    # Load all extraction results
    extraction_results = []
    for filepath in extraction_files:
        with filepath.open() as f:
            for line in f:
                extraction_results.append(json.loads(line))

    print(f"Judge model: {judge_model}", flush=True)
    print(f"Extraction files: {[f.name for f in extraction_files]}", flush=True)
    print(f"Total cases to judge: {len(extraction_results)}", flush=True)
    print("", flush=True)

    # Output file
    out_dir = REPO_ROOT / "evidence" / "extraction_quality" / "model_comparison"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"judge_{judge_model}_{timestamp}.jsonl"

    score_totals: dict[str, dict[str, float]] = {}
    score_counts: dict[str, int] = {}

    for i, result in enumerate(extraction_results, 1):
        game_id = result["game_id"]
        model_used = result["model"]
        original = game_inputs.get(game_id)

        if not original:
            print(f"[{i}/{len(extraction_results)}] SKIP - no original inputs for game={game_id[:8]}", flush=True)
            continue

        # Build ExtractionCase with new model's outputs but original inputs
        case = ExtractionCase(
            game_id=game_id,
            game_outcome=result["game_outcome"],
            roles=original.roles,
            formatted_discussions=original.formatted_discussions,
            formatted_strategy_notes=original.formatted_strategy_notes,
            observations=result["observations"],
            strategy_points=result["strategy_points"],
            model_used=model_used,
        )

        scores = run_extraction_judge(case, model=judge_model)

        if scores:
            print(
                f"[{i}/{len(extraction_results)}] {model_used:>25} game={game_id[:8]} "
                f"obs={len(case.observations)} sp={len(case.strategy_points)} | "
                f"spec={scores.specificity} epist={scores.epistemic_compliance} "
                f"ground={scores.grounding} cov={scores.coverage} div={scores.diversity} "
                f"persp={scores.perspective_compliance}",
                flush=True,
            )
            if model_used not in score_totals:
                score_totals[model_used] = {}
                score_counts[model_used] = 0
            score_counts[model_used] += 1
            for dim in ("specificity", "epistemic_compliance", "grounding", "coverage", "diversity", "perspective_compliance"):
                score_totals[model_used][dim] = score_totals[model_used].get(dim, 0) + getattr(scores, dim)
        else:
            print(f"[{i}/{len(extraction_results)}] {model_used:>25} game={game_id[:8]} JUDGE FAILED", flush=True)

        record = {
            "game_id": game_id,
            "extraction_model": model_used,
            "judge_model": judge_model,
            "observation_count": len(case.observations),
            "strategy_point_count": len(case.strategy_points),
            "judge_scores": scores.model_dump(mode="json") if scores else None,
        }
        with out_file.open("a") as f:
            f.write(json.dumps(record) + "\n")

        time.sleep(1.0)

    # Summary per model
    print(f"\n{'='*60}", flush=True)
    print(f"SUMMARY (judge={judge_model})", flush=True)
    print(f"{'='*60}", flush=True)
    for model_key in sorted(score_totals.keys()):
        n = score_counts[model_key]
        avgs = {dim: total / n for dim, total in score_totals[model_key].items()}
        print(f"\n{model_key} ({n} games):", flush=True)
        for dim, avg in avgs.items():
            print(f"  {dim}: {avg:.2f}", flush=True)

    print(f"\nResults saved to {out_file}", flush=True)


if __name__ == "__main__":
    main()

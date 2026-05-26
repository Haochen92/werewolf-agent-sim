"""Judge extraction outputs per-role using the per-role extraction judge."""

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
from evaluation.judges.per_role_extraction import run_per_role_extraction_judge

REPO_ROOT = Path(__file__).resolve().parent.parent
DIMS = [
    "specificity", "epistemic_compliance", "grounding", "coverage",
    "diversity", "perspective_compliance", "strategy_depth", "novelty",
]


def main():
    if len(sys.argv) < 3:
        print("Usage: per_role_judge.py <judge_model> <extraction_jsonl> [extraction_jsonl2 ...]")
        sys.exit(1)

    judge_model = sys.argv[1]
    extraction_files = [Path(p) for p in sys.argv[2:]]

    dataset_path = REPO_ROOT / "eval_sets" / "extraction_v1.jsonl"
    original_records = read_extraction_dataset(dataset_path)
    game_inputs = {}
    for record in original_records:
        case = record.extraction_case
        game_inputs[case.game_id] = case

    extraction_results = []
    for filepath in extraction_files:
        with filepath.open() as f:
            for line in f:
                extraction_results.append(json.loads(line))

    print(f"Judge model: {judge_model}", flush=True)
    print(f"Extraction files: {[f.name for f in extraction_files]}", flush=True)
    print(f"Total cases to judge: {len(extraction_results)}", flush=True)
    print("", flush=True)

    out_dir = REPO_ROOT / "evidence" / "extraction_quality" / "model_comparison"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"per_role_judge_{judge_model}_{timestamp}.jsonl"

    # Accumulators: model -> role -> dim -> total
    role_totals: dict[str, dict[str, dict[str, float]]] = {}
    role_counts: dict[str, dict[str, int]] = {}

    for i, result in enumerate(extraction_results, 1):
        game_id = result["game_id"]
        model_used = result["model"]
        mode = result.get("mode", "single-pass")
        original = game_inputs.get(game_id)

        if not original:
            print(f"[{i}/{len(extraction_results)}] SKIP - no inputs for game={game_id[:8]}", flush=True)
            continue

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

        per_role_scores = run_per_role_extraction_judge(case, model=judge_model)

        model_key = f"{model_used} {mode}"
        if model_key not in role_totals:
            role_totals[model_key] = {}
            role_counts[model_key] = {}

        role_scores_out = {}
        role_counts_out = {}
        for rr in per_role_scores.role_results:
            role_counts_out[rr.role] = {
                "observations": rr.observation_count,
                "strategy_points": rr.strategy_point_count,
            }
            if rr.scores:
                scores_dict = {d: getattr(rr.scores, d) for d in DIMS}
                role_scores_out[rr.role] = scores_dict
                dim_str = " ".join(f"{d[:4]}={scores_dict[d]}" for d in DIMS)
                print(
                    f"[{i}/{len(extraction_results)}] {model_used} game={game_id[:8]} "
                    f"role={rr.role:12s} obs={rr.observation_count} sp={rr.strategy_point_count} | {dim_str}",
                    flush=True,
                )
                if rr.role not in role_totals[model_key]:
                    role_totals[model_key][rr.role] = {}
                    role_counts[model_key][rr.role] = 0
                role_counts[model_key][rr.role] += 1
                for d in DIMS:
                    role_totals[model_key][rr.role][d] = (
                        role_totals[model_key][rr.role].get(d, 0) + scores_dict[d]
                    )
            else:
                print(
                    f"[{i}/{len(extraction_results)}] {model_used} game={game_id[:8]} "
                    f"role={rr.role:12s} JUDGE FAILED",
                    flush=True,
                )

        record = {
            "game_id": game_id,
            "extraction_model": model_used,
            "extraction_mode": mode,
            "judge_model": judge_model,
            "role_scores": role_scores_out,
            "role_item_counts": role_counts_out,
            "aggregate_scores": per_role_scores.aggregate,
        }
        with out_file.open("a") as f:
            f.write(json.dumps(record) + "\n")

        time.sleep(1.0)

    # Summary
    print(f"\n{'='*80}", flush=True)
    print(f"SUMMARY (judge={judge_model})", flush=True)
    print(f"{'='*80}", flush=True)

    for model_key in sorted(role_totals.keys()):
        print(f"\n{model_key}:", flush=True)
        overall_totals: dict[str, float] = {}
        overall_n = 0
        for role in ["wolf", "villager", "healer", "investigator"]:
            if role not in role_totals[model_key]:
                continue
            n = role_counts[model_key][role]
            avgs = {d: role_totals[model_key][role][d] / n for d in DIMS}
            dims_str = " ".join(f"{d[:4]}={avgs[d]:.2f}" for d in DIMS)
            print(f"  {role:12s} (n={n}): {dims_str}", flush=True)
            for d in DIMS:
                overall_totals[d] = overall_totals.get(d, 0) + role_totals[model_key][role][d]
            overall_n += n
        if overall_n:
            overall_avgs = {d: overall_totals[d] / overall_n for d in DIMS}
            dims_str = " ".join(f"{d[:4]}={overall_avgs[d]:.2f}" for d in DIMS)
            print(f"  {'OVERALL':12s} (n={overall_n}): {dims_str}", flush=True)

    print(f"\nResults saved to {out_file}", flush=True)


if __name__ == "__main__":
    main()

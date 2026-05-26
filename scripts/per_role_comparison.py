"""Pairwise per-role comparison of extraction outputs."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from itertools import combinations
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from Agents.schemas.evaluation import ExtractionCase
from evaluation.data.datasets import read_extraction_dataset
from evaluation.judges.per_role_extraction import filter_items_by_role
from evaluation.judges.pairwise_extraction import run_pairwise_extraction_judge

REPO_ROOT = Path(__file__).resolve().parent.parent
ROLES = ["wolf", "villager", "healer", "investigator"]
DIMS = [
    "specificity", "epistemic_compliance", "grounding", "coverage",
    "diversity", "perspective_compliance", "strategy_depth", "novelty",
]


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: per_role_comparison.py <judge_model> "
            "<extraction_jsonl_A> <extraction_jsonl_B> [extraction_jsonl_C ...]"
        )
        sys.exit(1)

    judge_model = sys.argv[1]
    extraction_files = [Path(p) for p in sys.argv[2:]]

    dataset_path = REPO_ROOT / "eval_sets" / "extraction_v1.jsonl"
    original_records = read_extraction_dataset(dataset_path)
    game_inputs = {}
    for record in original_records:
        case = record.extraction_case
        game_inputs[case.game_id] = case

    # Load extraction results indexed by (model_label, game_id)
    model_results: dict[str, dict[str, dict]] = {}
    model_labels: list[str] = []
    for filepath in extraction_files:
        with filepath.open() as f:
            for line in f:
                d = json.loads(line)
                mode = d.get("mode", "single-pass")
                label = f"{d['model']} {mode}"
                if label not in model_results:
                    model_results[label] = {}
                    model_labels.append(label)
                model_results[label][d["game_id"]] = d

    # Find common games
    game_sets = [set(v.keys()) for v in model_results.values()]
    common_games = sorted(set.intersection(*game_sets)) if game_sets else []

    pairs = list(combinations(model_labels, 2))

    print(f"Judge model: {judge_model}", flush=True)
    print(f"Models: {model_labels}", flush=True)
    print(f"Common games: {len(common_games)}", flush=True)
    print(f"Pairs: {len(pairs)}", flush=True)
    print(f"Total comparisons: {len(common_games)} games x {len(ROLES)} roles x {len(pairs)} pairs = {len(common_games)*len(ROLES)*len(pairs)}", flush=True)
    print("", flush=True)

    out_dir = REPO_ROOT / "evidence" / "extraction_quality" / "model_comparison"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"comparison_{judge_model}_{timestamp}.jsonl"

    # Track wins: model_label -> role -> wins
    wins: dict[str, dict[str, int]] = {m: {r: 0 for r in ROLES} for m in model_labels}
    ties: dict[str, dict[str, int]] = {m: {r: 0 for r in ROLES} for m in model_labels}
    total_matchups: dict[str, dict[str, int]] = {m: {r: 0 for r in ROLES} for m in model_labels}

    case_num = 0
    total_cases = len(common_games) * len(ROLES) * len(pairs)

    for game_id in common_games:
        original = game_inputs.get(game_id)
        if not original:
            print(f"SKIP game={game_id[:8]} - no original inputs", flush=True)
            continue

        case = ExtractionCase(
            game_id=game_id,
            game_outcome=original.game_outcome,
            roles=original.roles,
            formatted_discussions=original.formatted_discussions,
            formatted_strategy_notes=original.formatted_strategy_notes,
            observations=[],
            strategy_points=[],
            model_used="",
        )

        for role in ROLES:
            for label_a, label_b in pairs:
                case_num += 1
                result_a = model_results[label_a][game_id]
                result_b = model_results[label_b][game_id]

                obs_a = filter_items_by_role(result_a["observations"], role)
                sp_a = filter_items_by_role(result_a["strategy_points"], role)
                obs_b = filter_items_by_role(result_b["observations"], role)
                sp_b = filter_items_by_role(result_b["strategy_points"], role)

                if not (obs_a or sp_a) and not (obs_b or sp_b):
                    continue

                scores = run_pairwise_extraction_judge(
                    case,
                    items_a=(obs_a, sp_a),
                    items_b=(obs_b, sp_b),
                    label_a=label_a,
                    label_b=label_b,
                    role=role,
                    model=judge_model,
                )

                if scores:
                    winner_label = (
                        label_a if scores.winner == "a"
                        else label_b if scores.winner == "b"
                        else "tie"
                    )
                    print(
                        f"[{case_num}/{total_cases}] game={game_id[:8]} role={role:12s} "
                        f"{label_a} vs {label_b} → winner={winner_label} conf={scores.confidence}",
                        flush=True,
                    )
                    for label in [label_a, label_b]:
                        total_matchups[label][role] += 1
                    if scores.winner == "a":
                        wins[label_a][role] += 1
                    elif scores.winner == "b":
                        wins[label_b][role] += 1
                    else:
                        ties[label_a][role] += 1
                        ties[label_b][role] += 1

                    record = {
                        "game_id": game_id,
                        "role": role,
                        "model_a": label_a,
                        "model_b": label_b,
                        "judge_model": judge_model,
                        "scores_a": scores.output_a.model_dump(mode="json"),
                        "scores_b": scores.output_b.model_dump(mode="json"),
                        "winner": scores.winner,
                        "confidence": scores.confidence,
                        "brief_reasoning": scores.brief_reasoning,
                    }
                    with out_file.open("a") as f:
                        f.write(json.dumps(record) + "\n")
                else:
                    print(
                        f"[{case_num}/{total_cases}] game={game_id[:8]} role={role:12s} "
                        f"{label_a} vs {label_b} → JUDGE FAILED",
                        flush=True,
                    )

                time.sleep(1.0)

    # Summary
    print(f"\n{'='*80}", flush=True)
    print(f"RANKING (judge={judge_model})", flush=True)
    print(f"{'='*80}", flush=True)

    for label in model_labels:
        print(f"\n{label}:", flush=True)
        total_w, total_t, total_m = 0, 0, 0
        for role in ROLES:
            m = total_matchups[label][role]
            if m == 0:
                continue
            w = wins[label][role]
            t = ties[label][role]
            pct = (w + 0.5 * t) / m * 100
            print(f"  {role:12s}: {w}W {t}T {m-w-t}L ({pct:.0f}%)", flush=True)
            total_w += w
            total_t += t
            total_m += m
        if total_m:
            pct = (total_w + 0.5 * total_t) / total_m * 100
            print(f"  {'OVERALL':12s}: {total_w}W {total_t}T {total_m-total_w-total_t}L ({pct:.0f}%)", flush=True)

    print(f"\nResults saved to {out_file}", flush=True)


if __name__ == "__main__":
    main()

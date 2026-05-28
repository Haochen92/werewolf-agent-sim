"""Pairwise quality comparison of captured vs regenerated situation summaries.

Uses the existing pairwise summary judge to score old-captured (v1 prompt)
against regenerated (v2 prompt with core dilemma) situations on 5 quality
dimensions: faithfulness, specificity, retrieval_usefulness, non_redundancy,
role_perspective.

Usage::

    # Compare captured vs flash-lite regenerated
    poetry run python -m evaluation.experiments.labeling.situation_quality_judge

    # Use a specific regenerated file (e.g. pro output)
    poetry run python -m evaluation.experiments.labeling.situation_quality_judge \
        --regen-file evidence/extraction/situation_summary/regenerated_situations_pro.json

    # Filter by role
    poetry run python -m evaluation.experiments.labeling.situation_quality_judge \
        --role wolf
"""

from __future__ import annotations

import argparse
import json
import random
import time
from collections import defaultdict
from pathlib import Path

from evaluation.core.settings import REPO_ROOT, load_project_env

load_project_env()

EVAL_DATASET = REPO_ROOT / "eval_sets" / "v4_filtering_eval.jsonl"
DEFAULT_REGEN = (
    REPO_ROOT
    / "evidence"
    / "extraction"
    / "situation_summary"
    / "regenerated_situations.json"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pairwise quality judge: captured vs regenerated situations."
    )
    parser.add_argument(
        "--regen-file",
        type=Path,
        default=DEFAULT_REGEN,
        help="Path to regenerated situations JSON",
    )
    parser.add_argument("--role", type=str, help="Filter to a specific role")
    parser.add_argument("--phase", type=str, help="Filter to a specific phase")
    parser.add_argument(
        "--judge-model",
        type=str,
        default="gemini-2.5-pro",
        help="Model for pairwise judge",
    )
    parser.add_argument(
        "--save-results",
        type=Path,
        help="Save detailed results to JSON file",
    )
    args = parser.parse_args()

    from evaluation.core.config_schema import JudgeConfig
    from evaluation.data.datasets import read_eval_dataset
    from evaluation.judges.pairwise_summary import run_pairwise_summary_judge

    records = read_eval_dataset(EVAL_DATASET)

    with open(args.regen_file) as f:
        regen_data = json.load(f)

    if args.role:
        regen_data = [r for r in regen_data if r["role"] == args.role]
    if args.phase:
        regen_data = [r for r in regen_data if r["phase"] == args.phase]

    if not regen_data:
        print("No cases match the filters.")
        return

    judge_config = JudgeConfig(model=args.judge_model, temperature=0.0)

    print(f"Judging {len(regen_data)} cases: captured (v1) vs regenerated (v2)")
    print(f"Judge model: {args.judge_model}")
    print(f"Regen file: {args.regen_file.name}")
    print(flush=True)

    results = []
    wins = {"captured": 0, "regenerated": 0, "tie": 0}
    dim_scores: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )
    role_wins: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    for entry in sorted(regen_data, key=lambda x: x["case_index"]):
        idx = entry["case_index"]
        role = entry["role"]
        phase = entry["phase"]
        record = records[idx]
        case = record.eval_case

        captured_situations = list(case.situations)
        regen_situations = entry["new_situations"]

        output_captured = {"label": "captured_v1", "situations": captured_situations}
        output_regen = {"label": "regenerated_v2", "situations": regen_situations}

        swapped = random.random() < 0.5
        if swapped:
            output_a, output_b = output_regen, output_captured
        else:
            output_a, output_b = output_captured, output_regen

        print(f"  Case {idx:2d} ({role}/{phase})...", end=" ", flush=True)
        start = time.time()
        try:
            scores, cost_info = run_pairwise_summary_judge(
                record, output_a, output_b, judge_config
            )
        except Exception as e:
            print(f"FAILED: {e}")
            continue
        elapsed = time.time() - start

        if swapped:
            winner_raw = scores.winner
            if winner_raw == "a":
                winner = "regenerated"
            elif winner_raw == "b":
                winner = "captured"
            else:
                winner = "tie"
            cap_scores = scores.output_b
            reg_scores = scores.output_a
        else:
            winner_raw = scores.winner
            if winner_raw == "a":
                winner = "captured"
            elif winner_raw == "b":
                winner = "regenerated"
            else:
                winner = "tie"
            cap_scores = scores.output_a
            reg_scores = scores.output_b

        wins[winner] += 1
        role_wins[role][winner] += 1

        for dim in ["faithfulness", "specificity", "retrieval_usefulness", "non_redundancy", "role_perspective"]:
            dim_scores[dim]["captured"].append(getattr(cap_scores, dim))
            dim_scores[dim]["regenerated"].append(getattr(reg_scores, dim))

        print(
            f"winner={winner:12s}  conf={scores.confidence}  "
            f"({elapsed:.1f}s)"
        )

        results.append({
            "case_index": idx,
            "role": role,
            "phase": phase,
            "winner": winner,
            "confidence": scores.confidence,
            "swapped": swapped,
            "captured_scores": cap_scores.model_dump(mode="json"),
            "regenerated_scores": reg_scores.model_dump(mode="json"),
            "reasoning": scores.brief_reasoning,
        })

    print()
    print("=" * 60)
    total = sum(wins.values())
    print(f"Results ({total} cases):")
    print(f"  Captured (v1) wins:    {wins['captured']:2d}  ({wins['captured']/total*100:.0f}%)")
    print(f"  Regenerated (v2) wins: {wins['regenerated']:2d}  ({wins['regenerated']/total*100:.0f}%)")
    print(f"  Ties:                  {wins['tie']:2d}  ({wins['tie']/total*100:.0f}%)")

    print()
    print("Per-dimension mean scores:")
    print(f"  {'Dimension':<22s}  {'Captured':>9s}  {'Regen':>9s}  {'Delta':>7s}")
    print(f"  {'-'*22}  {'-'*9}  {'-'*9}  {'-'*7}")
    for dim in ["faithfulness", "specificity", "retrieval_usefulness", "non_redundancy", "role_perspective"]:
        cap_mean = sum(dim_scores[dim]["captured"]) / len(dim_scores[dim]["captured"])
        reg_mean = sum(dim_scores[dim]["regenerated"]) / len(dim_scores[dim]["regenerated"])
        delta = reg_mean - cap_mean
        print(f"  {dim:<22s}  {cap_mean:9.2f}  {reg_mean:9.2f}  {delta:+7.2f}")

    print()
    print("Per-role wins:")
    for role in sorted(role_wins.keys()):
        rw = role_wins[role]
        n = sum(rw.values())
        print(
            f"  {role:>13s}: captured={rw['captured']}  regen={rw['regenerated']}  "
            f"tie={rw['tie']}  (n={n})"
        )

    if args.save_results:
        output = {
            "judge_model": args.judge_model,
            "regen_file": str(args.regen_file),
            "summary": {
                "total": total,
                "captured_wins": wins["captured"],
                "regenerated_wins": wins["regenerated"],
                "ties": wins["tie"],
            },
            "cases": results,
        }
        args.save_results.parent.mkdir(parents=True, exist_ok=True)
        with open(args.save_results, "w") as f:
            json.dump(output, f, indent=2)
            f.write("\n")
        print(f"\nSaved results to {args.save_results}")


if __name__ == "__main__":
    main()

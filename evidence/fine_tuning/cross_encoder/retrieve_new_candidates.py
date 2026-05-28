"""Retrieve candidates for new eval cases using golden situations.

Runs embedding-based retrieval against the v4_deduped_v2 memory store
for cases that have golden situations but no relevance labels yet.
Outputs a JSON file with retrieved candidates ready for labeling.

Usage:
    poetry run python evidence/fine_tuning/cross_encoder/retrieve_new_candidates.py \
        --situations-file /tmp/new_golden_situations.json \
        --output evidence/fine_tuning/cross_encoder/candidates_for_labeling.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EVAL_DATASET = REPO_ROOT / "eval_sets" / "v4_filtering_eval.jsonl"
STORE_DIR = REPO_ROOT / "Agents" / "memory_stores" / "v4_deduped_v2"
GOLDEN_LABELS_PATH = (
    REPO_ROOT / "evidence" / "extraction" / "situation_summary"
    / "retrieval_golden_labels.json"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--situations-file", type=Path, required=True,
        help="JSON file with golden situations per case",
    )
    parser.add_argument(
        "--output", type=Path,
        default=REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "candidates_for_labeling.json",
    )
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    with open(args.situations_file) as f:
        situations_data = json.load(f)

    case_situations = {
        c["case_index"]: c["golden_situations"]
        for c in situations_data["cases"]
    }
    print(f"Loaded golden situations for {len(case_situations)} cases")

    from evaluation.data.datasets import read_eval_dataset
    records = read_eval_dataset(EVAL_DATASET)
    print(f"Loaded {len(records)} eval records")

    from Agents.memory import store
    from Agents.memory_persistence import seed_memory_from_json_files_cached

    seed_memory_from_json_files_cached(
        observations_path=STORE_DIR / "observations.json",
        strategy_points_path=STORE_DIR / "strategy_points.json",
        target_store=store,
        cache_dir=STORE_DIR,
    )
    print("Memory store seeded")

    from Agents.memory import (
        retrieve_observations_for_agent,
        retrieve_strategy_points_for_agent,
    )

    results = []
    total_obs = 0
    total_sp = 0

    for case_idx in sorted(case_situations.keys()):
        golden_sits = case_situations[case_idx]
        record = records[case_idx]
        case = record.eval_case

        observations = retrieve_observations_for_agent(
            store=store,
            role=case.player_role,
            action_phase=case.action_phase,
            situations=golden_sits,
            top_k=args.top_k,
        )
        observations.sort(key=lambda x: x.score or 0, reverse=True)

        strategy_points = retrieve_strategy_points_for_agent(
            store=store,
            role=case.player_role,
            action_phase=case.action_phase,
            situations=golden_sits,
            top_k=args.top_k,
        )
        strategy_points.sort(key=lambda x: x.score or 0, reverse=True)

        obs_items = []
        for item in observations:
            obs = item.observation
            obs_items.append({
                "key": item.key,
                "score": round(item.score, 4) if item.score else 0.0,
                "situation": obs.situation,
                "approach": obs.approach or "",
                "outcome": obs.outcome or "",
            })

        sp_items = []
        for item in strategy_points:
            sp = item.strategy_point
            sp_items.append({
                "key": item.key,
                "score": round(item.score, 4) if item.score else 0.0,
                "situation": sp.situation,
                "action": sp.action,
            })

        results.append({
            "case_index": case_idx,
            "case_id": record.case_id,
            "player_role": case.player_role,
            "day": case.day,
            "round": case.round,
            "action_phase": case.action_phase,
            "golden_situations": golden_sits,
            "retrieved_observations": obs_items,
            "retrieved_strategy_points": sp_items,
        })

        total_obs += len(obs_items)
        total_sp += len(sp_items)
        print(f"  Case {case_idx:2d} ({case.player_role:>13} {case.action_phase}): "
              f"{len(obs_items)} obs + {len(sp_items)} sp")

    output = {
        "description": "Retrieved candidates for consensus labeling",
        "top_k": args.top_k,
        "store": "v4_deduped_v2",
        "cases": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")

    print(f"\nTotal: {total_obs} observations + {total_sp} strategy points = {total_obs + total_sp} items")
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()

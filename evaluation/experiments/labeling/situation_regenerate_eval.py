"""Regenerate situation summaries with the current prompt and compare retrieval.

Runs the situation summary pipeline on labeled eval cases, retrieves memories
using the new situations, and computes NDCG against golden relevance labels.
Compares golden, old-captured, and new-regenerated situations side by side.

Usage::

    # Regenerate for all 20 labeled cases
    poetry run python -m evaluation.experiments.labeling.situation_regenerate_eval

    # Filter by role
    poetry run python -m evaluation.experiments.labeling.situation_regenerate_eval \
        --role wolf

    # Save generated situations to file for later analysis
    poetry run python -m evaluation.experiments.labeling.situation_regenerate_eval \
        --save-situations evidence/extraction/situation_summary/regenerated_situations.json
"""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import defaultdict
from pathlib import Path

from evaluation.core.settings import REPO_ROOT, load_project_env

load_project_env()

GOLDEN_LABELS_PATH = (
    REPO_ROOT
    / "evidence"
    / "extraction"
    / "situation_summary"
    / "retrieval_golden_labels.json"
)
STORE_DIR = REPO_ROOT / "Agents" / "memory_stores" / "v4_deduped_v2"
EVAL_DATASET = REPO_ROOT / "eval_sets" / "v4_filtering_eval.jsonl"


def dcg_at_k(relevances: list[int], k: int) -> float:
    score = 0.0
    for i, rel in enumerate(relevances[:k]):
        score += rel / math.log2(i + 2)
    return score


def ndcg_at_k(relevances: list[int], k: int) -> float:
    actual = dcg_at_k(relevances, k)
    ideal = dcg_at_k(sorted(relevances, reverse=True), k)
    if ideal == 0:
        return 1.0
    return actual / ideal


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate situations and compare retrieval NDCG."
    )
    parser.add_argument("--role", type=str, help="Filter to a specific role")
    parser.add_argument("--phase", type=str, help="Filter to a specific phase")
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-3.1-flash-lite",
        help="Model for situation generation",
    )
    parser.add_argument(
        "--thinking-level",
        type=str,
        default="medium",
        help="Thinking level for generation",
    )
    parser.add_argument(
        "--save-situations",
        type=Path,
        help="Save generated situations to JSON file",
    )
    parser.add_argument(
        "--k",
        type=int,
        nargs="+",
        default=[3, 5, 10],
    )
    args = parser.parse_args()

    from Agents.memory import store as memory_store
    from Agents.memory import (
        retrieve_observations_for_agent,
        retrieve_strategy_points_for_agent,
    )
    from Agents.memory_persistence import seed_memory_from_json_files_cached
    from evaluation.components.situation_summary import run_situation_summary_variant
    from evaluation.core.config_schema import VariantConfig
    from evaluation.data.datasets import read_eval_dataset

    print("Loading store from cache...", flush=True)
    seed_memory_from_json_files_cached(
        observations_path=STORE_DIR / "observations.json",
        strategy_points_path=STORE_DIR / "strategy_points.json",
        target_store=memory_store,
        cache_dir=STORE_DIR,
    )

    with open(GOLDEN_LABELS_PATH) as f:
        data = json.load(f)

    labels_list = data["labels"]
    if args.role:
        labels_list = [l for l in labels_list if l["player_role"] == args.role]
    if args.phase:
        labels_list = [l for l in labels_list if l["action_phase"] == args.phase]

    if not labels_list:
        print("No labeled cases match the filters.")
        return

    records = read_eval_dataset(EVAL_DATASET)
    config = VariantConfig(
        label=f"{args.model}-regen",
        model=args.model,
        temperature=0.0,
        thinking_level=args.thinking_level,
    )
    ks = args.k

    print(f"Regenerating situations for {len(labels_list)} cases")
    print(f"Model: {args.model}, thinking: {args.thinking_level}")
    print(flush=True)

    results = []

    for entry in sorted(labels_list, key=lambda x: x["case_index"]):
        idx = entry["case_index"]
        role = entry["player_role"]
        phase = entry["action_phase"]
        record = records[idx]
        case = record.eval_case

        print(f"  Case {idx:2d} ({role}/{phase})...", end=" ", flush=True)

        start = time.time()
        try:
            gen_result = run_situation_summary_variant(case, config, max_retries=2)
        except Exception as e:
            print(f"FAILED: {e}")
            continue
        gen_time = time.time() - start
        new_situations = gen_result["situations"]
        print(f"{len(new_situations)} situations ({gen_time:.1f}s)", flush=True)

        obs_key_to_rel = {
            l["key"]: l["relevance"] for l in entry.get("observation_labels", [])
        }
        sp_key_to_rel = {
            l["key"]: l["relevance"] for l in entry.get("strategy_labels", [])
        }

        new_obs = retrieve_observations_for_agent(
            store=memory_store,
            role=role,
            action_phase=phase,
            situations=new_situations,
            top_k=10,
        )
        new_obs.sort(key=lambda x: x.score or 0, reverse=True)

        new_sp = retrieve_strategy_points_for_agent(
            store=memory_store,
            role=role,
            action_phase=phase,
            situations=new_situations,
            top_k=10,
        )
        new_sp.sort(key=lambda x: x.score or 0, reverse=True)

        new_labels = []
        unlabeled = 0
        for item in new_obs:
            rel = obs_key_to_rel.get(item.key, -1)
            if rel == -1:
                unlabeled += 1
                rel = 0
            new_labels.append({"key": item.key, "score": item.score, "relevance": rel})
        for item in new_sp:
            rel = sp_key_to_rel.get(item.key, -1)
            if rel == -1:
                unlabeled += 1
                rel = 0
            new_labels.append({"key": item.key, "score": item.score, "relevance": rel})

        new_labels.sort(key=lambda x: x.get("score", 0), reverse=True)
        new_relevances = [l["relevance"] for l in new_labels]

        golden_labels = entry.get("observation_labels", []) + entry.get("strategy_labels", [])
        golden_sorted = sorted(golden_labels, key=lambda x: x.get("score", 0), reverse=True)
        golden_relevances = [l["relevance"] for l in golden_sorted]

        captured = list(case.situations)
        cap_obs = retrieve_observations_for_agent(
            store=memory_store, role=role, action_phase=phase,
            situations=captured, top_k=10,
        )
        cap_obs.sort(key=lambda x: x.score or 0, reverse=True)
        cap_sp = retrieve_strategy_points_for_agent(
            store=memory_store, role=role, action_phase=phase,
            situations=captured, top_k=10,
        )
        cap_sp.sort(key=lambda x: x.score or 0, reverse=True)

        cap_labels = []
        cap_unlabeled = 0
        for item in cap_obs:
            rel = obs_key_to_rel.get(item.key, -1)
            if rel == -1:
                cap_unlabeled += 1
                rel = 0
            cap_labels.append({"key": item.key, "score": item.score, "relevance": rel})
        for item in cap_sp:
            rel = sp_key_to_rel.get(item.key, -1)
            if rel == -1:
                cap_unlabeled += 1
                rel = 0
            cap_labels.append({"key": item.key, "score": item.score, "relevance": rel})
        cap_labels.sort(key=lambda x: x.get("score", 0), reverse=True)
        cap_relevances = [l["relevance"] for l in cap_labels]

        result = {
            "case_index": idx,
            "role": role,
            "phase": phase,
            "new_situations": new_situations,
            "captured_situations": captured,
            "golden_ndcg": {k: ndcg_at_k(golden_relevances, k) for k in ks},
            "captured_ndcg": {k: ndcg_at_k(cap_relevances, k) for k in ks},
            "new_ndcg": {k: ndcg_at_k(new_relevances, k) for k in ks},
            "new_unlabeled": unlabeled,
            "cap_unlabeled": cap_unlabeled,
        }
        results.append(result)

    print()
    header = f"{'Case':>4}  {'Role':>13}  {'golden@5':>9}  {'old_cap@5':>9}  {'new@5':>9}  {'new-old':>8}  {'unlbl':>5}"
    print(header)
    print("-" * len(header))

    golden_5s = []
    old_5s = []
    new_5s = []
    by_role: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for r in results:
        g5 = r["golden_ndcg"][5]
        o5 = r["captured_ndcg"][5]
        n5 = r["new_ndcg"][5]
        delta = n5 - o5
        golden_5s.append(g5)
        old_5s.append(o5)
        new_5s.append(n5)
        by_role[r["role"]]["golden"].append(g5)
        by_role[r["role"]]["old"].append(o5)
        by_role[r["role"]]["new"].append(n5)
        print(
            f"{r['case_index']:4d}  {r['role']:>13}  {g5:9.4f}  {o5:9.4f}  {n5:9.4f}  {delta:+8.4f}  {r['new_unlabeled']:5d}"
        )

    print("-" * len(header))
    g_mean = sum(golden_5s) / len(golden_5s)
    o_mean = sum(old_5s) / len(old_5s)
    n_mean = sum(new_5s) / len(new_5s)
    print(
        f"MEAN  {'':>13}  {g_mean:9.4f}  {o_mean:9.4f}  {n_mean:9.4f}  {n_mean - o_mean:+8.4f}"
    )

    print()
    print("Per-role means:")
    for role in sorted(by_role.keys()):
        m = by_role[role]
        g = sum(m["golden"]) / len(m["golden"])
        o = sum(m["old"]) / len(m["old"])
        n = sum(m["new"]) / len(m["new"])
        print(
            f"  {role:>13}:  golden={g:.4f}  old_cap={o:.4f}  new={n:.4f}  "
            f"delta={n - o:+.4f}  (n={len(m['golden'])})"
        )

    # Low-unlabeled subset
    print()
    low_unlabeled = [r for r in results if r["new_unlabeled"] <= 4 and r["cap_unlabeled"] <= 4]
    if low_unlabeled:
        g_low = sum(r["golden_ndcg"][5] for r in low_unlabeled) / len(low_unlabeled)
        o_low = sum(r["captured_ndcg"][5] for r in low_unlabeled) / len(low_unlabeled)
        n_low = sum(r["new_ndcg"][5] for r in low_unlabeled) / len(low_unlabeled)
        cases = [str(r["case_index"]) for r in low_unlabeled]
        print(f"Clean subset (unlabeled<=4, n={len(low_unlabeled)}): cases [{', '.join(cases)}]")
        print(f"  golden={g_low:.4f}  old_cap={o_low:.4f}  new={n_low:.4f}  new-old={n_low - o_low:+.4f}")

    if args.save_situations:
        output = []
        for r in results:
            output.append({
                "case_index": r["case_index"],
                "role": r["role"],
                "phase": r["phase"],
                "new_situations": r["new_situations"],
                "captured_situations": r["captured_situations"],
                "golden_ndcg_5": r["golden_ndcg"][5],
                "captured_ndcg_5": r["captured_ndcg"][5],
                "new_ndcg_5": r["new_ndcg"][5],
                "new_unlabeled": r["new_unlabeled"],
            })
        args.save_situations.parent.mkdir(parents=True, exist_ok=True)
        with open(args.save_situations, "w") as f:
            json.dump(output, f, indent=2)
            f.write("\n")
        print(f"\nSaved situations to {args.save_situations}")


if __name__ == "__main__":
    main()

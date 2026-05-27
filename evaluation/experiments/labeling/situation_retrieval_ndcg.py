"""Compute NDCG metrics for situation summary retrieval using golden labels.

Evaluates retrieval ranking quality by comparing embedding similarity scores
against human-assigned graded relevance labels (0/1/2).

Two modes:
- **golden**: Uses the golden situations already in the labels file (no API calls)
- **captured**: Re-runs retrieval with the pipeline-captured situations to measure
  the gap between ideal queries and what the model actually produced

Usage::

    # Evaluate golden situation retrieval (offline, no API calls)
    poetry run python -m evaluation.experiments.labeling.situation_retrieval_ndcg

    # Also evaluate captured situations (requires embedding API)
    poetry run python -m evaluation.experiments.labeling.situation_retrieval_ndcg \
        --include-captured

    # Filter by role or phase
    poetry run python -m evaluation.experiments.labeling.situation_retrieval_ndcg \
        --role wolf --phase day_vote
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from evaluation.core.settings import REPO_ROOT

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


def compute_case_ndcg(
    labels: list[dict],
    ks: list[int],
) -> dict[str, float]:
    sorted_labels = sorted(labels, key=lambda x: x.get("score", 0), reverse=True)
    relevances = [l["relevance"] for l in sorted_labels]
    results = {}
    for k in ks:
        results[f"ndcg@{k}"] = ndcg_at_k(relevances, k)
    results["num_items"] = len(relevances)
    results["num_relevant"] = sum(1 for r in relevances if r > 0)
    results["num_highly_relevant"] = sum(1 for r in relevances if r == 2)
    return results


def compute_captured_ndcg(
    case_entry: dict,
    ks: list[int],
) -> dict[str, dict[str, float]] | None:
    """Re-run retrieval with captured situations and compute NDCG."""
    from Agents.memory import store as memory_store
    from Agents.memory import (
        retrieve_observations_for_agent,
        retrieve_strategy_points_for_agent,
    )
    from Agents.memory_persistence import seed_memory_from_json_files
    from evaluation.data.datasets import read_eval_dataset

    seed_memory_from_json_files(
        observations_path=STORE_DIR / "observations.json",
        strategy_points_path=STORE_DIR / "strategy_points.json",
        target_store=memory_store,
    )

    records = read_eval_dataset(EVAL_DATASET)
    record = records[case_entry["case_index"]]
    case = record.eval_case
    captured_situations = list(case.situations)

    if not captured_situations:
        return None

    obs_key_to_relevance = {
        l["key"]: l["relevance"] for l in case_entry.get("observation_labels", [])
    }
    sp_key_to_relevance = {
        l["key"]: l["relevance"] for l in case_entry.get("strategy_labels", [])
    }

    observations = retrieve_observations_for_agent(
        store=memory_store,
        role=case.player_role,
        action_phase=case.action_phase,
        situations=captured_situations,
        top_k=10,
    )
    observations.sort(key=lambda x: x.score or 0, reverse=True)

    strategy_points = retrieve_strategy_points_for_agent(
        store=memory_store,
        role=case.player_role,
        action_phase=case.action_phase,
        situations=captured_situations,
        top_k=10,
    )
    strategy_points.sort(key=lambda x: x.score or 0, reverse=True)

    obs_labels = []
    for item in observations:
        rel = obs_key_to_relevance.get(item.key, 0)
        obs_labels.append({"key": item.key, "score": item.score, "relevance": rel})

    sp_labels = []
    for item in strategy_points:
        rel = sp_key_to_relevance.get(item.key, 0)
        sp_labels.append({"key": item.key, "score": item.score, "relevance": rel})

    results = {}
    if obs_labels:
        results["observations"] = compute_case_ndcg(obs_labels, ks)
    if sp_labels:
        results["strategy_points"] = compute_case_ndcg(sp_labels, ks)

    combined = obs_labels + sp_labels
    if combined:
        combined.sort(key=lambda x: x.get("score", 0), reverse=True)
        relevances = [l["relevance"] for l in combined]
        results["combined"] = {}
        for k in ks:
            results["combined"][f"ndcg@{k}"] = ndcg_at_k(relevances, k)

    results["unlabeled_obs"] = sum(1 for item in observations if item.key not in obs_key_to_relevance)
    results["unlabeled_sp"] = sum(1 for item in strategy_points if item.key not in sp_key_to_relevance)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute NDCG metrics for situation retrieval golden labels."
    )
    parser.add_argument(
        "--include-captured",
        action="store_true",
        help="Also evaluate captured (pipeline) situations (requires embedding API)",
    )
    parser.add_argument("--role", type=str, help="Filter to a specific role")
    parser.add_argument("--phase", type=str, help="Filter to a specific action phase")
    parser.add_argument(
        "--k",
        type=int,
        nargs="+",
        default=[3, 5, 10],
        help="Values of k for NDCG@k (default: 3 5 10)",
    )
    args = parser.parse_args()

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

    ks = args.k

    print(f"Evaluating {len(labels_list)} labeled cases")
    print(f"NDCG@k for k={ks}")
    print()

    obs_ndcg: dict[str, list[float]] = defaultdict(list)
    sp_ndcg: dict[str, list[float]] = defaultdict(list)
    combined_ndcg: dict[str, list[float]] = defaultdict(list)
    role_ndcg: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    print(f"{'Case':>4}  {'Role':>13}  {'Phase':>16}", end="")
    for k in ks:
        print(f"  {'obs@' + str(k):>7}  {'sp@' + str(k):>7}  {'all@' + str(k):>7}", end="")
    print()
    print("-" * (42 + 27 * len(ks)))

    for entry in sorted(labels_list, key=lambda x: x["case_index"]):
        obs_labels = entry.get("observation_labels", [])
        sp_labels = entry.get("strategy_labels", [])

        obs_metrics = compute_case_ndcg(obs_labels, ks) if obs_labels else None
        sp_metrics = compute_case_ndcg(sp_labels, ks) if sp_labels else None

        all_labels = obs_labels + sp_labels
        all_labels_sorted = sorted(all_labels, key=lambda x: x.get("score", 0), reverse=True)
        all_relevances = [l["relevance"] for l in all_labels_sorted]
        combined_metrics = {}
        for k in ks:
            combined_metrics[f"ndcg@{k}"] = ndcg_at_k(all_relevances, k)

        idx = entry["case_index"]
        role = entry["player_role"]
        phase = entry["action_phase"]

        print(f"{idx:4d}  {role:>13}  {phase:>16}", end="")

        for k in ks:
            key = f"ndcg@{k}"
            o = obs_metrics[key] if obs_metrics else float("nan")
            s = sp_metrics[key] if sp_metrics else float("nan")
            c = combined_metrics[key]

            if obs_metrics:
                obs_ndcg[key].append(o)
            if sp_metrics:
                sp_ndcg[key].append(s)
            combined_ndcg[key].append(c)
            role_ndcg[role][key].append(c)

            print(f"  {o:7.4f}  {s:7.4f}  {c:7.4f}", end="")
        print()

    print()
    print("=" * (42 + 27 * len(ks)))
    print(f"{'MEAN':>4}  {'':>13}  {'':>16}", end="")
    for k in ks:
        key = f"ndcg@{k}"
        o = sum(obs_ndcg[key]) / len(obs_ndcg[key]) if obs_ndcg[key] else float("nan")
        s = sum(sp_ndcg[key]) / len(sp_ndcg[key]) if sp_ndcg[key] else float("nan")
        c = sum(combined_ndcg[key]) / len(combined_ndcg[key]) if combined_ndcg[key] else float("nan")
        print(f"  {o:7.4f}  {s:7.4f}  {c:7.4f}", end="")
    print()

    print()
    print("Per-role means (combined):")
    for role in sorted(role_ndcg.keys()):
        metrics = role_ndcg[role]
        print(f"  {role:>13}:", end="")
        for k in ks:
            key = f"ndcg@{k}"
            vals = metrics[key]
            mean = sum(vals) / len(vals) if vals else float("nan")
            print(f"  ndcg@{k}={mean:.4f}", end="")
        print(f"  (n={len(metrics[f'ndcg@{ks[0]}'])})")

    per_phase: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for entry in labels_list:
        phase = entry["action_phase"]
        all_labels = entry.get("observation_labels", []) + entry.get("strategy_labels", [])
        all_labels_sorted = sorted(all_labels, key=lambda x: x.get("score", 0), reverse=True)
        all_relevances = [l["relevance"] for l in all_labels_sorted]
        for k in ks:
            per_phase[phase][f"ndcg@{k}"].append(ndcg_at_k(all_relevances, k))

    print()
    print("Per-phase means (combined):")
    for phase in sorted(per_phase.keys()):
        metrics = per_phase[phase]
        print(f"  {phase:>16}:", end="")
        for k in ks:
            key = f"ndcg@{k}"
            vals = metrics[key]
            mean = sum(vals) / len(vals) if vals else float("nan")
            print(f"  ndcg@{k}={mean:.4f}", end="")
        print(f"  (n={len(metrics[f'ndcg@{ks[0]}'])})")

    if args.include_captured:
        print()
        print("=" * 60)
        print("CAPTURED SITUATIONS COMPARISON")
        print("Re-running retrieval with pipeline-captured situations...")
        print("=" * 60)
        print()

        captured_results = {}
        for entry in sorted(labels_list, key=lambda x: x["case_index"]):
            idx = entry["case_index"]
            print(f"  Retrieving case {idx}...", flush=True)
            result = compute_captured_ndcg(entry, ks)
            if result:
                captured_results[idx] = result

        if captured_results:
            print()
            print(f"{'Case':>4}  {'golden@5':>10}  {'captured@5':>12}  {'delta':>7}  {'unlabeled':>10}")
            print("-" * 55)

            golden_scores = []
            captured_scores = []
            for entry in sorted(labels_list, key=lambda x: x["case_index"]):
                idx = entry["case_index"]
                all_labels = entry.get("observation_labels", []) + entry.get("strategy_labels", [])
                all_labels_sorted = sorted(all_labels, key=lambda x: x.get("score", 0), reverse=True)
                golden_5 = ndcg_at_k([l["relevance"] for l in all_labels_sorted], 5)

                if idx in captured_results and "combined" in captured_results[idx]:
                    cap_5 = captured_results[idx]["combined"].get("ndcg@5", float("nan"))
                    unlabeled = (
                        captured_results[idx].get("unlabeled_obs", 0)
                        + captured_results[idx].get("unlabeled_sp", 0)
                    )
                    delta = golden_5 - cap_5
                    golden_scores.append(golden_5)
                    captured_scores.append(cap_5)
                    print(f"{idx:4d}  {golden_5:10.4f}  {cap_5:12.4f}  {delta:+7.4f}  {unlabeled:10d}")

            if golden_scores:
                g_mean = sum(golden_scores) / len(golden_scores)
                c_mean = sum(captured_scores) / len(captured_scores)
                print("-" * 55)
                print(f"MEAN  {g_mean:10.4f}  {c_mean:12.4f}  {g_mean - c_mean:+7.4f}")


if __name__ == "__main__":
    main()

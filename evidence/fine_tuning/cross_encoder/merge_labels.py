"""Merge multi-source labels into final consensus golden labels.

Combines ChatGPT labels (full context) with 3-model consensus labels
(flash-lite, 3.5-flash, Qwen 3.5) into a single set of golden labels.

For each item, computes a 4-model vote: ChatGPT + 3 automated models.
Disagreements are resolved by majority vote; ties default to ChatGPT
(full-context labeler).

Usage:
    poetry run python evidence/fine_tuning/cross_encoder/merge_labels.py

    # Custom paths
    poetry run python evidence/fine_tuning/cross_encoder/merge_labels.py \
        --chatgpt evidence/fine_tuning/cross_encoder/chatgpt_labels_full.json \
        --consensus evidence/fine_tuning/cross_encoder/consensus_labels_3model.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CROSS_ENCODER_DIR = REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder"
GOLDEN_LABELS_PATH = (
    REPO_ROOT / "evidence" / "extraction" / "situation_summary"
    / "retrieval_golden_labels.json"
)


def _build_key_map(labels_list: list[dict], label_type: str) -> dict[str, int]:
    result = {}
    for item in labels_list:
        result[item["key"]] = item["relevance"]
    return result


def _vote(scores: list[int | None], chatgpt_score: int | None = None) -> dict:
    valid = [s for s in scores if s is not None]
    if not valid:
        return {"label": None, "confidence": "no_response", "votes": scores}

    counter = Counter(valid)
    most_common = counter.most_common()

    if len(most_common) == 1:
        return {"label": most_common[0][0], "confidence": "unanimous", "votes": scores}

    top_label, top_count = most_common[0]
    second_count = most_common[1][1]

    if top_count > second_count:
        return {"label": top_label, "confidence": "majority", "votes": scores}

    if chatgpt_score is not None and chatgpt_score in [l for l, c in most_common if c == top_count]:
        return {"label": chatgpt_score, "confidence": "tie_chatgpt", "votes": scores}

    return {"label": round(sum(valid) / len(valid)), "confidence": "tie_avg", "votes": scores}


def merge(
    chatgpt_path: Path,
    consensus_path: Path,
    candidates_path: Path,
    output_path: Path,
):
    with open(chatgpt_path) as f:
        chatgpt_data = json.load(f)
    with open(consensus_path) as f:
        consensus_data = json.load(f)
    with open(candidates_path) as f:
        candidates_data = json.load(f)

    gpt_by_case = {}
    for case in chatgpt_data["cases"]:
        gpt_by_case[case["case_index"]] = case

    con_by_case = {}
    for case in consensus_data["cases"]:
        con_by_case[case["case_index"]] = case

    cand_by_case = {}
    for case in candidates_data["cases"]:
        cand_by_case[case["case_index"]] = case

    stats = Counter()
    results = []

    for case_idx in sorted(set(gpt_by_case) & set(con_by_case)):
        gpt_case = gpt_by_case[case_idx]
        con_case = con_by_case[case_idx]
        cand_case = cand_by_case[case_idx]

        gpt_obs = _build_key_map(gpt_case.get("observation_labels", []), "obs")
        gpt_sp = _build_key_map(gpt_case.get("strategy_labels", []), "sp")

        con_obs = {}
        for item in con_case.get("observation_labels", []):
            con_obs[item["key"]] = item
        con_sp = {}
        for item in con_case.get("strategy_labels", []):
            con_sp[item["key"]] = item

        cand_obs = {o["key"]: o for o in cand_case["retrieved_observations"]}
        cand_sp = {s["key"]: s for s in cand_case["retrieved_strategy_points"]}

        obs_labels = []
        for key in list(cand_obs.keys()):
            gpt_score = gpt_obs.get(key)
            con_item = con_obs.get(key, {})
            model_scores = con_item.get("model_scores", {})
            auto_scores = [v for v in model_scores.values() if v is not None]

            all_scores = ([gpt_score] if gpt_score is not None else []) + auto_scores
            vote = _vote(all_scores, chatgpt_score=gpt_score)
            stats[vote["confidence"]] += 1

            cand = cand_obs[key]
            obs_labels.append({
                "key": key,
                "relevance": vote["label"],
                "score": cand.get("score", con_item.get("score")),
                "situation": cand["situation"],
                "approach": cand.get("approach", ""),
                "outcome": cand.get("outcome", ""),
                "labeling": {
                    "chatgpt": gpt_score,
                    "model_scores": model_scores,
                    "confidence": vote["confidence"],
                },
            })

        sp_labels = []
        for key in list(cand_sp.keys()):
            gpt_score = gpt_sp.get(key)
            con_item = con_sp.get(key, {})
            model_scores = con_item.get("model_scores", {})
            auto_scores = [v for v in model_scores.values() if v is not None]

            all_scores = ([gpt_score] if gpt_score is not None else []) + auto_scores
            vote = _vote(all_scores, chatgpt_score=gpt_score)
            stats[vote["confidence"]] += 1

            cand = cand_sp[key]
            sp_labels.append({
                "key": key,
                "relevance": vote["label"],
                "score": cand.get("score", con_item.get("score")),
                "situation": cand["situation"],
                "action": cand.get("action", ""),
                "labeling": {
                    "chatgpt": gpt_score,
                    "model_scores": model_scores,
                    "confidence": vote["confidence"],
                },
            })

        results.append({
            "case_index": case_idx,
            "case_id": con_case.get("case_id", cand_case.get("case_id", "")),
            "player_role": con_case.get("player_role", cand_case.get("player_role", "")),
            "day": con_case.get("day", cand_case.get("day")),
            "round": con_case.get("round", cand_case.get("round")),
            "action_phase": con_case.get("action_phase", cand_case.get("action_phase", "")),
            "golden_situations": con_case.get("golden_situations",
                                               cand_case.get("golden_situations", [])),
            "observation_labels": obs_labels,
            "strategy_labels": sp_labels,
        })

    total = sum(stats.values())
    output = {
        "description": "Merged 4-model consensus labels (ChatGPT + flash-lite + 3.5-flash + Qwen 3.5)",
        "models": {
            "chatgpt": "GPT-4o (full game context)",
            "automated": consensus_data.get("models", []),
        },
        "stats": {
            "total_items": total,
            **{k: v for k, v in stats.most_common()},
        },
        "cases": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")

    print(f"Merged {total} items across {len(results)} cases")
    for conf, count in stats.most_common():
        print(f"  {conf:15s}: {count:3d} ({count/max(total,1)*100:.0f}%)")

    label_dist = Counter()
    for case in results:
        for item in case["observation_labels"] + case["strategy_labels"]:
            if item["relevance"] is not None:
                label_dist[item["relevance"]] += 1
    print(f"\nLabel distribution:")
    for label in sorted(label_dist):
        print(f"  {label}: {label_dist[label]}")

    print(f"\nWrote: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chatgpt", type=Path,
        default=CROSS_ENCODER_DIR / "chatgpt_labels_full.json",
    )
    parser.add_argument(
        "--consensus", type=Path,
        default=CROSS_ENCODER_DIR / "consensus_labels_3model.json",
    )
    parser.add_argument(
        "--candidates", type=Path,
        default=CROSS_ENCODER_DIR / "candidates_for_labeling.json",
    )
    parser.add_argument(
        "--output", type=Path,
        default=CROSS_ENCODER_DIR / "merged_labels.json",
    )
    args = parser.parse_args()
    merge(args.chatgpt, args.consensus, args.candidates, args.output)


if __name__ == "__main__":
    main()

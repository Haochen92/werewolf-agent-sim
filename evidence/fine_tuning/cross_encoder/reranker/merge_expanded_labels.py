"""Merge 4-model expanded labels into final consensus.

Combines ChatGPT batch responses (22 files, full game context) with 3
per-model label files (mistral, flash-lite, nim) into a single set of
golden labels for reranker cross-encoder training.

Voting logic (4 models):
  - 4/4 or 3/4 agree → majority label
  - 2/2 tie → flagged for Opus tiebreaking
  - 1/3 minority → label with majority, flag for spot-check

Usage:
    poetry run python evidence/fine_tuning/cross_encoder/reranker/merge_expanded_labels.py

    # Dry run to see disagreement stats only
    poetry run python evidence/fine_tuning/cross_encoder/reranker/merge_expanded_labels.py --dry-run
"""
from __future__ import annotations

import argparse
import glob
import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CE_DIR = REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker"


def _load_chatgpt_labels(response_dir: Path) -> dict[str, int]:
    """Load all batch_XX_response.json files into {case_index:short_key -> score}.

    ChatGPT batch exports use truncated keys (first 12 chars of UUID).
    """
    labels = {}
    for fpath in sorted(response_dir.glob("batch_*_response.json")):
        data = json.load(open(fpath))
        for case in data:
            case_idx = case["case_index"]
            for item in case["labels"]:
                labels[f"{case_idx}:{item['key']}"] = item["relevance"]
    return labels


def _chatgpt_lookup(chatgpt_labels: dict[str, int], case_idx: int, full_key: str) -> int | None:
    """Match a full UUID key against truncated ChatGPT keys."""
    short_key = full_key[:12]
    return chatgpt_labels.get(f"{case_idx}:{short_key}")


def _load_model_labels(label_path: Path) -> dict[str, int]:
    """Load a per-model label file into {case_index:key -> score}."""
    labels = {}
    data = json.load(open(label_path))
    for case in data["cases"]:
        case_idx = case["case_index"]
        for item in case.get("observation_labels", []):
            score = item.get("relevance")
            if score is not None:
                ms = item.get("model_scores", {})
                actual = next((v for v in ms.values() if v is not None), score)
                labels[f"{case_idx}:{item['key']}"] = actual
        for item in case.get("strategy_labels", []):
            score = item.get("relevance")
            if score is not None:
                ms = item.get("model_scores", {})
                actual = next((v for v in ms.values() if v is not None), score)
                labels[f"{case_idx}:{item['key']}"] = actual
    return labels


def _vote(scores: dict[str, int | None]) -> dict:
    """4-model vote. Returns label, confidence, and raw scores."""
    valid = {k: v for k, v in scores.items() if v is not None}
    if not valid:
        return {"label": None, "confidence": "no_response", "scores": scores}

    values = list(valid.values())
    counter = Counter(values)
    most_common = counter.most_common()

    n_voters = len(valid)
    top_label, top_count = most_common[0]

    if top_count == n_voters:
        return {"label": top_label, "confidence": "unanimous", "scores": scores}

    if top_count > n_voters / 2:
        return {"label": top_label, "confidence": "majority", "scores": scores}

    if len(most_common) >= 2 and most_common[0][1] == most_common[1][1]:
        chatgpt = scores.get("chatgpt")
        if chatgpt is not None and chatgpt in [l for l, _ in most_common if counter[l] == top_count]:
            return {"label": chatgpt, "confidence": "tie_chatgpt", "scores": scores}
        return {"label": None, "confidence": "tie", "scores": scores}

    return {"label": top_label, "confidence": "majority", "scores": scores}


MODEL_NAMES = {
    "chatgpt": "chatgpt",
    "mistral": "mistral-small-2506",
    "flashlite": "flash-lite",
    "nim": "llama-3.1-8b",
}


def merge(
    chatgpt_dir: Path,
    model_files: dict[str, Path],
    candidates_path: Path,
    output_path: Path,
    dry_run: bool = False,
):
    chatgpt_labels = _load_chatgpt_labels(chatgpt_dir)
    print(f"Loaded {len(chatgpt_labels)} ChatGPT labels")

    model_labels = {}
    for name, path in model_files.items():
        model_labels[name] = _load_model_labels(path)
        print(f"Loaded {len(model_labels[name])} {name} labels")

    with open(candidates_path) as f:
        candidates = json.load(f)

    stats = Counter()
    ties = []
    results = []

    for case in candidates["cases"]:
        case_idx = case["case_index"]

        obs_labels = []
        sp_labels = []

        all_items = (
            [("observation", o) for o in case["retrieved_observations"]]
            + [("strategy_point", s) for s in case["retrieved_strategy_points"]]
        )

        for mem_type, item in all_items:
            item_key = f"{case_idx}:{item['key']}"

            scores = {
                "chatgpt": _chatgpt_lookup(chatgpt_labels, case_idx, item["key"]),
            }
            for name, labels in model_labels.items():
                scores[name] = labels.get(item_key)

            vote = _vote(scores)
            stats[vote["confidence"]] += 1

            if vote["confidence"] == "tie":
                ties.append({
                    "case_index": case_idx,
                    "key": item["key"],
                    "type": mem_type,
                    "scores": scores,
                    "situation": item["situation"][:100],
                })

            entry = {
                "key": item["key"],
                "relevance": vote["label"],
                "score": item["score"],
                "situation": item["situation"],
                "labeling": {
                    "scores": vote["scores"],
                    "confidence": vote["confidence"],
                },
            }
            if mem_type == "observation":
                entry["approach"] = item.get("approach", "")
                entry["outcome"] = item.get("outcome", "")
                obs_labels.append(entry)
            else:
                entry["action"] = item.get("action", "")
                sp_labels.append(entry)

        results.append({
            "case_index": case_idx,
            "case_id": case["case_id"],
            "player_role": case["player_role"],
            "day": case["day"],
            "round": case["round"],
            "action_phase": case["action_phase"],
            "golden_situations": case["golden_situations"],
            "observation_labels": obs_labels,
            "strategy_labels": sp_labels,
        })

    total = sum(stats.values())
    print(f"\nMerged {total} items across {len(results)} cases")
    for conf, count in stats.most_common():
        print(f"  {conf:15s}: {count:4d} ({count/max(total,1)*100:.1f}%)")

    if ties:
        print(f"\n{len(ties)} ties need Opus tiebreaking:")
        for t in ties[:10]:
            print(f"  case {t['case_index']} {t['type']} "
                  f"{t['scores']} | {t['situation']}...")
        if len(ties) > 10:
            print(f"  ... and {len(ties) - 10} more")

    label_dist = Counter()
    for case in results:
        for item in case["observation_labels"] + case["strategy_labels"]:
            if item["relevance"] is not None:
                label_dist[item["relevance"]] += 1
    print(f"\nLabel distribution:")
    for label in sorted(label_dist):
        print(f"  {label}: {label_dist[label]}")
    if None in [i["relevance"] for c in results for i in c["observation_labels"] + c["strategy_labels"]]:
        none_count = sum(1 for c in results for i in c["observation_labels"] + c["strategy_labels"] if i["relevance"] is None)
        print(f"  None (unresolved): {none_count}")

    if dry_run:
        print("\nDry run — not writing output.")
        if ties:
            ties_path = output_path.parent / "expanded_ties.json"
            with open(ties_path, "w") as f:
                json.dump(ties, f, indent=2)
                f.write("\n")
            print(f"Wrote ties to: {ties_path}")
        return

    output = {
        "description": "Merged 4-model consensus labels for expanded reranker training",
        "models": MODEL_NAMES,
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
    print(f"\nWrote: {output_path}")

    if ties:
        ties_path = output_path.parent / "expanded_ties.json"
        with open(ties_path, "w") as f:
            json.dump(ties, f, indent=2)
            f.write("\n")
        print(f"Wrote ties to: {ties_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chatgpt-dir", type=Path,
        default=CE_DIR / "labeling_responses",
    )
    parser.add_argument(
        "--mistral", type=Path,
        default=CE_DIR / "expanded_labels_mistral.json",
    )
    parser.add_argument(
        "--flashlite", type=Path,
        default=CE_DIR / "expanded_labels_flashlite.json",
    )
    parser.add_argument(
        "--nim", type=Path,
        default=CE_DIR / "expanded_labels_nim.json",
    )
    parser.add_argument(
        "--candidates", type=Path,
        default=CE_DIR / "expanded_candidates_for_labeling.json",
    )
    parser.add_argument(
        "--output", type=Path,
        default=CE_DIR / "expanded_merged_labels.json",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    merge(
        chatgpt_dir=args.chatgpt_dir,
        model_files={
            "mistral": args.mistral,
            "flashlite": args.flashlite,
            "nim": args.nim,
        },
        candidates_path=args.candidates,
        output_path=args.output,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()

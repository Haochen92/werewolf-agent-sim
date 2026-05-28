"""Prepare training data for retrieval reranker cross-encoder.

Converts golden retrieval labels into (query, document, relevance) pairs
for cross-encoder training. Output format matches sentence-transformers
CrossEncoder training expectations.

Usage:
    poetry run python evidence/fine_tuning/cross_encoder/prep_reranker_data.py
    poetry run python evidence/fine_tuning/cross_encoder/prep_reranker_data.py \
        --output evidence/fine_tuning/cross_encoder/reranker_pairs.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLDEN_LABELS_PATH = (
    REPO_ROOT / "evidence" / "extraction" / "situation_summary"
    / "retrieval_golden_labels.json"
)
OBS_STORE = REPO_ROOT / "Agents" / "memory_stores" / "v4_deduped_v2" / "observations.json"
SP_STORE = REPO_ROOT / "Agents" / "memory_stores" / "v4_deduped_v2" / "strategy_points.json"

RELEVANCE_MAP = {0: 0.0, 1: 0.5, 2: 1.0}


def _load_memory_texts() -> dict[str, str]:
    key_to_text: dict[str, str] = {}

    with open(OBS_STORE) as f:
        obs_data = json.load(f)
    for items in obs_data["namespaces"].values():
        for item in items:
            val = item["value"]
            parts = [f"Situation: {val['situation']}"]
            if val.get("approach"):
                parts.append(f"Approach: {val['approach']}")
            if val.get("outcome"):
                parts.append(f"Outcome: {val['outcome']}")
            key_to_text[item["key"]] = " | ".join(parts)

    with open(SP_STORE) as f:
        sp_data = json.load(f)
    for items in sp_data["namespaces"].values():
        for item in items:
            key_to_text[item["key"]] = item["value"]["situation"]

    return key_to_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path,
        default=REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker_pairs.jsonl",
    )
    args = parser.parse_args()

    key_to_text = _load_memory_texts()
    print(f"Loaded {len(key_to_text)} memory texts")

    with open(GOLDEN_LABELS_PATH) as f:
        data = json.load(f)

    pairs = []
    for case in data["labels"]:
        query = "\n".join(case["golden_situations"])

        for label in case.get("observation_labels", []):
            text = key_to_text.get(label["key"])
            if text is None:
                continue
            pairs.append({
                "sentence1": query,
                "sentence2": text,
                "label": RELEVANCE_MAP[label["relevance"]],
                "case_index": case["case_index"],
                "mem_type": "observation",
            })

        for label in case.get("strategy_labels", []):
            text = key_to_text.get(label["key"])
            if text is None:
                continue
            pairs.append({
                "sentence1": query,
                "sentence2": text,
                "label": RELEVANCE_MAP[label["relevance"]],
                "case_index": case["case_index"],
                "mem_type": "strategy_point",
            })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")

    by_label = {0.0: 0, 0.5: 0, 1.0: 0}
    for p in pairs:
        by_label[p["label"]] += 1

    print(f"Wrote {len(pairs)} pairs to {args.output}")
    print(f"  irrelevant (0.0): {by_label[0.0]}")
    print(f"  partial (0.5):    {by_label[0.5]}")
    print(f"  relevant (1.0):   {by_label[1.0]}")


if __name__ == "__main__":
    main()

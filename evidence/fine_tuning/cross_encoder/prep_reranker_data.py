"""Prepare training data for retrieval reranker cross-encoder.

Converts golden retrieval labels into (query, document, relevance) pairs
for cross-encoder training. Splits into train/eval by held-out cases
(one per role) to prevent query leakage.

Usage:
    poetry run python evidence/fine_tuning/cross_encoder/prep_reranker_data.py
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
OUTPUT_DIR = REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder"

RELEVANCE_MAP = {0: 0.0, 1: 0.25, 2: 1.0}

EVAL_CASES = {5, 10, 14, 16, 20, 22, 24, 29}


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


def _build_pairs(data: dict, key_to_text: dict[str, str]) -> list[dict]:
    pairs = []
    for case in data["labels"]:
        query = "\n".join(case["golden_situations"])
        case_idx = case["case_index"]

        for label in case.get("observation_labels", []):
            text = key_to_text.get(label["key"])
            if text is None:
                continue
            pairs.append({
                "sentence1": query,
                "sentence2": text,
                "label": RELEVANCE_MAP[label["relevance"]],
                "case_index": case_idx,
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
                "case_index": case_idx,
                "mem_type": "strategy_point",
            })
    return pairs


def _print_split_stats(pairs: list[dict], name: str) -> None:
    by_label = {0.0: 0, 0.25: 0, 1.0: 0}
    for p in pairs:
        by_label[p["label"]] += 1
    cases = sorted(set(p["case_index"] for p in pairs))
    print(f"  {name}: {len(pairs)} pairs, {len(cases)} cases")
    print(f"    irrelevant={by_label[0.0]}  partial={by_label[0.25]}  relevant={by_label[1.0]}")


def _write_jsonl(pairs: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")


def main():
    key_to_text = _load_memory_texts()
    print(f"Loaded {len(key_to_text)} memory texts")

    with open(GOLDEN_LABELS_PATH) as f:
        data = json.load(f)

    all_pairs = _build_pairs(data, key_to_text)
    train_pairs = [p for p in all_pairs if p["case_index"] not in EVAL_CASES]
    eval_pairs = [p for p in all_pairs if p["case_index"] in EVAL_CASES]

    print(f"\nHeld-out eval cases: {sorted(EVAL_CASES)}")
    _print_split_stats(train_pairs, "train")
    _print_split_stats(eval_pairs, "eval")

    _write_jsonl(train_pairs, OUTPUT_DIR / "reranker_train.jsonl")
    _write_jsonl(eval_pairs, OUTPUT_DIR / "reranker_eval.jsonl")
    _write_jsonl(all_pairs, OUTPUT_DIR / "reranker_pairs.jsonl")

    print(f"\nWrote:")
    print(f"  {OUTPUT_DIR / 'reranker_train.jsonl'}")
    print(f"  {OUTPUT_DIR / 'reranker_eval.jsonl'}")
    print(f"  {OUTPUT_DIR / 'reranker_pairs.jsonl'} (all)")


if __name__ == "__main__":
    main()

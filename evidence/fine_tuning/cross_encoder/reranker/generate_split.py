"""Generate stratified train/val/test split for reranker cross-encoder.

Creates a deterministic split manifest (reranker_split.json) that all
downstream scripts read from. Stratified by (player_role x action_phase)
with proportional allocation (~70/15/15) per stratum.

Usage:
    poetry run python evidence/fine_tuning/cross_encoder/reranker/generate_split.py
    poetry run python evidence/fine_tuning/cross_encoder/reranker/generate_split.py --seed 123
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
GOLDEN_LABELS_PATH = (
    REPO_ROOT / "evidence" / "extraction" / "situation_summary"
    / "retrieval_golden_labels.json"
)
OUTPUT_PATH = REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker" / "reranker_split.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate stratified train/val/test split for reranker",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    raw = GOLDEN_LABELS_PATH.read_bytes()
    labels_hash = hashlib.sha256(raw).hexdigest()

    data = json.loads(raw)

    strata: dict[tuple[str, str], list[int]] = defaultdict(list)
    for case in data["labels"]:
        key = (case["player_role"], case["action_phase"])
        strata[key].append(case["case_index"])

    rng = random.Random(args.seed)

    train, val, test = [], [], []
    print(f"Seed: {args.seed}")
    print(f"Strata: {len(strata)}")
    print()

    for (role, phase) in sorted(strata.keys()):
        indices = sorted(strata[(role, phase)])
        rng.shuffle(indices)
        n = len(indices)
        n_test = max(1, round(n * 0.15))
        n_val = max(1, round(n * 0.15))
        n_train = n - n_val - n_test
        test.extend(indices[:n_test])
        val.extend(indices[n_test : n_test + n_val])
        train.extend(indices[n_test + n_val :])
        print(f"  {role:>13} x {phase:<16}: {n:3d} cases → "
              f"train={n_train}  val={n_val}  test={n_test}")

    train.sort()
    val.sort()
    test.sort()

    total = len(set(train) | set(val) | set(test))
    assert total == len(data["labels"]), f"Expected {len(data['labels'])}, got {total}"

    manifest = {
        "description": "Stratified train/val/test split for reranker cross-encoder",
        "seed": args.seed,
        "strategy": "stratified by (player_role x action_phase), ~70/15/15 per stratum",
        "golden_labels_sha256": labels_hash,
        "train": train,
        "val": val,
        "test": test,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    print(f"\nSplit: {len(train)} train / {len(val)} val / {len(test)} test")
    print(f"Golden labels hash: {labels_hash[:16]}...")
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()

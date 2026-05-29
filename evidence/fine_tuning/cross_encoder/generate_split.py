"""Generate stratified train/val/test split for reranker cross-encoder.

Creates a deterministic split manifest (reranker_split.json) that all
downstream scripts read from. Stratified by (player_role x action_phase)
with 3/1/1 allocation per stratum (24 train / 8 val / 8 test).

Usage:
    poetry run python evidence/fine_tuning/cross_encoder/generate_split.py
    poetry run python evidence/fine_tuning/cross_encoder/generate_split.py --seed 123
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLDEN_LABELS_PATH = (
    REPO_ROOT / "evidence" / "extraction" / "situation_summary"
    / "retrieval_golden_labels.json"
)
OUTPUT_PATH = REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker_split.json"


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
        train.extend(indices[:3])
        val.append(indices[3])
        test.append(indices[4])
        print(f"  {role:>13} x {phase:<16}: "
              f"train={sorted(indices[:3])}  val=[{indices[3]}]  test=[{indices[4]}]")

    train.sort()
    val.sort()
    test.sort()

    assert len(train) == 24
    assert len(val) == 8
    assert len(test) == 8
    assert len(set(train) | set(val) | set(test)) == 40

    manifest = {
        "description": "Stratified train/val/test split for reranker cross-encoder",
        "seed": args.seed,
        "strategy": "stratified by (player_role x action_phase), 3/1/1 per stratum",
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

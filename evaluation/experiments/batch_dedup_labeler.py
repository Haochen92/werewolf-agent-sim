"""Interactive batch dedup cluster labeling tool.

Reads clusters from a JSON file, formats them for review, and records
golden labels. Supports three workflows:

1. **Display**: Show a cluster's entries formatted for human review.
2. **Label**: Record a set of operations (DISCARD/MERGE/KEEP) for a cluster.
3. **Sample**: Select a balanced subset of clusters for labeling.

Usage::

    # Show a specific cluster
    poetry run python -m evaluation.experiments.batch_dedup_labeler \\
        show --source eval_sets/batch_dedup_clusters_v4.json --cluster 0

    # Show all small clusters (size <= 5)
    poetry run python -m evaluation.experiments.batch_dedup_labeler \\
        show --source eval_sets/batch_dedup_clusters_v4.json --max-size 5

    # Sample clusters for labeling (target ~120 items)
    poetry run python -m evaluation.experiments.batch_dedup_labeler \\
        sample --source eval_sets/batch_dedup_clusters_v4.json --target-items 120

    # Show labeling progress
    poetry run python -m evaluation.experiments.batch_dedup_labeler \\
        progress --labels eval_sets/batch_dedup_golden_labels.json
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any

from evaluation.core.settings import REPO_ROOT


def load_clusters(path: Path) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def load_labels(path: Path) -> dict:
    if not path.exists():
        return {
            "eval_set_id": "batch_dedup_golden_v1",
            "created_at": datetime.now().isoformat(),
            "labeler": "human",
            "description": "Golden labels for batch dedup cluster evaluation",
            "label_schema": {
                "DISCARD": "Entries are duplicates — same hypothesis. Pick survivor, delete rest.",
                "MERGE": "Entries share situation+outcome but different tactics. Consolidate approach.",
                "KEEP": "Entries are genuinely distinct — different situations or outcomes.",
            },
            "labels": [],
        }
    with open(path) as f:
        return json.load(f)


def save_labels(path: Path, labels: dict) -> None:
    with open(path, "w") as f:
        json.dump(labels, f, indent=2)
        f.write("\n")


def format_cluster(cluster: dict, cluster_idx: int) -> str:
    lines = []
    ns = cluster["namespace"]
    kind = cluster["kind"]
    size = cluster["size"]
    items = cluster["items"]

    lines.append(f"{'='*80}")
    lines.append(f"CLUSTER {cluster_idx}: {kind} | {ns} | {size} entries")
    lines.append(f"{'='*80}")
    lines.append("")

    for i, item in enumerate(items, 1):
        lines.append(f"--- Entry {i} ---")
        lines.append(f"  KEY: {item['key']}")
        lines.append(f"  obs_count: {item.get('observation_count', 1)}")

        if kind == "strategy_points":
            lines.append(f"  SITUATION: {item.get('situation', '')}")
            lines.append(f"  ACTION:    {item.get('action', '')}")
        else:
            lines.append(f"  SITUATION: {item.get('situation', '')}")
            lines.append(f"  APPROACH:  {item.get('approach', '')}")
            lines.append(f"  OUTCOME:   {item.get('outcome', '')}")
        lines.append("")

    return "\n".join(lines)


def sample_clusters(
    clusters: list[dict],
    target_items: int = 120,
    seed: int = 42,
) -> list[int]:
    rng = random.Random(seed)

    small = [i for i, c in enumerate(clusters) if c["size"] <= 5]
    medium = [i for i, c in enumerate(clusters) if 6 <= c["size"] <= 15]
    large = [i for i, c in enumerate(clusters) if c["size"] > 15]

    obs_indices = [i for i, c in enumerate(clusters) if c["kind"] == "observations"]
    strat_indices = [i for i, c in enumerate(clusters) if c["kind"] == "strategy_points"]

    selected: list[int] = []
    total_items = 0

    for idx in small:
        selected.append(idx)
        total_items += clusters[idx]["size"]

    rng.shuffle(medium)
    rng.shuffle(large)

    remaining = medium + large
    obs_count = sum(1 for i in selected if i in set(obs_indices))
    strat_count = sum(1 for i in selected if i in set(strat_indices))

    for idx in remaining:
        if total_items >= target_items:
            break
        kind = clusters[idx]["kind"]
        if kind == "observations" and obs_count > strat_count + 3:
            continue
        if kind == "strategy_points" and strat_count > obs_count + 3:
            continue

        selected.append(idx)
        total_items += clusters[idx]["size"]
        if kind == "observations":
            obs_count += 1
        else:
            strat_count += 1

    selected.sort()
    return selected


def add_label(
    labels: dict,
    cluster_idx: int,
    cluster: dict,
    operations: list[dict[str, Any]],
    confidence: str = "high",
    notes: str = "",
) -> None:
    existing = {l["cluster_id"] for l in labels["labels"]}
    if cluster_idx in existing:
        labels["labels"] = [
            l for l in labels["labels"] if l["cluster_id"] != cluster_idx
        ]

    all_keys = {item["key"] for item in cluster["items"]}
    labeled_keys = set()
    for op in operations:
        labeled_keys.update(op.get("source_keys", []))

    missing = all_keys - labeled_keys
    extra = labeled_keys - all_keys
    if missing:
        print(f"WARNING: {len(missing)} keys not covered: {missing}")
    if extra:
        print(f"WARNING: {len(extra)} keys not in cluster: {extra}")

    label_entry = {
        "cluster_id": cluster_idx,
        "namespace": cluster["namespace"],
        "kind": cluster["kind"],
        "size": cluster["size"],
        "operations": operations,
        "confidence": confidence,
        "notes": notes,
    }
    labels["labels"].append(label_entry)
    labels["labels"].sort(key=lambda l: l["cluster_id"])


def show_progress(labels: dict, clusters: list[dict]) -> None:
    labeled_ids = {l["cluster_id"] for l in labels["labels"]}
    total_items_labeled = sum(l["size"] for l in labels["labels"])

    print(f"Labeled: {len(labeled_ids)}/{len(clusters)} clusters")
    print(f"Items covered: {total_items_labeled}/{sum(c['size'] for c in clusters)}")
    print()

    from collections import Counter
    op_counts: Counter[str] = Counter()
    for l in labels["labels"]:
        for op in l["operations"]:
            op_counts[op["action"]] += 1

    if op_counts:
        print("Operation distribution:")
        for action, count in op_counts.most_common():
            print(f"  {action}: {count}")
    print()

    for i, c in enumerate(clusters):
        status = "DONE" if i in labeled_ids else "    "
        print(f"  [{status}] Cluster {i:2d}: {c['kind']:16s} {c['namespace']:45s} size={c['size']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactive batch dedup cluster labeling tool."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="Display cluster(s) for review")
    show.add_argument("--source", type=Path, required=True)
    show.add_argument("--cluster", type=int, default=None, help="Specific cluster index")
    show.add_argument("--max-size", type=int, default=None, help="Show clusters up to this size")
    show.add_argument("--kind", type=str, default=None, choices=["observations", "strategy_points"])

    samp = sub.add_parser("sample", help="Sample clusters for labeling")
    samp.add_argument("--source", type=Path, required=True)
    samp.add_argument("--target-items", type=int, default=120)
    samp.add_argument("--seed", type=int, default=42)

    prog = sub.add_parser("progress", help="Show labeling progress")
    prog.add_argument("--source", type=Path, default=REPO_ROOT / "eval_sets" / "batch_dedup_clusters_v4.json")
    prog.add_argument("--labels", type=Path, default=REPO_ROOT / "eval_sets" / "batch_dedup_golden_labels.json")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "show":
        clusters = load_clusters(args.source)
        indices = range(len(clusters))
        if args.cluster is not None:
            indices = [args.cluster]
        elif args.max_size is not None:
            indices = [i for i, c in enumerate(clusters) if c["size"] <= args.max_size]
        if args.kind:
            indices = [i for i in indices if clusters[i]["kind"] == args.kind]
        for idx in indices:
            print(format_cluster(clusters[idx], idx))
            print()

    elif args.command == "sample":
        clusters = load_clusters(args.source)
        selected = sample_clusters(clusters, args.target_items, args.seed)
        total = sum(clusters[i]["size"] for i in selected)
        print(f"Selected {len(selected)} clusters, {total} total items:\n")
        for idx in selected:
            c = clusters[idx]
            print(f"  Cluster {idx:2d}: {c['kind']:16s} {c['namespace']:45s} size={c['size']}")
        print(f"\nTotal items: {total}")

    elif args.command == "progress":
        clusters = load_clusters(args.source)
        labels = load_labels(args.labels)
        show_progress(labels, clusters)


if __name__ == "__main__":
    main()

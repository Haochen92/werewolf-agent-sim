from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from langgraph.store.base import PutOp
from langgraph.store.memory import InMemoryStore

from Agents.memory import embeddings
from evaluation.core.schemas import RetrievalScores


DEFAULT_STORE_LOAD_BATCH_SIZE = 1


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_store_from_snapshots(
    observations_path: Path,
    strategy_points_path: Path,
    batch_size: int = DEFAULT_STORE_LOAD_BATCH_SIZE,
) -> InMemoryStore:
    """Load snapshot entries directly, preserving exact JSON keys and values."""
    target_store = InMemoryStore(
        index={
            "dims": 1536,
            "embed": embeddings,
            "fields": ["content"],
        }
    )

    put_ops: list[PutOp] = []
    for path in (observations_path, strategy_points_path):
        payload = _read_json(path)
        for namespace_key, items in payload.get("namespaces", {}).items():
            namespace = tuple(namespace_key.split("/"))
            if len(namespace) != 2:
                continue
            for item in items:
                key = item.get("key")
                value = item.get("value", item)
                if key and value.get("content"):
                    put_ops.append(PutOp(namespace, key, value))

    print(
        f"  Indexing {len(put_ops)} memory items from "
        f"{observations_path.name} and {strategy_points_path.name}",
        flush=True,
    )
    for start in range(0, len(put_ops), batch_size):
        target_store.batch(put_ops[start : start + batch_size])
        indexed_count = min(start + batch_size, len(put_ops))
        if indexed_count == len(put_ops) or indexed_count % 25 == 0:
            print(f"    indexed {indexed_count}/{len(put_ops)} items", flush=True)

    return target_store


def keep_top_scored_items(items: list[Any], max_items: int | None) -> list[Any]:
    if not max_items or len(items) <= max_items:
        return items
    return sorted(items, key=lambda item: item.score or 0.0, reverse=True)[:max_items]


def redundancy_ratio(item_count: int, scores: RetrievalScores | None) -> float | None:
    if item_count <= 0 or scores is None:
        return None
    return max(0.0, 1 - (scores.unique_idea_count / item_count))


def parse_snapshot(raw: list[str]) -> tuple[str, Path, Path]:
    if len(raw) != 3:
        raise argparse.ArgumentTypeError(
            "--snapshot requires: LABEL OBSERVATIONS_JSON STRATEGY_POINTS_JSON"
        )
    label, observations_path, strategy_points_path = raw
    return label, Path(observations_path), Path(strategy_points_path)

"""Memory-store reconstruction and retrieval helpers for replay experiments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langgraph.store.base import PutOp
from langgraph.store.memory import InMemoryStore

from Agents.constants import ACTION_PHASES, VALID_ACTION_PHASES_BY_ROLE
from Agents.memory import embeddings
from evaluation.core.schemas import RetrievalScores


DEFAULT_STORE_LOAD_BATCH_SIZE = 1


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _snapshot_namespaces(namespace: tuple[str, ...]) -> list[tuple[str, ...]]:
    if len(namespace) == 3:
        return [namespace]
    if len(namespace) != 2:
        return []
    memory_kind, role = namespace
    if memory_kind not in {"observations", "strategy_points"}:
        return [namespace]
    phases = VALID_ACTION_PHASES_BY_ROLE.get(role, ACTION_PHASES)
    return [(memory_kind, role, phase) for phase in phases]


def _snapshot_value(value: dict[str, Any]) -> dict[str, Any] | None:
    situation = value.get("situation") or value.get("content")
    if not situation:
        return None
    return {**value, "situation": situation}


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
            "fields": ["situation"],
        }
    )

    put_ops: list[PutOp] = []
    for path in (observations_path, strategy_points_path):
        payload = _read_json(path)
        for namespace_key, items in payload.get("namespaces", {}).items():
            namespaces = _snapshot_namespaces(tuple(namespace_key.split("/")))
            if not namespaces:
                continue
            for item in items:
                key = item.get("key")
                value = _snapshot_value(item.get("value", item))
                if key and value:
                    put_ops.extend(
                        PutOp(namespace, key, value) for namespace in namespaces
                    )

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

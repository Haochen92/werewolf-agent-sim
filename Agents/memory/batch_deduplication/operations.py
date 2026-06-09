"""Application of a single LLM dedup operation against the store.

Validates source keys, merges metadata (counts/timestamps) onto the survivor, writes the survivor
value, and deletes absorbed entries — for both strategy-point and observation operations. Also the
index→UUID remap that turns the LLM's numbered keys back into real keys.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from langgraph.store.base import BaseStore

from .formatting import _latest_timestamp
from .schemas import ObservationBatchOperation, StrategyBatchOperation
from .store_io import _put_memory_with_retries


def _merged_metadata(
    source_keys: list[str],
    items_by_key: dict[str, Any],
    survivor_key: str,
) -> dict[str, Any]:
    source_values = [items_by_key[key].value for key in source_keys if key in items_by_key]
    survivor_value = items_by_key[survivor_key].value
    return {
        "observation_count": sum(
            int(value.get("observation_count", 1)) for value in source_values
        ),
        "last_observed": _latest_timestamp(
            [value.get("last_observed") for value in source_values]
        ),
        "game_id": survivor_value.get("game_id", ""),
        "retrieved_count": sum(
            int(value.get("retrieved_count", 0)) for value in source_values
        ),
        "used_count": sum(
            int(value.get("used_count", 0)) for value in source_values
        ),
        "positive_count": sum(
            int(value.get("positive_count", 0)) for value in source_values
        ),
        "neutral_count": sum(
            int(value.get("neutral_count", 0)) for value in source_values
        ),
        "negative_count": sum(
            int(value.get("negative_count", 0)) for value in source_values
        ),
    }


def _cache_item_value(items_by_key: dict[str, Any], key: str, value: dict[str, Any]) -> None:
    item = items_by_key.get(key)
    if item is None:
        return
    try:
        item.value = value
    except Exception:
        items_by_key[key] = SimpleNamespace(key=key, value=value)


def _validate_source_keys(
    source_keys: list[str],
    cluster_key_set: set[str],
    items_by_key: dict[str, Any],
) -> list[str]:
    return [
        key
        for key in source_keys
        if key in cluster_key_set and key in items_by_key
    ]


def _delete_absorbed_keys(
    target_store: BaseStore,
    namespace: tuple[str, str],
    source_keys: list[str],
    survivor_keys: set[str],
    items_by_key: dict[str, Any],
    apply: bool,
) -> int:
    deleted = 0
    for key in source_keys:
        if key in survivor_keys:
            continue
        if apply:
            target_store.delete(namespace, key)
            items_by_key.pop(key, None)
        deleted += 1
    return deleted


def _apply_strategy_operation(
    target_store: BaseStore,
    namespace: tuple[str, ...],
    operation: StrategyBatchOperation,
    cluster_key_set: set[str],
    items_by_key: dict[str, Any],
    apply: bool,
) -> tuple[str, int]:
    source_keys = _validate_source_keys(
        operation.source_keys,
        cluster_key_set,
        items_by_key,
    )
    if not source_keys:
        return "failed", 0

    if operation.action == "KEEP":
        return "kept", 0

    if operation.action == "DISCARD":
        survivor_key = operation.survivor_key or source_keys[0]
        if survivor_key not in source_keys or survivor_key not in items_by_key:
            return "failed", 0
        survivor_value = dict(items_by_key[survivor_key].value)
        metadata = _merged_metadata(source_keys, items_by_key, survivor_key)
        situation = operation.merged_situation or survivor_value.get("situation", "")
        action = operation.merged_action or survivor_value.get("action", "")
        value = {
            "situation": situation,
            "action": action,
            **metadata,
        }
        if apply:
            _put_memory_with_retries(target_store, namespace, survivor_key, value)
            _cache_item_value(items_by_key, survivor_key, value)
        deleted = _delete_absorbed_keys(
            target_store,
            namespace,
            source_keys,
            {survivor_key},
            items_by_key,
            apply,
        )
        return "discarded", deleted

    return "failed", 0


def _apply_observation_operation(
    target_store: BaseStore,
    namespace: tuple[str, ...],
    operation: ObservationBatchOperation,
    cluster_key_set: set[str],
    items_by_key: dict[str, Any],
    apply: bool,
) -> tuple[str, int]:
    source_keys = _validate_source_keys(
        operation.source_keys,
        cluster_key_set,
        items_by_key,
    )
    if not source_keys:
        return "failed", 0

    if operation.action == "KEEP":
        return "kept", 0

    if operation.action in {"DISCARD", "MERGE"}:
        survivor_key = operation.survivor_key or source_keys[0]
        if survivor_key not in source_keys or survivor_key not in items_by_key:
            return "failed", 0
        survivor_value = dict(items_by_key[survivor_key].value)
        metadata = _merged_metadata(source_keys, items_by_key, survivor_key)
        situation = survivor_value.get("situation", "")
        approach = survivor_value.get("approach", "")
        outcome = survivor_value.get("outcome", "")
        if operation.action == "MERGE":
            situation = operation.merged_situation or situation
            approach = operation.merged_approach or approach
            outcome = operation.merged_outcome or outcome
        value = {
            "situation": situation,
            "approach": approach,
            "outcome": outcome,
            **metadata,
        }
        if apply:
            _put_memory_with_retries(target_store, namespace, survivor_key, value)
            _cache_item_value(items_by_key, survivor_key, value)
        deleted = _delete_absorbed_keys(
            target_store,
            namespace,
            source_keys,
            {survivor_key},
            items_by_key,
            apply,
        )
        return ("discarded" if operation.action == "DISCARD" else "merged", deleted)

    return "failed", 0


def _remap_operation_keys(
    operation: StrategyBatchOperation | ObservationBatchOperation,
    index_to_key: dict[str, str],
) -> None:
    """Translate numbered indices back to real UUID keys in-place."""
    operation.source_keys = [
        index_to_key.get(k, k) for k in operation.source_keys
    ]
    if operation.survivor_key is not None:
        operation.survivor_key = index_to_key.get(
            operation.survivor_key, operation.survivor_key,
        )

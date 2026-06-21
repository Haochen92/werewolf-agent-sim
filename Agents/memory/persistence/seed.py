from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langgraph.store.base import BaseStore, Item, PutOp

from Agents.memory.store import store

from .cache import load_cached_vectors, load_indexed_store_cache, save_indexed_store_cache
from .config import (
    DEFAULT_MEMORY_STORE_DIR,
    INDEXED_CACHE_FILE_NAME,
    _SEEDED_STORE_IDS,
    memory_store_paths,
    normalize_memory_persistence_config,
    MemoryPersistenceConfig,
)
from .retries import _batch_with_retries
from .serialization import _read_json, _snapshot_namespaces, _snapshot_value

logger = logging.getLogger(__name__)


def seed_memory_from_config(
    config: MemoryPersistenceConfig | dict[str, Any] | None = None,
    target_store: BaseStore = store,
) -> dict[str, int | bool]:
    """Seed the memory store once using a memory persistence config."""
    memory_config = normalize_memory_persistence_config(config)
    if not memory_config.seed_enabled:
        return {
            "observations": 0,
            "strategies": 0,
            "strategy_points": 0,
            "skipped": True,
        }
    # Idempotency: seed a given store object only once (batches reuse one store).
    store_id = id(target_store)
    if store_id in _SEEDED_STORE_IDS:
        return {
            "observations": 0,
            "strategies": 0,
            "strategy_points": 0,
            "skipped": True,
        }
    observations_path, strategy_points_path = memory_store_paths(
        memory_config.seed_store_dir
    )
    # Cached loader: loads precomputed vectors from indexed_cache.pkl when the JSON is
    # unchanged (no embedding API calls); falls back to embedding + writes the cache.
    counts = seed_memory_from_json_files_cached(
        observations_path=observations_path,
        strategy_points_path=strategy_points_path,
        target_store=target_store,
    )
    _SEEDED_STORE_IDS.add(store_id)
    return {**counts, "skipped": False}


def seed_memory_from_json_files_once(
    observations_path: str | Path | None = None,
    strategy_points_path: str | Path | None = None,
    target_store: BaseStore = store,
) -> dict[str, int | bool]:
    store_id = id(target_store)
    if store_id in _SEEDED_STORE_IDS:
        return {
            "observations": 0,
            "strategies": 0,
            "strategy_points": 0,
            "skipped": True,
        }

    counts = seed_memory_from_json_files(
        observations_path=observations_path,
        strategy_points_path=strategy_points_path,
        target_store=target_store,
    )
    _SEEDED_STORE_IDS.add(store_id)
    return {
        **counts,
        "skipped": False,
    }


def seed_memory_from_json_files(
    observations_path: str | Path | None = None,
    strategy_points_path: str | Path | None = None,
    target_store: BaseStore = store,
    reuse_index: dict[tuple, tuple] | None = None,
    batch_size: int = 1,
    retry_attempts: int = 5,
    retry_initial_delay: float = 1.0,
    retry_max_delay: float = 30.0,
) -> dict[str, int]:
    """Seed the active memory store from JSON snapshots.

    Snapshot entries are already deduped. Load them directly to preserve keys,
    counts, and text while indexing them in batches.
    """
    default_observations, default_strategy_points = memory_store_paths(
        DEFAULT_MEMORY_STORE_DIR
    )
    observations_path = observations_path or default_observations
    strategy_points_path = strategy_points_path or default_strategy_points

    put_ops: list[PutOp] = []
    reuse_index = reuse_index or {}
    reused = 0
    _now = datetime.now(timezone.utc)
    counts = {
        "observations": 0,
        "strategies": 0,
        "strategy_points": 0,
    }
    for path in (observations_path, strategy_points_path):
        payload = _read_json(path)
        for namespace_key, namespace_items in payload.get("namespaces", {}).items():
            raw_namespace = tuple(namespace_key.split("/"))
            namespaces = _snapshot_namespaces(raw_namespace)
            if not namespaces:
                continue
            if raw_namespace[0] == "observations":
                count_key = "observations"
            elif raw_namespace[0] == "strategy_points":
                count_key = "strategy_points"
            else:
                continue
            for item in namespace_items:
                key = item.get("key")
                value = _snapshot_value(item.get("value", item))
                if not key or value is None:
                    continue
                for namespace in namespaces:
                    cached = reuse_index.get((namespace, key))
                    if cached is not None and cached[0] == value:
                        # value unchanged -> reuse the cached embedding (identical by determinism);
                        # inject data + vectors directly, skipping the embedding API call
                        target_store._data[namespace][key] = Item(
                            value=value, key=key, namespace=namespace,
                            created_at=_now, updated_at=_now,
                        )
                        target_store._vectors[namespace][key] = cached[1]
                        reused += 1
                    else:
                        put_ops.append(PutOp(namespace, key, value))
                    counts[count_key] += 1

    for start in range(0, len(put_ops), batch_size):
        _batch_with_retries(
            target_store,
            put_ops[start : start + batch_size],
            retry_attempts=retry_attempts,
            retry_initial_delay=retry_initial_delay,
            retry_max_delay=retry_max_delay,
        )

    if reused:
        logger.info("cached-seed: reused %d vectors, embedded %d new", reused, len(put_ops))
    return counts


def seed_memory_from_json_files_cached(
    observations_path: str | Path | None = None,
    strategy_points_path: str | Path | None = None,
    target_store: BaseStore = store,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Seed the store from cache if available, otherwise from API + save cache."""
    default_observations, default_strategy_points = memory_store_paths(
        DEFAULT_MEMORY_STORE_DIR
    )
    observations_path = Path(observations_path or default_observations)
    strategy_points_path = Path(strategy_points_path or default_strategy_points)

    if cache_dir is None:
        cache_dir = observations_path.parent
    cache_path = Path(cache_dir) / INDEXED_CACHE_FILE_NAME

    if load_indexed_store_cache(
        cache_path, target_store, observations_path, strategy_points_path
    ):
        return {"from_cache": True}

    # Full cache stale (source changed). Instead of re-embedding everything, reuse the cached per-key
    # vectors for records whose value is unchanged and embed only the new/changed ones — so cost scales
    # with NEW obs, not the whole growing store.
    reuse_index = load_cached_vectors(cache_path)
    counts = seed_memory_from_json_files(
        observations_path=observations_path,
        strategy_points_path=strategy_points_path,
        target_store=target_store,
        reuse_index=reuse_index,
    )

    save_indexed_store_cache(
        target_store, cache_path, observations_path, strategy_points_path
    )
    return {**counts, "from_cache": False}

from __future__ import annotations

import logging
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langgraph.store.base import BaseStore, Item

from .serialization import _file_sha256

logger = logging.getLogger(__name__)


def save_indexed_store_cache(
    target_store: BaseStore,
    cache_path: str | Path,
    observations_path: str | Path,
    strategy_points_path: str | Path,
) -> None:
    """Serialize store data and embedding vectors to a cache file.

    The cache file includes SHA-256 hashes of the source JSON files so it can
    be invalidated when the source data changes.
    """
    cache_path = Path(cache_path)

    data_dict: dict[tuple[str, ...], dict[str, dict[str, Any]]] = {}
    for namespace, items in target_store._data.items():
        data_dict[namespace] = {}
        for key, item in items.items():
            data_dict[namespace][key] = {
                "value": item.value,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }

    vectors_dict: dict[tuple[str, ...], dict[str, dict[str, list[float]]]] = {}
    for namespace, items in target_store._vectors.items():
        vectors_dict[namespace] = {}
        for key, paths in items.items():
            vectors_dict[namespace][key] = dict(paths)

    payload = {
        "version": 1,
        "observations_sha256": _file_sha256(Path(observations_path)),
        "strategy_points_sha256": _file_sha256(Path(strategy_points_path)),
        "data": data_dict,
        "vectors": vectors_dict,
    }

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "wb") as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

    logger.info(
        "Saved indexed store cache to %s (%d bytes)",
        cache_path,
        cache_path.stat().st_size,
    )


def load_indexed_store_cache(
    cache_path: str | Path,
    target_store: BaseStore,
    observations_path: str | Path,
    strategy_points_path: str | Path,
) -> bool:
    """Load store data and vectors from a cache file.

    Returns True if the cache was valid and loaded successfully,
    False if the cache is missing, stale, or corrupt.
    """
    cache_path = Path(cache_path)
    if not cache_path.exists():
        return False

    try:
        with open(cache_path, "rb") as f:
            payload = pickle.load(f)  # noqa: S301
    except Exception:
        logger.warning("Corrupt cache file %s, will re-seed", cache_path)
        return False

    if payload.get("version") != 1:
        return False

    obs_sha = _file_sha256(Path(observations_path))
    sp_sha = _file_sha256(Path(strategy_points_path))
    if (
        payload.get("observations_sha256") != obs_sha
        or payload.get("strategy_points_sha256") != sp_sha
    ):
        logger.info("Cache stale (source files changed), will re-seed")
        return False

    now = datetime.now(timezone.utc)
    for namespace, items in payload["data"].items():
        for key, item_data in items.items():
            target_store._data[namespace][key] = Item(
                value=item_data["value"],
                key=key,
                namespace=namespace,
                created_at=datetime.fromisoformat(item_data["created_at"]) if item_data["created_at"] else now,
                updated_at=datetime.fromisoformat(item_data["updated_at"]) if item_data["updated_at"] else now,
            )

    for namespace, items in payload["vectors"].items():
        for key, paths in items.items():
            target_store._vectors[namespace][key] = paths

    logger.info(
        "Loaded indexed store from cache: %d namespaces, %d vectors",
        len(payload["data"]),
        sum(len(v) for v in payload["vectors"].values()),
    )
    return True


def load_cached_vectors(cache_path: str | Path) -> dict[tuple, tuple]:
    """Per-key vector reuse map {(namespace, key): (value, vectors)}, IGNORING the whole-file SHA gate.

    The full-cache loader above is all-or-nothing: any change to the source JSON invalidates the ENTIRE
    cache, re-embedding every record each generation (cost grows with the whole store, not the new obs).
    This returns the cached per-key embeddings so a changed store can reuse the vectors of records whose
    VALUE is unchanged — identical to re-embedding by embedding determinism (same text -> same vector) —
    and embed only the genuinely new/changed records. Returns {} if the cache is absent or corrupt.
    """
    cache_path = Path(cache_path)
    if not cache_path.exists():
        return {}
    try:
        with open(cache_path, "rb") as f:
            payload = pickle.load(f)  # noqa: S301
    except Exception:
        return {}
    if payload.get("version") != 1:
        return {}
    data = payload.get("data", {})
    vectors = payload.get("vectors", {})
    reuse: dict[tuple, tuple] = {}
    for namespace, items in vectors.items():
        for key, paths in items.items():
            entry = data.get(namespace, {}).get(key)
            if entry is not None:
                reuse[(namespace, key)] = (entry["value"], paths)
    return reuse

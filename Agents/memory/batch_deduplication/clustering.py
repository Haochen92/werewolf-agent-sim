"""Candidate-cluster construction for batch dedup.

Fetches a namespace's items, then groups near-duplicate entries into clusters via one of three
modes — connected-component (``_cluster_items``), seed-bounded (``_bounded_seed_clusters``), or
local agglomerative re-embedding (``_agglomerative_clusters``). Sort-key helpers prioritise
high-observation-count / recently-observed entries as cluster seeds.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import Any

import numpy as np
from Agents.llm_factory import create_embeddings
from langgraph.store.base import BaseStore

from Agents.memory.persistence import _memory_store_call_with_retries
from Agents.memory.dedup_gate import partition_key_for

from .config import (
    BatchDedupRunConfig,
    DEFAULT_MEMORY_STORE_RETRY_ATTEMPTS,
    DEFAULT_MEMORY_STORE_RETRY_INITIAL_DELAY,
    DEFAULT_MEMORY_STORE_RETRY_MAX_DELAY,
    LinkageMethod,
)
from .store_retry import _search_memory_with_retries

logger = logging.getLogger(__name__)


def _build_clusters(
    target_store: BaseStore,
    namespace: tuple[str, str, str],
    items_by_key: dict[str, Any],
    config: BatchDedupRunConfig,
) -> list[list[str]]:
    """v6 structured gate (tunable): pre-partition the namespace by the full dedup key (gate regime +
    pair-checks) so items in different regimes/verdicts/landscapes/exposures NEVER cluster together —
    every cluster the LLM resolves is homogeneous. gate_enabled=False falls back to the un-gated global
    clustering (legacy / v5 stores)."""
    if not config.gate_enabled:
        return _build_clusters_for_items(target_store, namespace, items_by_key, config)
    memory_kind = namespace[0]
    clusters: list[list[str]] = []
    for partition_items in _gate_partitions(items_by_key, memory_kind):
        clusters.extend(_build_clusters_for_items(target_store, namespace, partition_items, config))
    clusters.sort(key=len, reverse=True)
    return clusters


def _gate_partitions(items_by_key: dict[str, Any], memory_kind: str) -> list[dict[str, Any]]:
    """Group items by the dedup partition key for this memory kind (obs: gate+pair-checks; SP: the
    direction/honesty/valence signature). Items with no v6 fields (partition None) fall into one
    'ungated' group, clustered as before."""
    groups: dict[Any, dict[str, Any]] = defaultdict(dict)
    for key, item in items_by_key.items():
        groups[partition_key_for(memory_kind, item.value)][key] = item
    return list(groups.values())


def _build_clusters_for_items(
    target_store: BaseStore,
    namespace: tuple[str, str, str],
    items_by_key: dict[str, Any],
    config: BatchDedupRunConfig,
    seed_keys: set[str] | None = None,
) -> list[list[str]]:
    # seed_keys (synth path: seed clusters from NEW arrivals only) is honored ONLY by the bounded mode.
    # connected/agglomerative ignore it — they're inactive in the loop, and the _synth_cluster gate still
    # filters old-only clusters downstream, so correctness holds even when they seed from everything.
    if config.cluster_mode == "connected":
        return _cluster_items(
            target_store,
            namespace,
            items_by_key,
            config.similarity_threshold,
            config.search_limit,
        )
    if config.cluster_mode == "agglomerative":
        return _agglomerative_clusters(
            items_by_key,
            config.similarity_threshold,
            config.linkage_method,
            config.max_cluster_size,
            config.embedding_model,
            config.embedding_dims,
        )
    return _bounded_seed_clusters(
        target_store,
        namespace,
        items_by_key,
        config.similarity_threshold,
        config.search_limit,
        config.max_cluster_size,
        seed_keys=seed_keys,
    )


def _fetch_namespace_items(
    target_store: BaseStore,
    namespace: tuple[str, str, str],
) -> dict[str, Any]:
    items: dict[str, Any] = {}
    offset = 0
    limit = 100
    while True:
        page = _search_memory_with_retries(
            target_store,
            namespace,
            query=None,
            limit=limit,
            offset=offset,
        )
        if not page:
            break
        for item in page:
            items[item.key] = item
        offset += len(page)
        if len(page) < limit:
            break
    return items


def _cluster_items(
    target_store: BaseStore,
    namespace: tuple[str, str, str],
    items_by_key: dict[str, Any],
    threshold: float,
    search_limit: int,
) -> list[list[str]]:
    graph: dict[str, set[str]] = {key: set() for key in items_by_key}
    valid_keys = set(items_by_key)

    for key, item in items_by_key.items():
        situation = item.value.get("situation", "")
        if not situation:
            continue
        similar_items = _search_memory_with_retries(
            target_store,
            namespace,
            query=situation,
            limit=search_limit,
        )
        for similar in similar_items:
            if similar.key == key or similar.key not in valid_keys:
                continue
            if (similar.score or 0.0) < threshold:
                continue
            graph[key].add(similar.key)
            graph[similar.key].add(key)

    clusters: list[list[str]] = []
    seen: set[str] = set()
    for key in graph:
        if key in seen:
            continue
        queue = deque([key])
        seen.add(key)
        component: list[str] = []
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in graph[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        if len(component) > 1:
            clusters.append(sorted(component))

    clusters.sort(key=len, reverse=True)
    return clusters


def _bounded_seed_clusters(
    target_store: BaseStore,
    namespace: tuple[str, str, str],
    items_by_key: dict[str, Any],
    threshold: float,
    search_limit: int,
    max_cluster_size: int,
    seed_keys: set[str] | None = None,
) -> list[list[str]]:
    unprocessed = set(items_by_key)   # ALL items stay absorbable as neighbours, even non-seeds
    clusters: list[list[str]] = []
    ordered_seeds = sorted(items_by_key, key=lambda key: _seed_sort_key(key, items_by_key))
    if seed_keys is not None:   # restrict which items may SEED a cluster (synth: new arrivals only)
        ordered_seeds = [key for key in ordered_seeds if key in seed_keys]

    for seed_key in ordered_seeds:
        if seed_key not in unprocessed:
            continue

        seed_item = items_by_key[seed_key]
        situation = seed_item.value.get("situation", "")
        if not situation:
            unprocessed.remove(seed_key)
            continue

        neighbors = _search_memory_with_retries(
            target_store,
            namespace,
            query=situation,
            limit=search_limit,
        )
        candidates = [
            item
            for item in neighbors
            if item.key != seed_key
            and item.key in unprocessed
            and (item.score or 0.0) >= threshold
        ]
        candidates.sort(key=_neighbor_sort_key)

        cluster_keys = [seed_key]
        cluster_keys.extend(
            item.key for item in candidates[: max_cluster_size - 1]
        )
        for key in cluster_keys:
            unprocessed.discard(key)

        if len(cluster_keys) > 1:
            clusters.append(cluster_keys)

    clusters.sort(key=len, reverse=True)
    return clusters


def _agglomerative_clusters(
    items_by_key: dict[str, Any],
    threshold: float,
    linkage_method: LinkageMethod,
    max_cluster_size: int,
    embedding_model: str,
    embedding_dims: int,
) -> list[list[str]]:
    try:
        from scipy.cluster.hierarchy import fcluster, linkage
        from scipy.spatial.distance import squareform
    except ImportError as exc:
        raise RuntimeError(
            "Agglomerative clustering requires scipy. Install project dependencies "
            "after the pyproject update, or use --cluster-mode bounded."
        ) from exc

    keys = [
        key
        for key in sorted(items_by_key, key=lambda item_key: _seed_sort_key(item_key, items_by_key))
        if items_by_key[key].value.get("situation")
    ]
    if len(keys) < 2:
        return []

    texts = [items_by_key[key].value.get("situation", "") for key in keys]
    matrix = _normalized_embedding_matrix(texts, embedding_model, embedding_dims)
    similarity_matrix = matrix @ matrix.T
    distance_matrix = 1.0 - similarity_matrix
    np.fill_diagonal(distance_matrix, 0.0)
    distance_matrix = np.clip(distance_matrix, 0.0, 2.0)

    condensed = squareform(distance_matrix, checks=False)
    linkage_matrix = linkage(condensed, method=linkage_method)
    distance_threshold = 1.0 - threshold
    labels = fcluster(linkage_matrix, t=distance_threshold, criterion="distance")

    clusters_by_label: dict[int, list[str]] = defaultdict(list)
    for key, label in zip(keys, labels):
        clusters_by_label[int(label)].append(key)

    clusters: list[list[str]] = []
    for cluster_keys in clusters_by_label.values():
        if len(cluster_keys) < 2:
            continue
        cluster_keys.sort(key=lambda key: _seed_sort_key(key, items_by_key))
        for start in range(0, len(cluster_keys), max_cluster_size):
            chunk = cluster_keys[start : start + max_cluster_size]
            if len(chunk) > 1:
                clusters.append(chunk)

    clusters.sort(key=len, reverse=True)
    return clusters


def _normalized_embedding_matrix(
    texts: list[str],
    embedding_model: str,
    embedding_dims: int,
) -> np.ndarray:
    embeddings = _memory_store_call_with_retries(
        lambda: _get_batch_embeddings(
            embedding_model,
            embedding_dims,
        ).embed_documents(texts),
        operation_name="embed_documents",
        retry_attempts=DEFAULT_MEMORY_STORE_RETRY_ATTEMPTS,
        retry_initial_delay=DEFAULT_MEMORY_STORE_RETRY_INITIAL_DELAY,
        retry_max_delay=DEFAULT_MEMORY_STORE_RETRY_MAX_DELAY,
    )
    matrix = np.asarray(embeddings, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    matrix = matrix / np.clip(norms, 1e-12, None)
    return matrix


def _get_batch_embeddings(
    model: str,
    output_dimensionality: int,
):
    return create_embeddings(
        model,
        output_dimensionality=output_dimensionality,
    )


def _seed_sort_key(key: str, items_by_key: dict[str, Any]) -> tuple[int, float, str]:
    item = items_by_key[key]
    return (
        -_observation_count(item),
        -_last_observed_sort_value(item),
        key,
    )


def _neighbor_sort_key(item: Any) -> tuple[float, int, float, str]:
    return (
        -(item.score or 0.0),
        -_observation_count(item),
        -_last_observed_sort_value(item),
        item.key,
    )


def _observation_count(item: Any) -> int:
    try:
        return int(item.value.get("observation_count", 1))
    except Exception:
        return 1


def _last_observed_sort_value(item: Any) -> float:
    return _parse_datetime_sort_value(item.value.get("last_observed"))


def _parse_datetime_sort_value(value: Any) -> float:
    if isinstance(value, datetime):
        return value.timestamp()
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).timestamp()
        except ValueError:
            return 0.0
    return 0.0

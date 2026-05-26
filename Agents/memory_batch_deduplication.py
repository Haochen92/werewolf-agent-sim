from __future__ import annotations

import argparse
import json
import logging
import os
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

import numpy as np
from dotenv import load_dotenv
from Agents.llm_factory import create_chat_model, create_embeddings
from langgraph.store.base import BaseStore
from pydantic import BaseModel, Field

from Agents.constants import ACTION_PHASES, VALID_ACTION_PHASES_BY_ROLE, roles
from Agents.memory import store
from Agents.memory_persistence import (
    DEFAULT_MEMORY_STORE_DIR,
    dump_memory_to_json_files,
    memory_store_paths,
    _memory_store_call_with_retries,
    seed_memory_from_json_files,
)
from Agents.prompts.dedup import (
    BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT,
    BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT,
)
from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS

load_dotenv()
logger = logging.getLogger(__name__)

MemoryKind = Literal["observations", "strategy_points"]
ClusterMode = Literal["bounded", "connected", "agglomerative"]
LinkageMethod = Literal["complete", "average"]

DEFAULT_BATCH_MODEL = os.getenv("MEMORY_BATCH_DEDUP_MODEL", "gemini-2.5-pro")
DEFAULT_BATCH_THINKING_LEVEL = os.getenv("MEMORY_BATCH_DEDUP_THINKING_LEVEL", "")
DEFAULT_BATCH_EMBEDDING_MODEL = os.getenv(
    "MEMORY_BATCH_EMBEDDING_MODEL",
    "gemini-embedding-001",
)
DEFAULT_BATCH_EMBEDDING_DIMS = int(os.getenv("MEMORY_BATCH_EMBEDDING_DIMS", "1536"))
DEFAULT_BATCH_SIMILARITY_THRESHOLD = 0.70
DEFAULT_MAX_CLUSTER_SIZE = 25
DEFAULT_MEMORY_STORE_RETRY_ATTEMPTS = 5
DEFAULT_MEMORY_STORE_RETRY_INITIAL_DELAY = 1.0
DEFAULT_MEMORY_STORE_RETRY_MAX_DELAY = 30.0


class StrategyBatchOperation(BaseModel):
    action: Literal["DISCARD", "KEEP"]
    reasoning: str
    source_keys: list[str] = Field(
        description="Keys in this cluster that the operation applies to",
        min_length=1,
    )
    survivor_key: str | None = Field(
        default=None,
        description="Existing key to preserve for DISCARD",
    )
    merged_situation: str | None = Field(
        default=None,
        description=(
            "Optional improved situation text for the survivor. "
            "Use only when combining elements from multiple entries."
        ),
    )
    merged_action: str | None = Field(
        default=None,
        description=(
            "Optional improved action text for the survivor. "
            "Use only when combining elements from multiple entries."
        ),
    )


class ObservationBatchOperation(BaseModel):
    action: Literal["DISCARD", "MERGE", "KEEP"]
    reasoning: str
    source_keys: list[str] = Field(
        description="Keys in this cluster that the operation applies to",
        min_length=1,
    )
    survivor_key: str | None = Field(
        default=None,
        description="Existing key to preserve for DISCARD or MERGE",
    )
    merged_situation: str | None = Field(
        default=None,
        description="Merged situation text for MERGE",
    )
    merged_approach: str | None = Field(
        default=None,
        description=(
            "Merged approach listing all distinct tactics with counts for MERGE"
        ),
    )
    merged_outcome: str | None = Field(
        default=None,
        description="Merged outcome summarizing the shared lesson for MERGE",
    )


class StrategyBatchDedupOutput(BaseModel):
    operations: list[StrategyBatchOperation]


class ObservationBatchDedupOutput(BaseModel):
    operations: list[ObservationBatchOperation]


class NamespaceStats(BaseModel):
    memory_kind: MemoryKind
    role: str
    items: int = 0
    clusters: int = 0
    processed_clusters: int = 0
    skipped_clusters: int = 0
    operations: int = 0
    discarded: int = 0
    replaced: int = 0
    differentiated: int = 0
    merged: int = 0
    kept: int = 0
    failed: int = 0
    dry_run: bool = True


class ClusterPreview(BaseModel):
    memory_kind: MemoryKind
    role: str
    size: int
    keys: list[str]
    previews: list[str]


class BatchDedupReport(BaseModel):
    apply: bool
    seed_store_dir: str
    dump_store_dir: str
    stats: list[NamespaceStats] = Field(default_factory=list)
    clusters: list[ClusterPreview] = Field(default_factory=list)


def _langfuse_handler():
    from langfuse.langchain import CallbackHandler
    return CallbackHandler()


def _get_batch_llm(model: str, thinking_level: str | None):
    return create_chat_model(
        model,
        temperature=0.0,
        thinking_level=thinking_level,
    )


def _fetch_namespace_items(
    target_store: BaseStore,
    namespace: tuple[str, str],
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
    namespace: tuple[str, str],
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


def _parse_datetime_sort_value(value: Any) -> float:
    if isinstance(value, datetime):
        return value.timestamp()
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).timestamp()
        except ValueError:
            return 0.0
    return 0.0


def _observation_count(item: Any) -> int:
    try:
        return int(item.value.get("observation_count", 1))
    except Exception:
        return 1


def _last_observed_sort_value(item: Any) -> float:
    return _parse_datetime_sort_value(item.value.get("last_observed"))


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


def _bounded_seed_clusters(
    target_store: BaseStore,
    namespace: tuple[str, str],
    items_by_key: dict[str, Any],
    threshold: float,
    search_limit: int,
    max_cluster_size: int,
) -> list[list[str]]:
    unprocessed = set(items_by_key)
    clusters: list[list[str]] = []
    seed_keys = sorted(items_by_key, key=lambda key: _seed_sort_key(key, items_by_key))

    for seed_key in seed_keys:
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


def _get_batch_embeddings(
    model: str,
    output_dimensionality: int,
):
    return create_embeddings(
        model,
        output_dimensionality=output_dimensionality,
    )


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


def _build_clusters(
    target_store: BaseStore,
    namespace: tuple[str, str],
    items_by_key: dict[str, Any],
    threshold: float,
    search_limit: int,
    cluster_mode: ClusterMode,
    max_cluster_size: int,
    linkage_method: LinkageMethod,
    embedding_model: str,
    embedding_dims: int,
) -> list[list[str]]:
    if cluster_mode == "connected":
        return _cluster_items(
            target_store,
            namespace,
            items_by_key,
            threshold,
            search_limit,
        )
    if cluster_mode == "agglomerative":
        return _agglomerative_clusters(
            items_by_key,
            threshold,
            linkage_method,
            max_cluster_size,
            embedding_model,
            embedding_dims,
        )
    return _bounded_seed_clusters(
        target_store,
        namespace,
        items_by_key,
        threshold,
        search_limit,
        max_cluster_size,
    )


def _format_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if value:
        return str(value)
    return ""


def _format_cluster_entries(
    memory_kind: MemoryKind,
    cluster_keys: list[str],
    items_by_key: dict[str, Any],
) -> str:
    lines: list[str] = []
    for key in cluster_keys:
        value = items_by_key[key].value
        lines.append(f"KEY: {key}")
        lines.append(f"observation_count: {value.get('observation_count', 1)}")
        lines.append(f"last_observed: {_format_datetime(value.get('last_observed'))}")
        lines.append(f"situation: {value.get('situation', '')}")
        if memory_kind == "strategy_points":
            lines.append(f"action: {value.get('action', '')}")
        else:
            lines.append(f"approach: {value.get('approach', '')}")
            lines.append(f"outcome: {value.get('outcome', '')}")
        lines.append("")
    return "\n".join(lines).strip()


def _cluster_preview(
    memory_kind: MemoryKind,
    role: str,
    cluster_keys: list[str],
    items_by_key: dict[str, Any],
    preview_chars: int,
) -> ClusterPreview:
    previews: list[str] = []
    for key in cluster_keys:
        value = items_by_key[key].value
        situation = value.get("situation", "")
        preview = situation[:preview_chars]
        if len(situation) > preview_chars:
            preview += "..."
        previews.append(preview)
    return ClusterPreview(
        memory_kind=memory_kind,
        role=role,
        size=len(cluster_keys),
        keys=cluster_keys,
        previews=previews,
    )


def _latest_timestamp(values: list[Any]) -> str:
    raw_values = [_format_datetime(value) for value in values if value]
    if not raw_values:
        return datetime.now().isoformat()
    return max(raw_values)


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


def _put_memory_with_retries(
    target_store: BaseStore,
    namespace: tuple[str, str],
    key: str,
    value: dict[str, Any],
) -> None:
    _memory_store_call_with_retries(
        lambda: target_store.put(namespace, key, value),
        operation_name="put",
        retry_attempts=DEFAULT_MEMORY_STORE_RETRY_ATTEMPTS,
        retry_initial_delay=DEFAULT_MEMORY_STORE_RETRY_INITIAL_DELAY,
        retry_max_delay=DEFAULT_MEMORY_STORE_RETRY_MAX_DELAY,
    )


def _search_memory_with_retries(
    target_store: BaseStore,
    namespace: tuple[str, str],
    *,
    query: str | None,
    limit: int,
    offset: int = 0,
) -> list[Any]:
    return _memory_store_call_with_retries(
        lambda: target_store.search(
            namespace,
            query=query,
            limit=limit,
            offset=offset,
        ),
        operation_name="search",
        retry_attempts=DEFAULT_MEMORY_STORE_RETRY_ATTEMPTS,
        retry_initial_delay=DEFAULT_MEMORY_STORE_RETRY_INITIAL_DELAY,
        retry_max_delay=DEFAULT_MEMORY_STORE_RETRY_MAX_DELAY,
    )


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


def _call_cluster_llm(
    memory_kind: MemoryKind,
    role: str,
    action_phase: str,
    entries: str,
    model: str,
    thinking_level: str | None,
) -> StrategyBatchDedupOutput | ObservationBatchDedupOutput:
    llm = _get_batch_llm(model, thinking_level)
    if memory_kind == "strategy_points":
        prompt = BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT.format(
            role=role,
            action_phase=action_phase,
            entries=entries,
            situation_standards=SITUATION_STANDARDS,
            epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        )
        output_schema = StrategyBatchDedupOutput
        run_name = "batch_dedup_strategy_points"
    else:
        prompt = BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT.format(
            role=role,
            action_phase=action_phase,
            entries=entries,
            situation_standards=SITUATION_STANDARDS,
        )
        output_schema = ObservationBatchDedupOutput
        run_name = "batch_dedup_observations"

    result = llm.with_structured_output(output_schema).invoke(
        [{"role": "user", "content": prompt}],
        config={"run_name": run_name, "callbacks": [_langfuse_handler()]},
    )
    if isinstance(result, output_schema):
        return result
    if isinstance(result, dict):
        return output_schema.model_validate(result)
    raise TypeError(f"Unexpected batch dedup result type: {type(result)!r}")


def dedup_namespace(
    target_store: BaseStore,
    memory_kind: MemoryKind,
    role: str,
    action_phase: str,
    *,
    apply: bool,
    similarity_threshold: float,
    search_limit: int,
    model: str,
    thinking_level: str | None,
    cluster_mode: ClusterMode,
    max_cluster_size: int,
    linkage_method: LinkageMethod,
    embedding_model: str,
    embedding_dims: int,
    max_clusters: int | None = None,
) -> NamespaceStats:
    namespace = (memory_kind, role, action_phase)
    items_by_key = _fetch_namespace_items(target_store, namespace)
    clusters = _build_clusters(
        target_store,
        namespace,
        items_by_key,
        similarity_threshold,
        search_limit,
        cluster_mode,
        max_cluster_size,
        linkage_method,
        embedding_model,
        embedding_dims,
    )
    if max_clusters is not None:
        clusters = clusters[:max_clusters]

    if clusters:
        sizes = [len(c) for c in clusters]
        logger.info(
            "Clusters for %s/%s: %d clusters, sizes=%s",
            memory_kind, role, len(clusters), sorted(sizes, reverse=True),
        )

    stats = NamespaceStats(
        memory_kind=memory_kind,
        role=role,
        items=len(items_by_key),
        clusters=len(clusters),
        dry_run=not apply,
    )

    for cluster_keys in clusters:
        live_cluster_keys = [key for key in cluster_keys if key in items_by_key]
        if len(live_cluster_keys) < 2:
            stats.skipped_clusters += 1
            continue

        entries = _format_cluster_entries(memory_kind, live_cluster_keys, items_by_key)
        try:
            result = _call_cluster_llm(
                memory_kind,
                role,
                action_phase,
                entries,
                model,
                thinking_level,
            )
        except Exception as exc:
            logger.warning(
                "Batch dedup failed for namespace=%s role=%s cluster_size=%s: %s",
                memory_kind,
                role,
                len(live_cluster_keys),
                exc,
            )
            stats.failed += 1
            continue

        cluster_key_set = set(live_cluster_keys)
        operation_results: dict[str, int] = defaultdict(int)
        operations = result.operations
        for operation in operations:
            try:
                if memory_kind == "strategy_points":
                    status, deleted = _apply_strategy_operation(
                        target_store,
                        namespace,
                        operation,
                        cluster_key_set,
                        items_by_key,
                        apply,
                    )
                else:
                    status, deleted = _apply_observation_operation(
                        target_store,
                        namespace,
                        operation,
                        cluster_key_set,
                        items_by_key,
                        apply,
                    )
            except Exception as exc:
                logger.warning(
                    "Batch dedup apply failed for namespace=%s role=%s "
                    "operation=%s: %s",
                    memory_kind,
                    role,
                    operation.action,
                    exc,
                )
                status, deleted = "failed", 0
            operation_results[status] += 1
            if status in {"discarded", "merged"}:
                stats.operations += 1
                stats.discarded += deleted if status == "discarded" else 0
                stats.merged += deleted if status == "merged" else 0
            elif status == "kept":
                stats.kept += 1
            else:
                stats.failed += 1

        logger.info(
            "Batch dedup namespace=%s role=%s cluster_size=%s results=%s",
            memory_kind,
            role,
            len(live_cluster_keys),
            dict(operation_results),
        )
        stats.processed_clusters += 1

    return stats


def inspect_namespace_clusters(
    target_store: BaseStore,
    memory_kind: MemoryKind,
    role: str,
    action_phase: str,
    *,
    similarity_threshold: float,
    search_limit: int,
    cluster_mode: ClusterMode,
    max_cluster_size: int,
    linkage_method: LinkageMethod,
    embedding_model: str,
    embedding_dims: int,
    max_clusters: int | None = None,
    preview_chars: int = 160,
) -> tuple[NamespaceStats, list[ClusterPreview]]:
    namespace = (memory_kind, role, action_phase)
    items_by_key = _fetch_namespace_items(target_store, namespace)
    clusters = _build_clusters(
        target_store,
        namespace,
        items_by_key,
        similarity_threshold,
        search_limit,
        cluster_mode,
        max_cluster_size,
        linkage_method,
        embedding_model,
        embedding_dims,
    )
    if max_clusters is not None:
        clusters = clusters[:max_clusters]

    if clusters:
        sizes = [len(c) for c in clusters]
        logger.info(
            "Clusters for %s/%s: %d clusters, sizes=%s",
            memory_kind, role, len(clusters), sorted(sizes, reverse=True),
        )

    stats = NamespaceStats(
        memory_kind=memory_kind,
        role=role,
        items=len(items_by_key),
        clusters=len(clusters),
        dry_run=True,
    )
    previews = [
        _cluster_preview(
            memory_kind,
            role,
            cluster_keys,
            items_by_key,
            preview_chars,
        )
        for cluster_keys in clusters
    ]
    return stats, previews


def run_batch_memory_dedup(
    *,
    target_store: BaseStore = store,
    seed_store_dir: Path = DEFAULT_MEMORY_STORE_DIR,
    dump_store_dir: Path = DEFAULT_MEMORY_STORE_DIR,
    memory_kinds: list[MemoryKind] | None = None,
    selected_roles: list[str] | None = None,
    apply: bool = False,
    similarity_threshold: float = DEFAULT_BATCH_SIMILARITY_THRESHOLD,
    search_limit: int = 10,
    cluster_mode: ClusterMode = "bounded",
    max_cluster_size: int = DEFAULT_MAX_CLUSTER_SIZE,
    linkage_method: LinkageMethod = "complete",
    embedding_model: str = DEFAULT_BATCH_EMBEDDING_MODEL,
    embedding_dims: int = DEFAULT_BATCH_EMBEDDING_DIMS,
    model: str = DEFAULT_BATCH_MODEL,
    thinking_level: str | None = DEFAULT_BATCH_THINKING_LEVEL,
    max_clusters: int | None = None,
    cluster_report_only: bool = False,
    preview_chars: int = 160,
) -> BatchDedupReport:
    memory_kinds = memory_kinds or ["observations", "strategy_points"]
    selected_roles = selected_roles or list(roles)

    observations_path, strategy_points_path = memory_store_paths(seed_store_dir)
    seed_memory_from_json_files(
        observations_path=observations_path,
        strategy_points_path=strategy_points_path,
        target_store=target_store,
    )

    report = BatchDedupReport(
        apply=apply,
        seed_store_dir=str(seed_store_dir),
        dump_store_dir=str(dump_store_dir),
    )

    for memory_kind in memory_kinds:
        for role in selected_roles:
            role_phases = VALID_ACTION_PHASES_BY_ROLE.get(role, ACTION_PHASES)
            for action_phase in role_phases:
                if cluster_report_only:
                    try:
                        stats, cluster_previews = inspect_namespace_clusters(
                            target_store,
                            memory_kind,
                            role,
                            action_phase,
                            similarity_threshold=similarity_threshold,
                            search_limit=search_limit,
                            cluster_mode=cluster_mode,
                            max_cluster_size=max_cluster_size,
                            linkage_method=linkage_method,
                            embedding_model=embedding_model,
                            embedding_dims=embedding_dims,
                            max_clusters=max_clusters,
                            preview_chars=preview_chars,
                        )
                    except Exception as exc:
                        logger.warning(
                            "Batch dedup inspection failed for namespace=%s role=%s phase=%s: %s",
                            memory_kind,
                            role,
                            action_phase,
                            exc,
                        )
                        stats = NamespaceStats(
                            memory_kind=memory_kind,
                            role=role,
                            failed=1,
                            dry_run=True,
                        )
                        cluster_previews = []
                    report.stats.append(stats)
                    report.clusters.extend(cluster_previews)
                    continue

                try:
                    stats = dedup_namespace(
                        target_store,
                        memory_kind,
                        role,
                        action_phase,
                        apply=apply,
                        similarity_threshold=similarity_threshold,
                        search_limit=search_limit,
                        cluster_mode=cluster_mode,
                        max_cluster_size=max_cluster_size,
                        linkage_method=linkage_method,
                        embedding_model=embedding_model,
                        embedding_dims=embedding_dims,
                        model=model,
                        thinking_level=thinking_level,
                        max_clusters=max_clusters,
                    )
                except Exception as exc:
                    logger.warning(
                        "Batch dedup namespace failed for namespace=%s role=%s phase=%s: %s",
                        memory_kind,
                        role,
                        action_phase,
                        exc,
                    )
                    stats = NamespaceStats(
                        memory_kind=memory_kind,
                        role=role,
                        failed=1,
                        dry_run=not apply,
                    )
                report.stats.append(stats)

    if apply:
        observations_dump_path, strategy_points_dump_path = memory_store_paths(
            dump_store_dir
        )
        dump_memory_to_json_files(
            observations_path=observations_dump_path,
            strategy_points_path=strategy_points_dump_path,
            target_store=target_store,
        )

    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Periodically deduplicate Werewolf memory stores by cluster."
    )
    parser.add_argument(
        "--store-dir",
        type=Path,
        default=DEFAULT_MEMORY_STORE_DIR,
        help="Memory store directory used for both seeding and dumping.",
    )
    parser.add_argument(
        "--seed-store-dir",
        type=Path,
        default=None,
        help="Memory store directory to seed from. Defaults to --store-dir.",
    )
    parser.add_argument(
        "--dump-store-dir",
        type=Path,
        default=None,
        help="Memory store directory to dump to when --apply is set. Defaults to --store-dir.",
    )
    parser.add_argument(
        "--types",
        nargs="+",
        choices=("observations", "strategy_points"),
        default=["observations", "strategy_points"],
        help="Memory types to deduplicate.",
    )
    parser.add_argument(
        "--roles",
        nargs="+",
        choices=roles,
        default=list(roles),
        help="Roles to deduplicate.",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=DEFAULT_BATCH_SIMILARITY_THRESHOLD,
        help="Similarity threshold used to form candidate clusters.",
    )
    parser.add_argument(
        "--search-limit",
        type=int,
        default=10,
        help="Number of nearest neighbors to inspect for each memory entry.",
    )
    parser.add_argument(
        "--cluster-mode",
        choices=("bounded", "connected", "agglomerative"),
        default="bounded",
        help=(
            "Cluster construction mode. 'bounded' forms seed-centered clusters; "
            "'connected' uses full connected components; 'agglomerative' "
            "re-embeds namespace contents and clusters locally."
        ),
    )
    parser.add_argument(
        "--max-cluster-size",
        type=int,
        default=DEFAULT_MAX_CLUSTER_SIZE,
        help="Maximum entries in a bounded or agglomerative cluster.",
    )
    parser.add_argument(
        "--linkage",
        choices=("complete", "average"),
        default="complete",
        help="Linkage method for --cluster-mode agglomerative.",
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_BATCH_EMBEDDING_MODEL,
        help="Embedding model used for --cluster-mode agglomerative.",
    )
    parser.add_argument(
        "--embedding-dims",
        type=int,
        default=DEFAULT_BATCH_EMBEDDING_DIMS,
        help="Embedding dimensionality used for --cluster-mode agglomerative.",
    )
    parser.add_argument(
        "--max-clusters",
        type=int,
        default=None,
        help="Optional cap on clusters processed per namespace.",
    )
    parser.add_argument(
        "--cluster-report-only",
        action="store_true",
        help="Only report pre-merge clusters. Does not call the LLM or mutate memory.",
    )
    parser.add_argument(
        "--preview-chars",
        type=int,
        default=160,
        help="Maximum characters to include for each clustered memory preview.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_BATCH_MODEL,
        help="Gemini model used for cluster resolution.",
    )
    parser.add_argument(
        "--thinking-level",
        default=DEFAULT_BATCH_THINKING_LEVEL,
        help="Gemini thinking level. Use an empty string to omit it.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply mutations and dump the store. Without this, run a dry-run report.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=None,
        help="Optional JSON report path.",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _parse_args()
    seed_store_dir = args.seed_store_dir or args.store_dir
    dump_store_dir = args.dump_store_dir or args.store_dir
    thinking_level = args.thinking_level or None

    report = run_batch_memory_dedup(
        seed_store_dir=seed_store_dir,
        dump_store_dir=dump_store_dir,
        memory_kinds=args.types,
        selected_roles=args.roles,
        apply=args.apply,
        similarity_threshold=args.similarity_threshold,
        search_limit=args.search_limit,
        cluster_mode=args.cluster_mode,
        max_cluster_size=args.max_cluster_size,
        linkage_method=args.linkage,
        embedding_model=args.embedding_model,
        embedding_dims=args.embedding_dims,
        model=args.model,
        thinking_level=thinking_level,
        max_clusters=args.max_clusters,
        cluster_report_only=args.cluster_report_only,
        preview_chars=args.preview_chars,
    )
    report_json = json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True)
    if args.report_path:
        args.report_path.parent.mkdir(parents=True, exist_ok=True)
        args.report_path.write_text(report_json + "\n", encoding="utf-8")
    print(report_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

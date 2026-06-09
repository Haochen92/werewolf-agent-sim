"""
Batch (cluster) dedup pipeline for memory entries.

Periodically re-clusters near-duplicate observations / strategy points per
(memory_kind, role, action_phase) namespace and resolves each cluster with an LLM, optionally in a
fast-triage → targeted-verify two pass. Submodules split the pipeline by concern (schemas, config,
clustering, formatting, operations, store I/O, incremental bookkeeping, orchestration); everything
public is re-exported here so ``from Agents.memory.batch_deduplication import X`` keeps resolving.
"""

import logging

from dotenv import load_dotenv

from .clustering import (
    _agglomerative_clusters,
    _bounded_seed_clusters,
    _build_clusters,
    _cluster_items,
    _fetch_namespace_items,
    _get_batch_embeddings,
    _last_observed_sort_value,
    _neighbor_sort_key,
    _normalized_embedding_matrix,
    _observation_count,
    _parse_datetime_sort_value,
    _seed_sort_key,
)
from .config import (
    ClusterMode,
    DEDUP_TIMESTAMP_FILE,
    DEFAULT_BATCH_EMBEDDING_DIMS,
    DEFAULT_BATCH_EMBEDDING_MODEL,
    DEFAULT_BATCH_MODEL,
    DEFAULT_BATCH_SIMILARITY_THRESHOLD,
    DEFAULT_BATCH_THINKING_LEVEL,
    DEFAULT_MAX_CLUSTER_SIZE,
    DEFAULT_MEMORY_STORE_RETRY_ATTEMPTS,
    DEFAULT_MEMORY_STORE_RETRY_INITIAL_DELAY,
    DEFAULT_MEMORY_STORE_RETRY_MAX_DELAY,
    DEFAULT_TRIAGE_MODEL,
    DEFAULT_TRIAGE_THINKING_LEVEL,
    LinkageMethod,
    TwoPassConfig,
    _get_batch_llm,
    _langfuse_handler,
)
from .formatting import (
    _cluster_preview,
    _format_cluster_entries,
    _format_datetime,
    _latest_timestamp,
)
from .incremental import (
    _collect_new_keys,
    _read_last_dedup_at,
    _write_last_dedup_at,
)
from .operations import (
    _apply_observation_operation,
    _apply_strategy_operation,
    _cache_item_value,
    _delete_absorbed_keys,
    _merged_metadata,
    _remap_operation_keys,
    _validate_source_keys,
)
from .cli import _parse_args, main
from .orchestration import (
    dedup_namespace,
    inspect_namespace_clusters,
    run_batch_memory_dedup,
)
from .resolution import (
    _OBS_PROMPT_VARIANTS,
    _call_cluster_llm,
    _two_pass_cluster_dedup,
)
from .schemas import (
    BatchDedupReport,
    ClusterPreview,
    MemoryKind,
    NamespaceStats,
    ObservationBatchDedupOutput,
    ObservationBatchOperation,
    StrategyBatchDedupOutput,
    StrategyBatchOperation,
)
from .store_io import (
    _put_memory_with_retries,
    _search_memory_with_retries,
)

load_dotenv()
logger = logging.getLogger(__name__)

__all__ = [
    # schemas
    "BatchDedupReport",
    "ClusterPreview",
    "MemoryKind",
    "NamespaceStats",
    "ObservationBatchDedupOutput",
    "ObservationBatchOperation",
    "StrategyBatchDedupOutput",
    "StrategyBatchOperation",
    # config
    "ClusterMode",
    "DEDUP_TIMESTAMP_FILE",
    "DEFAULT_BATCH_EMBEDDING_DIMS",
    "DEFAULT_BATCH_EMBEDDING_MODEL",
    "DEFAULT_BATCH_MODEL",
    "DEFAULT_BATCH_SIMILARITY_THRESHOLD",
    "DEFAULT_BATCH_THINKING_LEVEL",
    "DEFAULT_MAX_CLUSTER_SIZE",
    "DEFAULT_MEMORY_STORE_RETRY_ATTEMPTS",
    "DEFAULT_MEMORY_STORE_RETRY_INITIAL_DELAY",
    "DEFAULT_MEMORY_STORE_RETRY_MAX_DELAY",
    "DEFAULT_TRIAGE_MODEL",
    "DEFAULT_TRIAGE_THINKING_LEVEL",
    "LinkageMethod",
    "TwoPassConfig",
    "_get_batch_llm",
    "_langfuse_handler",
    # incremental
    "_collect_new_keys",
    "_read_last_dedup_at",
    "_write_last_dedup_at",
    # store_io
    "_put_memory_with_retries",
    "_search_memory_with_retries",
    # clustering
    "_agglomerative_clusters",
    "_bounded_seed_clusters",
    "_build_clusters",
    "_cluster_items",
    "_fetch_namespace_items",
    "_get_batch_embeddings",
    "_last_observed_sort_value",
    "_neighbor_sort_key",
    "_normalized_embedding_matrix",
    "_observation_count",
    "_parse_datetime_sort_value",
    "_seed_sort_key",
    # formatting
    "_cluster_preview",
    "_format_cluster_entries",
    "_format_datetime",
    "_latest_timestamp",
    # operations
    "_apply_observation_operation",
    "_apply_strategy_operation",
    "_cache_item_value",
    "_delete_absorbed_keys",
    "_merged_metadata",
    "_remap_operation_keys",
    "_validate_source_keys",
    # orchestration
    "_OBS_PROMPT_VARIANTS",
    "_call_cluster_llm",
    "_parse_args",
    "_two_pass_cluster_dedup",
    "dedup_namespace",
    "inspect_namespace_clusters",
    "main",
    "run_batch_memory_dedup",
]

"""Top-level batch-dedup orchestration.

Wires cluster construction → LLM resolution (single- or two-pass) → operation application across
every (memory_kind, role, action_phase) namespace, seeding/dumping the JSON store around the run.
The CLI that drives ``run_batch_memory_dedup`` lives in cli.py.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from langgraph.store.base import BaseStore

from Agents.constants import ACTION_PHASES, VALID_ACTION_PHASES_BY_ROLE, roles
from Agents.memory.store import store
from Agents.memory.persistence import (
    dump_memory_to_json_files,
    memory_store_paths,
    seed_memory_from_json_files,
)

from .clustering import _build_clusters, _fetch_namespace_items
from .config import (
    BatchDedupRunConfig,
    ClusterMode,
    DEDUP_TIMESTAMP_FILE,
    LinkageMethod,
    TwoPassConfig,
)
from .formatting import _cluster_preview, _format_cluster_entries
from .incremental import _collect_new_keys, _read_last_dedup_at, _write_last_dedup_at
from .operations import _apply_observation_operation, _apply_strategy_operation
from .resolution import _call_cluster_llm, _two_pass_cluster_dedup
from .schemas import (
    BatchDedupReport,
    ClusterPreview,
    MemoryKind,
    NamespaceStats,
)

logger = logging.getLogger(__name__)


def run_batch_memory_dedup(
    config: BatchDedupRunConfig,
    *,
    target_store: BaseStore = store,
) -> BatchDedupReport:
    # Explode the run config into locals once; the sweep below reads them directly.
    seed_store_dir = config.seed_store_dir
    dump_store_dir = config.dump_store_dir
    apply = config.apply
    similarity_threshold = config.similarity_threshold
    search_limit = config.search_limit
    cluster_mode = config.cluster_mode
    max_cluster_size = config.max_cluster_size
    linkage_method = config.linkage_method
    embedding_model = config.embedding_model
    embedding_dims = config.embedding_dims
    model = config.model
    thinking_level = config.thinking_level
    max_clusters = config.max_clusters
    incremental = config.incremental
    cluster_report_only = config.cluster_report_only
    preview_chars = config.preview_chars
    two_pass = config.two_pass
    prompt_variant = config.prompt_variant
    memory_kinds = config.memory_kinds or ["observations", "strategy_points"]
    selected_roles = config.selected_roles or list(roles)

    observations_path, strategy_points_path = memory_store_paths(seed_store_dir)
    seed_memory_from_json_files(
        observations_path=observations_path,
        strategy_points_path=strategy_points_path,
        target_store=target_store,
    )

    new_keys: set[str] | None = None
    if incremental:
        last_dedup = _read_last_dedup_at(seed_store_dir)
        if last_dedup is None:
            logger.info("Incremental: no previous dedup timestamp found, processing all entries")
        else:
            new_keys = _collect_new_keys(seed_store_dir, last_dedup)
            logger.info(
                "Incremental: %d new keys since %s",
                len(new_keys), last_dedup.isoformat(),
            )
            if not new_keys:
                logger.info("Incremental: no new entries, nothing to do")
                return BatchDedupReport(
                    apply=apply,
                    seed_store_dir=str(seed_store_dir),
                    dump_store_dir=str(dump_store_dir),
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
                        two_pass=two_pass,
                        prompt_variant=prompt_variant,
                        new_keys=new_keys,
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
        _write_last_dedup_at(dump_store_dir)
        logger.info("Wrote dedup timestamp to %s", dump_store_dir / DEDUP_TIMESTAMP_FILE)

    return report


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
    two_pass: TwoPassConfig | None = None,
    prompt_variant: str = "default",
    new_keys: set[str] | None = None,
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

    if new_keys is not None:
        total_before = len(clusters)
        clusters = [c for c in clusters if any(k in new_keys for k in c)]
        skipped_incremental = total_before - len(clusters)
        if skipped_incremental:
            logger.info(
                "Incremental: skipped %d all-old clusters for %s/%s (%d remain)",
                skipped_incremental, memory_kind, role, len(clusters),
            )

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

        try:
            if two_pass is not None:
                result = _two_pass_cluster_dedup(
                    memory_kind,
                    role,
                    action_phase,
                    live_cluster_keys,
                    items_by_key,
                    two_pass,
                )
            else:
                entries, index_to_key = _format_cluster_entries(
                    memory_kind, live_cluster_keys, items_by_key,
                )
                result = _call_cluster_llm(
                    memory_kind,
                    role,
                    action_phase,
                    entries,
                    index_to_key,
                    model,
                    thinking_level,
                    prompt_variant=prompt_variant,
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

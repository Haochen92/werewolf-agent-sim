"""Top-level batch-dedup orchestration.

Wires cluster construction → LLM resolution (single- or two-pass) → operation application across
every (memory_kind, role, action_phase) namespace, seeding/dumping the JSON store around the run.
The CLI that drives ``run_batch_memory_dedup`` lives in cli.py.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from langgraph.store.base import BaseStore

from Agents.schemas.roles import ACTION_PHASES, VALID_ACTION_PHASES_BY_ROLE, roles
from Agents.memory.store import store
from Agents.memory.persistence import (
    dump_memory_to_json_files,
    memory_store_paths,
    seed_memory_from_json_files,
)

from .clustering import _build_clusters, _fetch_namespace_items
from .config import BatchDedupRunConfig, DEDUP_TIMESTAMP_FILE
from .formatting import _cluster_preview, _format_cluster_entries
from .incremental import _collect_new_keys, _read_last_dedup_at, _write_last_dedup_at
from .operations import _apply_observation_operation, _apply_strategy_operation
from .cluster_agent import _cluster_agent, _two_pass_cluster_dedup
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
    memory_kinds = config.memory_kinds or ["observations", "strategy_points"]
    selected_roles = config.selected_roles or list(roles)

    observations_path, strategy_points_path = memory_store_paths(config.seed_store_dir)
    seed_memory_from_json_files(
        observations_path=observations_path,
        strategy_points_path=strategy_points_path,
        target_store=target_store,
    )

    report = BatchDedupReport(
        apply=config.apply,
        seed_store_dir=str(config.seed_store_dir),
        dump_store_dir=str(config.dump_store_dir),
    )

    new_keys: set[str] | None = None
    if config.incremental:
        last_dedup = _read_last_dedup_at(config.seed_store_dir)
        if last_dedup is None:
            logger.info("Incremental: no previous dedup timestamp found, processing all entries")
        else:
            new_keys = _collect_new_keys(config.seed_store_dir, last_dedup)
            logger.info(
                "Incremental: %d new keys since %s",
                len(new_keys), last_dedup.isoformat(),
            )
            if not new_keys:
                logger.info("Incremental: no new entries, nothing to do")
                return report

    for memory_kind in memory_kinds:
        for role in selected_roles:
            role_phases = VALID_ACTION_PHASES_BY_ROLE.get(role, ACTION_PHASES)
            for action_phase in role_phases:
                if config.cluster_report_only:
                    try:
                        stats, cluster_previews = inspect_namespace_clusters(
                            target_store, memory_kind, role, action_phase, config,
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
                        target_store, memory_kind, role, action_phase, config,
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
                        dry_run=not config.apply,
                    )
                report.stats.append(stats)

    if config.apply:
        observations_dump_path, strategy_points_dump_path = memory_store_paths(
            config.dump_store_dir
        )
        dump_memory_to_json_files(
            observations_path=observations_dump_path,
            strategy_points_path=strategy_points_dump_path,
            target_store=target_store,
        )
        _write_last_dedup_at(config.dump_store_dir)
        logger.info(
            "Wrote dedup timestamp to %s", config.dump_store_dir / DEDUP_TIMESTAMP_FILE
        )

    return report


def dedup_namespace(
    target_store: BaseStore,
    memory_kind: MemoryKind,
    role: str,
    action_phase: str,
    config: BatchDedupRunConfig,
    *,
    new_keys: set[str] | None = None,
) -> NamespaceStats:
    namespace = (memory_kind, role, action_phase)
    items_by_key, clusters = _collect_namespace_clusters(target_store, namespace, config)

    if new_keys is not None:
        total_before = len(clusters)
        clusters = [c for c in clusters if any(k in new_keys for k in c)]
        skipped_incremental = total_before - len(clusters)
        if skipped_incremental:
            logger.info(
                "Incremental: skipped %d all-old clusters for %s/%s (%d remain)",
                skipped_incremental, memory_kind, role, len(clusters),
            )

    _log_cluster_sizes(memory_kind, role, clusters)

    stats = NamespaceStats(
        memory_kind=memory_kind,
        role=role,
        items=len(items_by_key),
        clusters=len(clusters),
        dry_run=not config.apply,
    )

    for cluster_keys in clusters:
        live_cluster_keys = [key for key in cluster_keys if key in items_by_key]
        if len(live_cluster_keys) < 2:
            stats.skipped_clusters += 1
            continue

        try:
            if config.two_pass is not None:
                result = _two_pass_cluster_dedup(
                    memory_kind,
                    role,
                    action_phase,
                    live_cluster_keys,
                    items_by_key,
                    config.two_pass,
                )
            else:
                entries, index_to_key = _format_cluster_entries(
                    memory_kind, live_cluster_keys, items_by_key,
                )
                result = _cluster_agent(
                    memory_kind,
                    role,
                    action_phase,
                    entries,
                    index_to_key,
                    config.model,
                    config.thinking_level,
                    prompt_variant=config.prompt_variant,
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

        _apply_cluster_operations(
            target_store,
            namespace,
            result.operations,
            live_cluster_keys,
            items_by_key,
            config.apply,
            stats,
            new_keys=new_keys,
        )
        stats.processed_clusters += 1

    return stats


def _apply_cluster_operations(
    target_store: BaseStore,
    namespace: tuple[str, str, str],
    operations,
    live_cluster_keys: list[str],
    items_by_key: dict,
    apply: bool,
    stats: NamespaceStats,
    *,
    new_keys: set[str] | None = None,
) -> None:
    memory_kind, role, _ = namespace
    apply_operation = (
        _apply_strategy_operation
        if memory_kind == "strategy_points"
        else _apply_observation_operation
    )
    cluster_key_set = set(live_cluster_keys)
    operation_results: dict[str, int] = defaultdict(int)
    for operation in operations:
        try:
            status, deleted = apply_operation(
                target_store,
                namespace,
                operation,
                cluster_key_set,
                items_by_key,
                apply,
                new_keys,
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
        elif status == "frozen":
            stats.frozen += 1
        else:
            stats.failed += 1

    logger.info(
        "Batch dedup namespace=%s role=%s cluster_size=%s results=%s",
        memory_kind,
        role,
        len(live_cluster_keys),
        dict(operation_results),
    )


def inspect_namespace_clusters(
    target_store: BaseStore,
    memory_kind: MemoryKind,
    role: str,
    action_phase: str,
    config: BatchDedupRunConfig,
) -> tuple[NamespaceStats, list[ClusterPreview]]:
    namespace = (memory_kind, role, action_phase)
    items_by_key, clusters = _collect_namespace_clusters(target_store, namespace, config)
    _log_cluster_sizes(memory_kind, role, clusters)

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
            config.preview_chars,
        )
        for cluster_keys in clusters
    ]
    return stats, previews


def _collect_namespace_clusters(
    target_store: BaseStore,
    namespace: tuple[str, str, str],
    config: BatchDedupRunConfig,
) -> tuple[dict, list[list[str]]]:
    items_by_key = _fetch_namespace_items(target_store, namespace)
    clusters = _build_clusters(target_store, namespace, items_by_key, config)
    if config.max_clusters is not None:
        clusters = clusters[: config.max_clusters]
    return items_by_key, clusters


def _log_cluster_sizes(memory_kind: MemoryKind, role: str, clusters: list[list[str]]) -> None:
    if not clusters:
        return
    sizes = [len(c) for c in clusters]
    logger.info(
        "Clusters for %s/%s: %d clusters, sizes=%s",
        memory_kind, role, len(clusters), sorted(sizes, reverse=True),
    )

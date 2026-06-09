"""Top-level batch-dedup orchestration + CLI entrypoint.

Wires cluster construction → LLM resolution (single- or two-pass) → operation application across
every (memory_kind, role, action_phase) namespace, seeding/dumping the JSON store around the run.
This is the only module that runs as a script.
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from langgraph.store.base import BaseStore

from Agents.constants import ACTION_PHASES, VALID_ACTION_PHASES_BY_ROLE, roles
from Agents.memory.store import store
from Agents.memory.persistence import (
    DEFAULT_MEMORY_STORE_DIR,
    dump_memory_to_json_files,
    memory_store_paths,
    seed_memory_from_json_files,
)
from Agents.prompts.dedup import (
    BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT,
    BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT_LITE,
    BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT,
)
from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS

from .clustering import _build_clusters, _fetch_namespace_items
from .config import (
    ClusterMode,
    DEFAULT_BATCH_EMBEDDING_DIMS,
    DEFAULT_BATCH_EMBEDDING_MODEL,
    DEFAULT_BATCH_MODEL,
    DEFAULT_BATCH_SIMILARITY_THRESHOLD,
    DEFAULT_BATCH_THINKING_LEVEL,
    DEFAULT_MAX_CLUSTER_SIZE,
    DEFAULT_TRIAGE_MODEL,
    DEFAULT_TRIAGE_THINKING_LEVEL,
    DEDUP_TIMESTAMP_FILE,
    LinkageMethod,
    TwoPassConfig,
    _get_batch_llm,
    _langfuse_handler,
)
from .formatting import _cluster_preview, _format_cluster_entries
from .incremental import _collect_new_keys, _read_last_dedup_at, _write_last_dedup_at
from .operations import _apply_observation_operation, _apply_strategy_operation, _remap_operation_keys
from .schemas import (
    BatchDedupReport,
    ClusterPreview,
    MemoryKind,
    NamespaceStats,
    ObservationBatchDedupOutput,
    StrategyBatchDedupOutput,
)

_OBS_PROMPT_VARIANTS = {
    "default": BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT,
    "lite": BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT_LITE,
}

logger = logging.getLogger(__name__)


def _call_cluster_llm(
    memory_kind: MemoryKind,
    role: str,
    action_phase: str,
    entries: str,
    index_to_key: dict[str, str],
    model: str,
    thinking_level: str | None,
    prompt_variant: str = "default",
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
        obs_prompt_template = _OBS_PROMPT_VARIANTS.get(
            prompt_variant, BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT,
        )
        prompt = obs_prompt_template.format(
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
        pass
    elif isinstance(result, dict):
        result = output_schema.model_validate(result)
    else:
        raise TypeError(f"Unexpected batch dedup result type: {type(result)!r}")

    for op in result.operations:
        _remap_operation_keys(op, index_to_key)
    return result


def _two_pass_cluster_dedup(
    memory_kind: MemoryKind,
    role: str,
    action_phase: str,
    live_cluster_keys: list[str],
    items_by_key: dict[str, Any],
    two_pass: TwoPassConfig,
) -> StrategyBatchDedupOutput | ObservationBatchDedupOutput:
    """Run two-pass dedup on a single cluster.

    Pass 1: triage model classifies all entries.
    Pass 2: verify model re-evaluates only MERGE-flagged entries.
    Returns a combined output with trusted + verified operations.
    """
    entries, index_to_key = _format_cluster_entries(
        memory_kind, live_cluster_keys, items_by_key,
    )

    triage_result = _call_cluster_llm(
        memory_kind, role, action_phase, entries, index_to_key,
        model=two_pass.triage_model,
        thinking_level=two_pass.triage_thinking_level,
    )

    trusted_ops = []
    merge_keys: set[str] = set()

    for op in triage_result.operations:
        if op.action == "MERGE":
            merge_keys.update(op.source_keys)
        else:
            trusted_ops.append(op)

    if not merge_keys:
        return triage_result

    logger.info(
        "Two-pass: triage flagged %d keys as MERGE in cluster of %d, "
        "escalating to verify model",
        len(merge_keys), len(live_cluster_keys),
    )

    verify_keys = [k for k in live_cluster_keys if k in merge_keys]
    if len(verify_keys) < 2:
        for op in triage_result.operations:
            if op.action == "MERGE":
                op.action = "KEEP"
                op.merged_situation = None
                op.survivor_key = None
                if hasattr(op, "merged_approach"):
                    op.merged_approach = None
                if hasattr(op, "merged_outcome"):
                    op.merged_outcome = None
                if hasattr(op, "merged_action"):
                    op.merged_action = None
        return triage_result

    verify_entries, verify_index_to_key = _format_cluster_entries(
        memory_kind, verify_keys, items_by_key,
    )
    verify_result = _call_cluster_llm(
        memory_kind, role, action_phase, verify_entries, verify_index_to_key,
        model=two_pass.verify_model,
        thinking_level=two_pass.verify_thinking_level,
    )

    all_ops = trusted_ops + list(verify_result.operations)
    if memory_kind == "strategy_points":
        return StrategyBatchDedupOutput(operations=all_ops)
    return ObservationBatchDedupOutput(operations=all_ops)


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
    incremental: bool = False,
    cluster_report_only: bool = False,
    preview_chars: int = 160,
    two_pass: TwoPassConfig | None = None,
    prompt_variant: str = "default",
) -> BatchDedupReport:
    memory_kinds = memory_kinds or ["observations", "strategy_points"]
    selected_roles = selected_roles or list(roles)

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
        "--incremental",
        action="store_true",
        help="Only process clusters containing entries added since the last dedup run.",
    )
    parser.add_argument(
        "--two-pass",
        action="store_true",
        help="Enable two-pass pipeline: fast triage model → targeted verification model.",
    )
    parser.add_argument(
        "--triage-model",
        default=DEFAULT_TRIAGE_MODEL,
        help="Triage model for two-pass mode (pass 1).",
    )
    parser.add_argument(
        "--triage-thinking-level",
        default=DEFAULT_TRIAGE_THINKING_LEVEL,
        help="Thinking level for triage model.",
    )
    parser.add_argument(
        "--verify-model",
        default=DEFAULT_BATCH_MODEL,
        help="Verification model for two-pass mode (pass 2).",
    )
    parser.add_argument(
        "--verify-thinking-level",
        default=DEFAULT_BATCH_THINKING_LEVEL,
        help="Thinking level for verification model.",
    )
    parser.add_argument(
        "--prompt-variant",
        default="default",
        choices=list(_OBS_PROMPT_VARIANTS.keys()),
        help="Observation prompt variant (default: standard v3 prompts).",
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

    two_pass_config = None
    if args.two_pass:
        two_pass_config = TwoPassConfig(
            triage_model=args.triage_model,
            triage_thinking_level=args.triage_thinking_level or None,
            verify_model=args.verify_model,
            verify_thinking_level=args.verify_thinking_level or None,
        )

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
        two_pass=two_pass_config,
        prompt_variant=args.prompt_variant,
        incremental=args.incremental,
    )
    report_json = json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True)
    if args.report_path:
        args.report_path.parent.mkdir(parents=True, exist_ok=True)
        args.report_path.write_text(report_json + "\n", encoding="utf-8")
    print(report_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

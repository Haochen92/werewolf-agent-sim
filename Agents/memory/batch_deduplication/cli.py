"""Command-line entry point for the batch-dedup pipeline.

Parses args into a ``run_batch_memory_dedup`` call and prints/writes the JSON report. This is the
only module that runs as a script; ``scripts/dedup_memory_store.py`` and the ``memory-batch-dedup``
console script both land here via the package's re-exported ``main``.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from Agents.constants import roles
from Agents.memory.persistence import DEFAULT_MEMORY_STORE_DIR

from .config import (
    DEFAULT_BATCH_EMBEDDING_DIMS,
    DEFAULT_BATCH_EMBEDDING_MODEL,
    DEFAULT_BATCH_MODEL,
    DEFAULT_BATCH_SIMILARITY_THRESHOLD,
    DEFAULT_BATCH_THINKING_LEVEL,
    DEFAULT_MAX_CLUSTER_SIZE,
    DEFAULT_TRIAGE_MODEL,
    DEFAULT_TRIAGE_THINKING_LEVEL,
    TwoPassConfig,
)
from .orchestration import run_batch_memory_dedup
from .resolution import _OBS_PROMPT_VARIANTS


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


if __name__ == "__main__":
    raise SystemExit(main())

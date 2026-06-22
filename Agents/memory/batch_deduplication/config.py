"""Config for the batch (cluster) dedup pipeline.

Env-driven defaults, the cluster-mode/linkage type aliases, TwoPassConfig (which defaults to
these constants), and the full run spec (BatchDedupRunConfig). ``load_dotenv()`` runs here so
the env-driven constants resolve before anything imports them.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from Agents.memory.persistence import DEFAULT_MEMORY_STORE_DIR
from pydantic import BaseModel

from .schemas import MemoryKind

load_dotenv()

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
DEFAULT_MAX_CLUSTER_SIZE = 15
DEFAULT_MEMORY_STORE_RETRY_ATTEMPTS = 5
DEFAULT_MEMORY_STORE_RETRY_INITIAL_DELAY = 1.0
DEFAULT_MEMORY_STORE_RETRY_MAX_DELAY = 30.0

DEFAULT_TRIAGE_MODEL = "gemini-3.1-flash-lite"
DEFAULT_TRIAGE_THINKING_LEVEL = "low"

DEDUP_TIMESTAMP_FILE = ".last_dedup_at"


class TwoPassConfig(BaseModel):
    """Configuration for two-pass batch dedup: fast triage + targeted verification.

    Pass 1 (triage): cheap/fast model classifies all entries. KEEP and DISCARD
    decisions are trusted. MERGE decisions are escalated to pass 2.

    Pass 2 (verify): slower/smarter model re-evaluates only the MERGE-flagged
    entries and writes merge text where appropriate.
    """

    triage_model: str = DEFAULT_TRIAGE_MODEL
    triage_thinking_level: str | None = DEFAULT_TRIAGE_THINKING_LEVEL
    verify_model: str = DEFAULT_BATCH_MODEL
    verify_thinking_level: str | None = DEFAULT_BATCH_THINKING_LEVEL or None
    skip_verify: bool = False
    """Run pass 1 (triage) ONLY and skip pass 2 (the verify/MERGE model). Triage's KEEP/DISCARD are
    applied (exact dups still collapse + count-bump); anything triage flags MERGE downgrades to KEEP (both
    entries stay, no merge text written, no verify-model call). Use this for observations when we want NO
    merge at all — flash-lite triage is reliable for KEEP/DISCARD but loses nuance writing merged text, so
    we keep near-dups separate rather than let it fuse them. Cheap (single flash-lite pass)."""


class BatchDedupRunConfig(BaseModel):
    """The full parameter surface for one ``run_batch_memory_dedup`` invocation — the runner's
    config object that every adapter builds.

    cli.py builds it from argparse; the post-game pipeline (``persistence.dump``) builds it from its
    own ``persistence.config.IncrementalDedupConfig`` gate. That gate is deliberately the small
    graph-facing on/off subset (enabled + which models); this is the complete run spec (I/O dirs,
    clustering, embedding, resolution, run-mode). Field defaults mirror the module constants above —
    i.e. the previous ``run_batch_memory_dedup`` keyword defaults, verbatim, so the reshape is neutral.
    """

    # I/O — the seed/dump store directories (provenance = store identity).
    seed_store_dir: Path = DEFAULT_MEMORY_STORE_DIR
    dump_store_dir: Path = DEFAULT_MEMORY_STORE_DIR
    # Selection — None means "all kinds / all roles".
    memory_kinds: list[MemoryKind] | None = None
    selected_roles: list[str] | None = None
    # Clustering.
    similarity_threshold: float = DEFAULT_BATCH_SIMILARITY_THRESHOLD
    search_limit: int = 10
    cluster_mode: ClusterMode = "bounded"
    max_cluster_size: int = DEFAULT_MAX_CLUSTER_SIZE
    linkage_method: LinkageMethod = "complete"
    # v6 structured gate: pre-partition the namespace by the gate key + pair-checks before clustering,
    # so clusters are homogeneous (no cross-regime/verdict/landscape/exposure merges). Tunable —
    # turn OFF to fall back to the un-gated global clustering (legacy / v5 stores).
    gate_enabled: bool = True
    embedding_model: str = DEFAULT_BATCH_EMBEDDING_MODEL
    embedding_dims: int = DEFAULT_BATCH_EMBEDDING_DIMS
    max_clusters: int | None = None
    # Resolution — single-pass model + optional two-pass escalation.
    model: str = DEFAULT_BATCH_MODEL
    thinking_level: str | None = DEFAULT_BATCH_THINKING_LEVEL
    two_pass: TwoPassConfig | None = None
    prompt_variant: str = "default"
    # Run mode.
    apply: bool = False
    incremental: bool = False
    cluster_report_only: bool = False
    preview_chars: int = 160

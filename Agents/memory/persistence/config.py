from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

# Repo-root data directory (sibling of models/, batch_results/, evaluation/), NOT
# inside the Agents/ code package. Anchored to the repo root (parents[3] =
# .../Agents/memory/persistence/<file>.py -> repo root) so it survives file moves —
# unlike the former __file__.parent form, which silently broke when this module
# moved into the memory/ subpackage.
MEMORY_STORES_DIR = Path(__file__).resolve().parents[3] / "memory_stores"
DEFAULT_MEMORY_STORE_DIR = MEMORY_STORES_DIR / "v1_post_dedup"
OBSERVATIONS_FILE_NAME = "observations.json"
STRATEGY_POINTS_FILE_NAME = "strategy_points.json"
INDEXED_CACHE_FILE_NAME = "indexed_cache.pkl"
_SEEDED_STORE_IDS: set[int] = set()
_TRANSIENT_MEMORY_STORE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_TRANSIENT_MEMORY_STORE_ERROR_MARKERS = (
    "408",
    "429",
    "500",
    "502",
    "503",
    "504",
    "bad gateway",
    "connection reset",
    "deadline",
    "rate limit",
    "server error",
    "service unavailable",
    "temporar",
    "timeout",
    "too many requests",
)


class IncrementalDedupConfig(BaseModel):
    """Gate for the post-game *incremental* batch dedup — the routine maintenance pass run from the
    orchestrator's post-game node (``run_batch_dedup_from_config`` → ``run_batch_memory_dedup`` with
    ``incremental=True``: only clusters with entries added since the last ``.last_dedup_at`` are
    touched). This is the small graph-facing subset (on/off + which models); the full run spec is
    ``batch_deduplication.config.BatchDedupRunConfig``. ``enabled`` defaults False, so the pass is
    wired but dormant unless a run turns it on. Whole-store dedup is the CLI default instead."""

    enabled: bool = False
    two_pass: bool = True
    triage_model: str = "gemini-3.1-flash-lite"
    triage_thinking_level: str | None = "medium"
    verify_model: str = "gemini-2.5-pro"
    verify_thinking_level: str | None = None
    prompt_variant: str = "default"


class ExtractionConfig(BaseModel):
    """How post-game extraction runs (the v5 lever).

    ``per_role`` (default, the v5 way) fans the extraction out over the six roles
    in concurrent LLM calls, each sharing one byte-identical role-neutral prefix —
    the unit that explicit prefix caching reuses across the six calls. The old
    single-shot path (one all-roles prompt) is kept runnable for A/B by setting
    ``per_role=False``. ``cache_prefix`` creates a Vertex context cache from that
    shared prefix so the concurrent calls hit it instead of re-sending it; it is
    best-effort (falls back to the full uncached prompt) and only applies when
    ``per_role`` is on.
    """

    per_role: bool = True
    cache_prefix: bool = True
    max_workers: int = 6


class MemoryPersistenceConfig(BaseModel):
    """Seed/dump settings for the process-global LangGraph memory store.

    Normal graph runs use the v1 post-dedup store. Batch experiments can point
    seed and dump directories at another versioned store without changing code.
    """

    seed_enabled: bool = True
    dump_enabled: bool = True
    seed_store_dir: Path = DEFAULT_MEMORY_STORE_DIR
    dump_store_dir: Path = DEFAULT_MEMORY_STORE_DIR
    batch_dedup: IncrementalDedupConfig = IncrementalDedupConfig()
    extraction: ExtractionConfig = ExtractionConfig()


def normalize_memory_persistence_config(
    config: MemoryPersistenceConfig | dict[str, Any] | None,
) -> MemoryPersistenceConfig:
    """Return a concrete memory persistence config with project defaults."""
    if config is None:
        return MemoryPersistenceConfig()
    if isinstance(config, MemoryPersistenceConfig):
        return config
    return MemoryPersistenceConfig.model_validate(config)


def memory_persistence_config_from_runnable(
    config: dict[str, Any] | None,
) -> MemoryPersistenceConfig:
    """Read memory persistence settings from LangGraph runnable config."""
    configurable = config.get("configurable", {}) if config else {}
    return normalize_memory_persistence_config(
        configurable.get("memory_persistence_config")
    )


def memory_store_paths(store_dir: str | Path) -> tuple[Path, Path]:
    """Return observation and strategy-point paths for an episodic store dir."""
    store_dir = Path(store_dir)
    return (
        store_dir / OBSERVATIONS_FILE_NAME,
        store_dir / STRATEGY_POINTS_FILE_NAME,
    )

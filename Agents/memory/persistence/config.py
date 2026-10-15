from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# Repo-root data directory (sibling of models/, batch_results/, evaluation/), NOT
# inside the Agents/ code package. Anchored to the repo root (parents[3] =
# .../Agents/memory/persistence/<file>.py -> repo root) so it survives file moves —
# unlike the former __file__.parent form, which silently broke when this module
# moved into the memory/ subpackage.
MEMORY_STORES_DIR = Path(__file__).resolve().parents[3] / "memory_stores"
# Canonical live store = the v6 cell store (seed + dump default). v6_1 = QC prompts + gate enums +
# dimensions + per_run SPs; not git-tracked (built offline by reextract_cells). Batch runs still
# override seed_store_dir / dump_store_dir per-run; a dump that shouldn't compound into the canonical
# store should point dump_store_dir at a throwaway copy.
DEFAULT_MEMORY_STORE_DIR = MEMORY_STORES_DIR / "v6_1"
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
    triage_model: str = "anthropic/claude-haiku-5-5"
    triage_thinking_level: str | None = "medium"
    verify_model: str = "anthropic/claude-sonnet-5-5"
    verify_thinking_level: str | None = None
    prompt_variant: str = "default"


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() not in ("0", "false", "no", "off", "")


class DehaloConfig(BaseModel):
    """The de-halo pass after extraction (Agents/memory/extraction/dehalo.py): a second model
    rewrites verdicts the game record does not support. Each field defaults from the environment,
    so a deployment or a batch can change it without code; a run's config records what was used."""

    enabled: bool = Field(default_factory=lambda: _env_flag("MEMORY_DEHALO_ENABLED", True))
    """On by default (v8, 2026-10-11). MEMORY_DEHALO_ENABLED=0 turns it off."""
    model: str = Field(default_factory=lambda: os.getenv("MEMORY_DEHALO_MODEL") or "claude-haiku-5-5")
    """A claude-* model goes through the Anthropic SDK (CLAUDE_API_KEY); any other through the
    game's model factory. claude-haiku-5-5 was the most precise judge on the v8 smoke game, at about
    $0.006 a game."""
    thinking_level: str | None = Field(default_factory=lambda: os.getenv("MEMORY_DEHALO_THINKING_LEVEL") or None)
    """None = the model's default. On Claude: minimal/off disables thinking, low..max sets adaptive
    thinking at that effort. On other models: the factory's thinking level."""


class ExtractionConfig(BaseModel):
    """How post-game extraction runs.

    The LIVE graph now runs the v6 per-CELL fan-out (``extract_postgame_per_cell``): one dual
    {observations, strategy_points} call per (role, phase) cell over a byte-identical cell prefix.
    ``cache_prefix`` creates a Vertex context cache from that shared prefix so the concurrent cell
    calls hit it instead of re-sending it (best-effort; falls back to the full uncached prompt);
    ``max_workers`` caps the cell concurrency. ``per_role`` is no longer read by the live graph —
    it (and the v5 single-shot path) survive only for the offline store-builders / experiments that
    still extract the v5 GameStrategyOutput schema.
    """

    per_role: bool = True
    cache_prefix: bool = True
    max_workers: int = 6
    extract_without_dump: bool = False
    # When dump is OFF, normally extraction is skipped (wasted cost). Set this to run +
    # trace extraction anyway WITHOUT persisting — for measuring per-role fan-out + cache
    # cost on a throwaway game, and for a served memory-on game, whose replay shows what
    # the game taught (the memory_extracted stream chunk) without ever writing the store.
    dehalo: DehaloConfig = Field(default_factory=DehaloConfig)


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

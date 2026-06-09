"""Config-driven feature gates for memory enrichment.

These predicates read the per-role/per-kind routing off the runnable config and
are the Phase C independent variable — covered by
tests/test_memory_enrichment_gating.py.
"""
from __future__ import annotations

from langchain_core.runnables import RunnableConfig


def _memory_enabled_for_role(config: RunnableConfig, role: str) -> bool:
    configurable = config.get("configurable", {}) if config else {}
    memory_config = configurable.get("memory_config")
    if not isinstance(memory_config, dict):
        return True
    return bool(memory_config.get(role, False))


def _reranking_enabled_for_memory_kind(
    config: RunnableConfig,
    role: str,
    memory_kind: str,
) -> bool:
    configurable = config.get("configurable", {}) if config else {}
    reranking_config = configurable.get("reranking_config")
    if not isinstance(reranking_config, dict):
        return False
    if isinstance(reranking_config.get(memory_kind), dict):
        return bool(reranking_config[memory_kind].get(role, False))
    return False


def _filtering_enabled_for_role(config: RunnableConfig, role: str) -> bool:
    configurable = config.get("configurable", {}) if config else {}
    filtering_config = configurable.get("filtering_config")
    if not isinstance(filtering_config, dict):
        return False
    return bool(filtering_config.get(role, False))


def _retrieval_type_enabled(config: RunnableConfig, memory_kind: str) -> bool:
    configurable = config.get("configurable", {}) if config else {}
    retrieval_types_config = configurable.get("retrieval_types_config")
    if not isinstance(retrieval_types_config, dict):
        return True
    return bool(retrieval_types_config.get(memory_kind, True))


def _store_dir_from_config(config: RunnableConfig) -> str:
    """The seeded store directory = the store identity (provenance gap #4).

    Lives on ``memory_persistence_config`` in the runnable config (a
    ``MemoryPersistenceConfig`` or a plain dict, depending on call site).
    """
    configurable = (config or {}).get("configurable", {}) or {}
    mpc = configurable.get("memory_persistence_config")
    if mpc is None:
        return ""
    seed = getattr(mpc, "seed_store_dir", None)
    if seed is None and isinstance(mpc, dict):
        seed = mpc.get("seed_store_dir")
    return str(seed) if seed else ""

"""Config-driven retrieval-plan gating: what this turn's memory retrieval should do.

``retrieval_plan`` reads the per-role/per-kind routing off the runnable config (plus the day-1 /
no-store / role-off skip) and returns a frozen ``RetrievalPlan`` the read-path pipeline executes. The
underlying predicates are the Phase C independent variable — covered by
tests/test_memory_plan_gating.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.runnables import RunnableConfig

from Agents.state import (
    HealerDayState,
    InvestigatorDayState,
    VillagerDayState,
    WolfDayState,
)

_DayPayload = VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState


@dataclass(frozen=True)
class RetrievalPlan:
    """The per-turn retrieval policy derived from config + payload state. Gating builds it; the
    pipeline executes it. ``skip_reason`` set ⇒ retrieval is skipped entirely this turn."""

    skip_reason: str | None
    """Why retrieval is skipped (day_1 / no_store / memory_disabled_for_role), or None to proceed."""
    store_dir: str
    """The seeded store directory = the store identity (provenance), for the trace record."""
    retrieve_observations: bool
    """Whether to retrieve observations this turn."""
    retrieve_strategy: bool
    """Whether to retrieve strategy points this turn."""
    observation_reranking: bool
    """Whether to LLM-rerank observations."""
    strategy_point_reranking: bool
    """Whether to LLM-rerank strategy points."""
    filtering: bool
    """Whether to apply dedup/MMR filtering."""
    dimension_gating: bool
    """Whether to soft-reweight retrieved memory by query↔stored dimension alignment (v7 retrieval
    precision lever; SOFT + selective, never a hard drop). Default off — a screened knob."""
    reranking: bool
    """Derived: observation_reranking or strategy_point_reranking."""
    needs_wide_retrieval: bool
    """Derived: reranking or filtering or dimension_gating — drives the wide (top-k) retrieval +
    candidate snapshot (gating must see beyond top-5 to promote a dim-matched item into it)."""


def retrieval_plan(
    config: RunnableConfig,
    payload: _DayPayload,
    active_store: Any,
) -> RetrievalPlan:
    """Read the runnable config + payload state into a concrete retrieval policy for this turn."""
    role = payload["player_role"]

    if payload["current_day"] == 1:
        skip_reason = "day_1"
    elif active_store is None:
        skip_reason = "no_store"
    elif not _memory_enabled_for_role(config, role):
        skip_reason = "memory_disabled_for_role"
    else:
        skip_reason = None

    observation_reranking = _reranking_enabled_for_memory_kind(config, role, "observations")
    strategy_point_reranking = _reranking_enabled_for_memory_kind(config, role, "strategy_points")
    reranking = observation_reranking or strategy_point_reranking
    filtering = _filtering_enabled_for_role(config, role)
    dimension_gating = _dimension_gating_enabled_for_role(config, role)

    return RetrievalPlan(
        skip_reason=skip_reason,
        store_dir=_store_dir_from_config(config),
        retrieve_observations=_retrieval_type_enabled(config, "observations"),
        retrieve_strategy=_retrieval_type_enabled(config, "strategy_points"),
        observation_reranking=observation_reranking,
        strategy_point_reranking=strategy_point_reranking,
        filtering=filtering,
        dimension_gating=dimension_gating,
        reranking=reranking,
        needs_wide_retrieval=reranking or filtering or dimension_gating,
    )


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


def _dimension_gating_enabled_for_role(config: RunnableConfig, role: str) -> bool:
    configurable = config.get("configurable", {}) if config else {}
    dimension_gating_config = configurable.get("dimension_gating_config")
    if not isinstance(dimension_gating_config, dict):
        return False
    return bool(dimension_gating_config.get(role, False))


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

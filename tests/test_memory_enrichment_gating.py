"""Unit tests for memory-enrichment gating (Agents/memory/enrichment/gating.py).

This is the Phase C independent variable. The danger these tests guard against is
not a crash but a *silent* mis-gate: the "memory-on" arm secretly running with
memory off (or vice versa), which a smoke game cannot reveal because the happy
path looks identical either way. So we pin every config-routing default and the
skip-precedence of the day-1 / no-store / role-off gate.

Pure functions over a config dict, plus the early-return skip path of
``enrich_payload_with_memory`` (which returns BEFORE any retrieval/langfuse, so
a SimpleNamespace runtime is all the plumbing it needs).
"""
from __future__ import annotations

from types import SimpleNamespace


from Agents.memory.enrichment import (
    enrich_payload_with_memory,
    _filtering_enabled_for_role,
    _memory_enabled_for_role,
    _reranking_enabled_for_memory_kind,
    _retrieval_type_enabled,
    _store_dir_from_config,
)
from Agents.memory.enrichment.gating import retrieval_plan


def cfg(**configurable) -> dict:
    return {"configurable": configurable}


# --- _memory_enabled_for_role: DEFAULT ON, per-role OFF when absent ----------

def test_memory_enabled_defaults_on_when_unconfigured():
    # No memory_config at all -> ON. (A dropped config must not silently disable.)
    assert _memory_enabled_for_role(cfg(), "villager") is True
    assert _memory_enabled_for_role({}, "villager") is True


def test_memory_enabled_per_role_routing():
    config = cfg(memory_config={"villager": True, "healer": False})
    assert _memory_enabled_for_role(config, "villager") is True
    assert _memory_enabled_for_role(config, "healer") is False


def test_memory_enabled_missing_role_is_off_once_config_present():
    # Once a memory_config dict exists, a role absent from it is OFF, not ON.
    config = cfg(memory_config={"villager": True})
    assert _memory_enabled_for_role(config, "wolf") is False


# --- _retrieval_type_enabled: DEFAULT ON ------------------------------------

def test_retrieval_type_defaults_on():
    assert _retrieval_type_enabled(cfg(), "observations") is True
    assert _retrieval_type_enabled(cfg(), "strategy_points") is True


def test_retrieval_type_explicit_off():
    config = cfg(retrieval_types_config={"observations": False})
    assert _retrieval_type_enabled(config, "observations") is False
    # A kind absent from a present config still defaults ON.
    assert _retrieval_type_enabled(config, "strategy_points") is True


# --- _reranking_enabled_for_memory_kind: DEFAULT OFF, nested per-role --------

def test_reranking_defaults_off():
    assert _reranking_enabled_for_memory_kind(cfg(), "villager", "observations") is False


def test_reranking_nested_routing():
    config = cfg(reranking_config={"observations": {"villager": True, "healer": False}})
    assert _reranking_enabled_for_memory_kind(config, "villager", "observations") is True
    assert _reranking_enabled_for_memory_kind(config, "healer", "observations") is False
    # memory_kind not configured -> off.
    assert _reranking_enabled_for_memory_kind(config, "villager", "strategy_points") is False


# --- _filtering_enabled_for_role: DEFAULT OFF -------------------------------

def test_filtering_defaults_off():
    assert _filtering_enabled_for_role(cfg(), "villager") is False


def test_filtering_per_role_routing():
    config = cfg(filtering_config={"villager": True})
    assert _filtering_enabled_for_role(config, "villager") is True
    assert _filtering_enabled_for_role(config, "healer") is False


# --- _store_dir_from_config -------------------------------------------------

def test_store_dir_empty_when_unconfigured():
    assert _store_dir_from_config(cfg()) == ""


def test_store_dir_from_dict_config():
    config = cfg(memory_persistence_config={"seed_store_dir": "/seeds/v5"})
    assert _store_dir_from_config(config) == "/seeds/v5"


def test_store_dir_from_object_config():
    mpc = SimpleNamespace(seed_store_dir="/seeds/v5")
    assert _store_dir_from_config(cfg(memory_persistence_config=mpc)) == "/seeds/v5"


def test_store_dir_empty_when_seed_missing():
    config = cfg(memory_persistence_config={"other": "x"})
    assert _store_dir_from_config(config) == ""


# --- enrich_payload_with_memory: the skip gate -----------------------------

def payload(day: int, role: str = "villager") -> dict:
    return {
        "current_day": day,
        "player_role": role,
        "player_id": "p1",
        "current_round": 1,
        "strategy_points": ["sp_seeded"],
    }


def runtime(store):
    return SimpleNamespace(store=store)


def enrich(day, role="villager", store=object(), config=None):
    return enrich_payload_with_memory(
        payload(day, role),
        config if config is not None else cfg(),
        runtime(store),
        action_phase="day_discussion",
    )


def test_day_1_skips_with_memory_off_and_empty_observations():
    enriched, meta = enrich(day=1)
    assert meta["memory_enabled"] is False
    assert meta["retrieval_skipped_reason"] == "day_1"
    assert enriched["retrieved_observations"] == []


def test_skip_preserves_seeded_strategy_points():
    enriched, _ = enrich(day=1)
    assert enriched["strategy_points"] == ["sp_seeded"]


def test_no_store_skips_after_day_1():
    _, meta = enrich(day=2, store=None)
    assert meta["retrieval_skipped_reason"] == "no_store"


def test_role_disabled_skips():
    config = cfg(memory_config={"villager": False})
    _, meta = enrich(day=2, role="villager", config=config)
    assert meta["retrieval_skipped_reason"] == "memory_disabled_for_role"


# --- skip precedence: day_1 > no_store > role-off ----------------------------

def test_day_1_beats_no_store_and_role_off():
    config = cfg(memory_config={"villager": False})
    _, meta = enrich(day=1, store=None, config=config)
    assert meta["retrieval_skipped_reason"] == "day_1"


def test_no_store_beats_role_off():
    config = cfg(memory_config={"villager": False})
    _, meta = enrich(day=2, store=None, config=config)
    assert meta["retrieval_skipped_reason"] == "no_store"


# --- retrieval_plan: the policy object the pipeline executes ------------------

def plan(day=2, role="villager", store=object(), config=None):
    return retrieval_plan(config if config is not None else cfg(), payload(day, role), store)


def test_plan_defaults_proceed_retrieve_all_no_rerank_no_filter():
    p = plan()
    assert p.skip_reason is None
    assert p.retrieve_observations is True and p.retrieve_strategy is True
    assert p.observation_reranking is False and p.strategy_point_reranking is False
    assert p.reranking is False and p.filtering is False
    assert p.needs_wide_retrieval is False
    assert p.store_dir == ""


def test_plan_skip_reasons_match_gate():
    assert plan(day=1).skip_reason == "day_1"
    assert plan(day=2, store=None).skip_reason == "no_store"
    assert plan(
        day=2, config=cfg(memory_config={"villager": False})
    ).skip_reason == "memory_disabled_for_role"


def test_plan_reranking_sets_wide_retrieval():
    p = plan(config=cfg(reranking_config={"observations": {"villager": True}}))
    assert p.observation_reranking is True
    assert p.reranking is True
    assert p.needs_wide_retrieval is True


def test_plan_filtering_sets_wide_retrieval():
    p = plan(config=cfg(filtering_config={"villager": True}))
    assert p.filtering is True
    assert p.reranking is False
    assert p.needs_wide_retrieval is True


def test_plan_retrieval_type_off_propagates():
    p = plan(config=cfg(retrieval_types_config={"observations": False}))
    assert p.retrieve_observations is False
    assert p.retrieve_strategy is True


def test_plan_store_dir_propagates():
    p = plan(config=cfg(memory_persistence_config={"seed_store_dir": "/seeds/v5"}))
    assert p.store_dir == "/seeds/v5"

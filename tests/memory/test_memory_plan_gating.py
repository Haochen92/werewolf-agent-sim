"""Unit tests for retrieval-plan gating (Agents/memory/retrieval/plan_gating.py).

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


from Agents.memory.retrieval import (
    cap_per_situation,
    enrich_payload_with_memory,
    partition_proven_first,
    _filtering_enabled_for_role,
    _memory_enabled_for_role,
    _reranking_enabled_for_memory_kind,
    _retrieval_type_enabled,
    _sp_exploration_slot_enabled,
    _sp_proven_tiering_enabled,
    _store_dir_from_config,
)
from Agents.memory.retrieval.pipeline import _sp_is_proven
from Agents.memory.retrieval.plan_gating import retrieval_plan


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


# --- §0.4 proven-first SP tiering: gate + stable partition + tier boundary ----

def _sp(key, follow, pos, neg):
    """A retrieved-SP stand-in exposing exactly the counters _sp_is_proven reads."""
    return SimpleNamespace(
        key=key,
        strategy_point=SimpleNamespace(
            follow_count=follow, positive_count=pos, negative_count=neg
        ),
    )


def test_sp_tiering_defaults_on_when_unconfigured():
    # A dropped config must not silently disable it (inert on uncredited stores, so ON is safe).
    assert _sp_proven_tiering_enabled(cfg()) is True
    assert _sp_proven_tiering_enabled({}) is True


def test_sp_tiering_explicit_off():
    assert _sp_proven_tiering_enabled(cfg(sp_proven_tiering=False)) is False
    assert _sp_proven_tiering_enabled(cfg(sp_proven_tiering=True)) is True


def test_plan_sp_tiering_default_on_and_no_wide_retrieval():
    p = plan()
    assert p.sp_proven_tiering is True
    # tiering reorders the final capped list -> it must NOT force a wide retrieval on its own.
    assert p.needs_wide_retrieval is False


def test_plan_sp_tiering_off_propagates():
    p = plan(config=cfg(sp_proven_tiering=False))
    assert p.sp_proven_tiering is False


def test_sp_is_proven_boundary():
    assert _sp_is_proven(_sp("ok", follow=5, pos=3, neg=1)) is True     # follow>=5 and pos>neg
    assert _sp_is_proven(_sp("few", follow=4, pos=9, neg=0)) is False   # follow=4 < floor -> unproven
    assert _sp_is_proven(_sp("tie", follow=9, pos=2, neg=2)) is False   # pos==neg -> unproven
    assert _sp_is_proven(_sp("neg", follow=9, pos=1, neg=5)) is False   # pos<neg -> unproven


def test_partition_proven_first_is_stable():
    # Interleaved list; proven = {a, c}. Proven come first in their ORIGINAL relative order (a before c),
    # unproven keep theirs (b before d) -> the partition never re-sorts within a tier.
    items = [
        _sp("a", follow=8, pos=6, neg=1),   # proven
        _sp("b", follow=0, pos=0, neg=0),   # unproven (never followed)
        _sp("c", follow=6, pos=4, neg=2),   # proven
        _sp("d", follow=4, pos=4, neg=0),   # unproven (below follow floor)
    ]
    out = [it.key for it in partition_proven_first(items, _sp_is_proven)]
    assert out == ["a", "c", "b", "d"]


def test_partition_flag_off_leaves_order_unchanged():
    # Mirrors the pipeline gate: `partition... if plan.sp_proven_tiering else <untouched>`.
    items = [
        _sp("b", follow=0, pos=0, neg=0),
        _sp("a", follow=8, pos=6, neg=1),
    ]
    enabled = _sp_proven_tiering_enabled(cfg(sp_proven_tiering=False))
    tiered = partition_proven_first(items, _sp_is_proven) if enabled else items
    assert [it.key for it in tiered] == ["b", "a"]   # unproven-first order preserved (no tiering)


# --- §0.4 tiering PROVENANCE: the flag reaches the run record + per-turn trace ----
# A behavior-changing retrieval toggle that never reaches the recorded config would make tiering-on vs
# tiering-off runs indistinguishable in the artifacts — the whole point of the embedded-config stamp.

def test_recorded_game_config_carries_sp_tiering_default():
    from Agents.config import DEFAULT_SP_PROVEN_TIERING, RunConfig, build_runnable_config

    recorded = build_runnable_config(RunConfig())["configurable"]
    assert recorded["sp_proven_tiering"] is DEFAULT_SP_PROVEN_TIERING is True
    # False is a valid, recordable off-arm (a bool field keeps it from snapping to the True default).
    conf = build_runnable_config(RunConfig(sp_proven_tiering=False))["configurable"]
    assert conf["sp_proven_tiering"] is False


def test_retrieval_metadata_carries_resolved_sp_tiering():
    # Active path with zero situations: no store search, no LLM; langfuse span stubbed out.
    import Agents.tracing as tracing_mod
    from unittest.mock import MagicMock, patch

    def meta_for(config):
        with patch.object(tracing_mod, "langfuse", MagicMock()), \
                patch("Agents.memory.retrieval.pipeline._generate_situations_for_agent",
                      return_value=([], [])):
            _, meta = enrich(day=2, config=config)
        return meta

    assert meta_for(cfg())["sp_proven_tiering_enabled"] is True                       # default ON
    assert meta_for(cfg(sp_proven_tiering=False))["sp_proven_tiering_enabled"] is False  # resolved OFF
    # Skipped turns mirror the active-path keys (nothing fired).
    _, skipped = enrich(day=1)
    assert skipped["sp_proven_tiering_enabled"] is False


# --- §0.4 exploration slot at the SP cap: gate + the swap/fill/never-exceed behavior ----

def _csp(key, situation, score, follow, pos, neg):
    """A retrieved-SP stand-in with the situation + score cap_per_situation groups/ranks on, plus the
    counters _sp_is_proven reads."""
    return SimpleNamespace(
        key=key,
        matched_situation=situation,
        score=score,
        strategy_point=SimpleNamespace(follow_count=follow, positive_count=pos, negative_count=neg),
    )


def _cap(items, is_proven=_sp_is_proven, keep=3):
    return cap_per_situation(
        items, get_situation=lambda it: it.matched_situation,
        get_score=lambda it: it.score or 0.0, keep=keep, is_proven=is_proven,
    )


def test_exploration_slot_swaps_lowest_proven_for_best_unproven():
    # All three kept (top-3 by score) are proven; pool holds an unproven below them -> the lowest-scoring
    # proven slot (0.7) is dropped for the best unproven (0.6).
    items = [
        _csp("p_hi", "s", 0.9, follow=8, pos=6, neg=0),
        _csp("p_mid", "s", 0.8, follow=8, pos=6, neg=0),
        _csp("p_lo", "s", 0.7, follow=8, pos=6, neg=0),
        _csp("u", "s", 0.6, follow=0, pos=0, neg=0),
    ]
    keys = [it.key for it in _cap(items)]
    assert keys == ["p_hi", "p_mid", "u"]   # p_lo evicted, unproven surfaced, re-sorted by score desc


def test_exploration_slot_noop_when_unproven_already_kept():
    # An unproven is already in the top-3 -> no swap; the lower unproven is NOT pulled in.
    items = [
        _csp("p_hi", "s", 0.9, follow=8, pos=6, neg=0),
        _csp("u_hi", "s", 0.7, follow=0, pos=0, neg=0),
        _csp("p_lo", "s", 0.5, follow=8, pos=6, neg=0),
        _csp("u_lo", "s", 0.3, follow=0, pos=0, neg=0),
    ]
    keys = [it.key for it in _cap(items)]
    assert keys == ["p_hi", "u_hi", "p_lo"]


def test_exploration_slot_off_restores_plain_cap():
    # is_proven=None (flag False path) -> today's behavior: top-3 by score, no exploration.
    items = [
        _csp("p_hi", "s", 0.9, follow=8, pos=6, neg=0),
        _csp("p_mid", "s", 0.8, follow=8, pos=6, neg=0),
        _csp("p_lo", "s", 0.7, follow=8, pos=6, neg=0),
        _csp("u", "s", 0.6, follow=0, pos=0, neg=0),
    ]
    keys = [it.key for it in _cap(items, is_proven=None)]
    assert keys == ["p_hi", "p_mid", "p_lo"]   # unproven never surfaces


def test_exploration_slot_never_exceeds_keep():
    # 5 proven + 1 unproven for one situation -> still exactly keep(=3), one of them the unproven.
    items = [_csp(f"p{i}", "s", 0.9 - i * 0.1, follow=8, pos=6, neg=0) for i in range(5)]
    items.append(_csp("u", "s", 0.1, follow=0, pos=0, neg=0))
    out = _cap(items)
    assert len(out) == 3
    assert "u" in [it.key for it in out]


def test_exploration_slot_defaults_on_when_unconfigured():
    assert _sp_exploration_slot_enabled(cfg()) is True
    assert _sp_exploration_slot_enabled({}) is True


def test_exploration_slot_explicit_off():
    assert _sp_exploration_slot_enabled(cfg(sp_exploration_slot=False)) is False
    assert _sp_exploration_slot_enabled(cfg(sp_exploration_slot=True)) is True


def test_plan_carries_exploration_slot():
    assert plan().sp_exploration_slot is True
    assert plan(config=cfg(sp_exploration_slot=False)).sp_exploration_slot is False


def test_recorded_game_config_carries_exploration_slot_default():
    from Agents.config import DEFAULT_SP_EXPLORATION_SLOT, RunConfig, build_runnable_config

    recorded = build_runnable_config(RunConfig())["configurable"]
    assert recorded["sp_exploration_slot"] is DEFAULT_SP_EXPLORATION_SLOT is True
    conf = build_runnable_config(RunConfig(sp_exploration_slot=False))["configurable"]
    assert conf["sp_exploration_slot"] is False

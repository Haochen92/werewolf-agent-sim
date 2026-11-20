"""Guard the structured dedup gate: v5-safe no-op, v6 partition, verdict rule, candidate filter."""

from types import SimpleNamespace

from Agents.memory.dedup_gate import (
    _alive_bucket,
    batch_partition_key,
    compatible,
    gate_filter,
    gate_filter_for,
    gate_key,
    partition_key_for,
    same_verdict,
    sp_gate_filter,
    sp_gate_key,
)


def _v6(is_swing, alive, consensus, verdict="positive"):
    return {
        "is_swing": is_swing, "players_alive": alive,
        "consensus_direction": consensus, "net_verdict": verdict,
    }


def test_alive_buckets():
    assert _alive_bucket(9) == "early" and _alive_bucket(8) == "early"
    assert _alive_bucket(7) == "mid" and _alive_bucket(5) == "mid"
    assert _alive_bucket(4) == "late" and _alive_bucket(2) == "late"
    assert _alive_bucket(None) == "unknown"


def test_gate_key_none_for_v5_entry():
    assert gate_key({"situation": "x", "approach": "y", "outcome": "z"}) is None


def test_gate_key_v6_partition():
    assert gate_key(_v6(True, 6, "opposes_my_read")) == (True, "mid", "opposes_my_read")


def test_same_verdict_rule():
    assert same_verdict(_v6(False, 6, "x", "positive"), _v6(False, 6, "x", "positive"))
    assert not same_verdict(_v6(False, 6, "x", "positive"), _v6(False, 6, "x", "negative"))
    assert same_verdict({"net_verdict": None}, _v6(False, 6, "x"))  # missing -> no constraint


def test_compatible_pairchecks():
    base = {"net_verdict": "positive", "info_landscape_class": "info_starved", "exposure_class": "safe"}
    assert compatible(base, dict(base))
    assert not compatible(base, {**base, "net_verdict": "negative"})
    assert not compatible(base, {**base, "info_landscape_class": "info_rich"})
    assert not compatible(base, {**base, "exposure_class": "exposed"})
    assert compatible(base, {"net_verdict": None})  # missing -> no constraint


def test_gate_filter_applies_pairchecks():
    item = SimpleNamespace(
        is_swing=False, players_alive=6, consensus_direction="opposes_my_read",
        net_verdict="positive", info_landscape_class="info_starved", exposure_class="safe",
    )
    ok = SimpleNamespace(value=_v6(False, 7, "opposes_my_read", "positive") | {
        "info_landscape_class": "info_starved", "exposure_class": "safe"})
    diff_landscape = SimpleNamespace(value=_v6(False, 6, "opposes_my_read", "positive") | {
        "info_landscape_class": "info_rich", "exposure_class": "safe"})
    diff_exposure = SimpleNamespace(value=_v6(False, 6, "opposes_my_read", "positive") | {
        "info_landscape_class": "info_starved", "exposure_class": "exposed"})
    assert gate_filter(item, [ok, diff_landscape, diff_exposure]) == [ok]


def test_batch_partition_key_is_gate_plus_pairchecks():
    v = _v6(False, 6, "opposes_my_read", "positive") | {
        "info_landscape_class": "info_starved", "exposure_class": "safe"}
    assert batch_partition_key(v) == (False, "mid", "opposes_my_read", "positive", "info_starved", "safe")
    assert batch_partition_key({"situation": "x"}) is None  # v5 -> no gating


def test_gate_partitions_separate_by_full_key():
    from Agents.memory.batch_deduplication.clustering import _gate_partitions

    def it(verdict):
        return SimpleNamespace(value=_v6(False, 6, "x", verdict) | {
            "info_landscape_class": "info_rich", "exposure_class": "safe"})
    parts = _gate_partitions(
        {"a": it("positive"), "b": it("positive"), "c": it("negative")}, "observations",
    )
    assert sorted(len(p) for p in parts) == [1, 2]  # a,b (positive) together; c (negative) apart


def test_gate_filter_is_noop_for_v5_item():
    item = SimpleNamespace(situation="x")  # no v6 fields -> gate_key None
    cands = [SimpleNamespace(value=_v6(True, 9, "a"))]
    assert gate_filter(item, cands) == cands


def test_gate_filter_keeps_only_same_bucket_same_verdict():
    item = SimpleNamespace(
        is_swing=False, players_alive=6, consensus_direction="opposes_my_read",
        net_verdict="positive",
    )
    same = SimpleNamespace(value=_v6(False, 7, "opposes_my_read", "positive"))  # same mid bucket
    diff_bucket = SimpleNamespace(value=_v6(False, 9, "opposes_my_read", "positive"))
    diff_consensus = SimpleNamespace(value=_v6(False, 6, "aligns_with_my_read", "positive"))
    diff_verdict = SimpleNamespace(value=_v6(False, 6, "opposes_my_read", "negative"))
    out = gate_filter(item, [same, diff_bucket, diff_consensus, diff_verdict])
    assert out == [same]


# ── strategy-point gate: signature = direction + honesty (situation goes soft) ──


def _sp(direction, honesty):
    return {"direction": direction, "honesty": honesty}


def test_sp_gate_key_none_for_v5_strategy_point():
    assert sp_gate_key({"situation": "x", "action": "y"}) is None


def test_sp_gate_key_signature():
    assert sp_gate_key(_sp("offensive", "honest")) == ("offensive", "honest", None, None, None)


def test_sp_gate_filter_keeps_only_same_signature():
    # SP does NOT gate on the situation enums — only the move classification. Rival moves in the
    # same spot (different direction/honesty) must NOT be candidates.
    item = SimpleNamespace(direction="offensive", honesty="honest")
    same = SimpleNamespace(value=_sp("offensive", "honest"))
    diff_direction = SimpleNamespace(value=_sp("defensive", "honest"))
    diff_honesty = SimpleNamespace(value=_sp("offensive", "deceptive"))
    assert sp_gate_filter(item, [same, diff_direction, diff_honesty]) == [same]


def test_kind_dispatch_routes_sp_vs_obs():
    sp_val = _sp("positional", "deceptive")
    obs_val = _v6(False, 6, "opposes_my_read", "positive") | {
        "info_landscape_class": "info_starved", "exposure_class": "safe"}
    # partition_key_for picks the SP signature for strategy_points, the obs gate+pairchecks otherwise
    assert partition_key_for("strategy_points", sp_val) == ("positional", "deceptive", None, None, None)
    assert partition_key_for("observations", obs_val) == batch_partition_key(obs_val)
    # gate_filter_for routes the per-game candidate filter the same way
    sp_item = SimpleNamespace(direction="positional", honesty="deceptive")
    sp_other = SimpleNamespace(value=_sp("positional", "honest"))
    assert gate_filter_for("strategy_points", sp_item, [sp_other]) == []


# ── strategy-point gate: stage is in the partition, before the judge ──


def _staged(direction="offensive", honesty="honest", **dims):
    return {"direction": direction, "honesty": honesty, "dimensions": dims}


def test_sp_key_carries_the_stage_filter_facts():
    sp = _staged(players_alive=9, ally_revealed=True, uses_left=2)
    assert sp_gate_key(sp) == ("offensive", "honest", "early", True, True)
    assert sp_gate_key(_staged(players_alive=4, bullets_left=0))[2:] == ("late", None, False)


def test_a_missing_stage_fact_is_none_in_its_slot():
    assert sp_gate_key(_staged(players_alive=6)) == ("offensive", "honest", "mid", None, None)
    assert sp_gate_key(_staged(ally_revealed=False)) == ("offensive", "honest", None, False, None)


def test_a_fresh_point_reads_stage_from_its_own_fields():
    fresh = SimpleNamespace(direction="offensive", honesty="honest", players_alive=9, uses_left=0)
    assert sp_gate_key(fresh) == ("offensive", "honest", "early", None, False)


def test_same_labels_other_stage_never_share_a_partition():
    from Agents.memory.batch_deduplication.clustering import _gate_partitions

    base = dict(players_alive=9, ally_revealed=False, uses_left=1)
    items = {
        "a": SimpleNamespace(value=_staged(**base)),
        "same_stage": SimpleNamespace(value=_staged(**base | {"players_alive": 8, "uses_left": 2})),
        "other_alive": SimpleNamespace(value=_staged(**base | {"players_alive": 6})),
        "partner_lost": SimpleNamespace(value=_staged(**base | {"ally_revealed": True})),
        "spent": SimpleNamespace(value=_staged(**base | {"uses_left": 0})),
    }
    parts = sorted(sorted(p) for p in _gate_partitions(items, "strategy_points"))
    assert parts == [["a", "same_stage"], ["other_alive"], ["partner_lost"], ["spent"]]


def test_sp_gate_filter_drops_other_stage_candidates():
    item = SimpleNamespace(direction="offensive", honesty="honest", players_alive=9)
    same = SimpleNamespace(value=_staged(players_alive=8))
    late = SimpleNamespace(value=_staged(players_alive=4))
    assert sp_gate_filter(item, [same, late]) == [same]


def test_the_partition_is_never_looser_than_the_after_judge_check():
    # Lessons sharing a partition never differ on a stage fact the check compares; a lesson missing a
    # fact sits apart from one that has it, so the check (which skips missing facts) cannot fire inside.
    from Agents.memory.retrieval.dimension_gating import stage_mismatch

    boards = [dict(players_alive=a, **extra) for a in (9, 6, 3)
              for extra in ({}, {"ally_revealed": True}, {"ally_revealed": False, "uses_left": 0},
                            {"uses_left": 2}, {"bullets_left": 1})]
    for x in boards:
        for y in boards:
            if sp_gate_key(_staged(**x)) == sp_gate_key(_staged(**y)):
                assert stage_mismatch(x, y) == []
    assert sp_gate_key(_staged(players_alive=9)) != sp_gate_key(_staged(players_alive=9, uses_left=1))

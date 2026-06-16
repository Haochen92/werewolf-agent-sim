"""Guard the structured dedup gate: v5-safe no-op, v6 partition, verdict rule, candidate filter."""

from types import SimpleNamespace

from Agents.memory.dedup_gate import _alive_bucket, gate_filter, gate_key, same_verdict


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

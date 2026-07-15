"""Credit-layer guard tests: discussion/night credit is a LIFT not a level, fossil credit ages out,
adoption counters are windowed (evict lives), every credited channel has a same-grading-function OFF
base (the standing baseline-coherence invariant) — plus the v1 wiring (2026-07-13): healer night credit
(the attack-join), the read-partition, the endpoint self-lynch guard, the move-grain refinement, and the
concealment floor with both guards.

$0 / fully deterministic: the de-luck grading (`_vote_credit`, `_night_credit`, the endpoint verdict,
the heat census) runs for real on hand-checkable fixtures, so exact lifts are asserted, not just signs.
The omniscient-tagger credit mode was retired 2026-07-13 (owner ruling) — its tests went with it; the
invariant still accepts legacy 'tagger' gradings so old run records verify (covered in (f))."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.src.loop.config import LoopConfig
from evaluation.src.loop.consolidate import prune_and_evict
from evaluation.src.loop.credit import base_for, credit_apply, sp_lift
from evaluation.src.loop.invariants import assert_baseline_coherence


# --- fixtures --------------------------------------------------------------------------------------
def _ec(case: dict) -> dict:
    return {"kind": "agent_action_eval", "output": {"eval_case": case}}


def _game(tmp: Path, name: str, cases: list, *, roles: dict, day_res=None, night_res=None,
          day_channel=None, extra=None) -> str:
    """A (game record, eval-cases) pair on disk; returns the game-record path (a single-line jsonl)."""
    ecp = tmp / f"{name}_cases.jsonl"
    ecp.write_text("\n".join(json.dumps(_ec(c)) for c in cases))
    rec = {"roles": roles, "eval_cases_path": str(ecp), "game_id": f"gid_{name}"}
    if day_res is not None:
        rec["day_resolutions"] = day_res
    if night_res is not None:
        rec["night_resolutions"] = night_res
    if day_channel is not None:
        rec["day_channel"] = day_channel
    if extra:
        rec.update(extra)
    gp = tmp / f"{name}.jsonl"
    gp.write_text(json.dumps(rec))
    return str(gp)


def _store(tmp: Path, namespaces: dict) -> Path:
    sp = tmp / "strategy_points.json"
    sp.write_text(json.dumps({"namespaces": namespaces}))
    return sp


def _by_key(sp: Path, key: str) -> dict:
    for recs in json.loads(Path(sp).read_text())["namespaces"].values():
        for r in recs:
            if r["key"] == key:
                return r["value"]
    raise KeyError(key)


def _disc_case(role, pid, day, key, verdict="follow", mem=True, accuses=None, spoke=True):
    c = {"action_phase": "day_discussion", "player_role": role, "player_id": pid, "day": day,
         "memory_enabled": mem}
    if spoke:  # the discussion ledger credits SPOKEN turns only (the pass-gate)
        c["agent_message"] = {"day": day, "seq": 0, "player": pid, "message": "…", "passed": False,
                              "addressed_targets": [{"target": t, "addressed_form": "mention",
                                                     "stance": "accusation"} for t in (accuses or [])]}
    if mem:
        c["strategy_index_to_key"] = {"0": key}
        c["strategy_verdicts"] = [{"verdict": verdict, "strategy_index": 0}]
    return c


def _vote_case(role, pid, votee, key, verdict="follow"):
    return {"action_phase": "day_vote", "player_role": role, "player_id": pid, "day": 1,
            "memory_enabled": True, "agent_vote": {"votee": votee},
            "strategy_index_to_key": {"0": key},
            "strategy_verdicts": [{"verdict": verdict, "strategy_index": 0}]}


def _night_case(role, pid, target, key, reads=None, mem=True):
    c = {"action_phase": "night_action", "player_role": role, "player_id": pid, "day": 1,
         "memory_enabled": mem, "agent_night_action": {"target": target, "role": role}}
    if reads is not None:
        c["reads"] = reads
    if mem:
        c["strategy_index_to_key"] = {"0": key}
        c["strategy_verdicts"] = [{"verdict": "follow", "strategy_index": 0}]
    return c


def _speech(day, player, targets=()):
    return {"day": day, "seq": 0, "player": player, "message": "…", "passed": False,
            "addressed_targets": [{"target": t, "addressed_form": "mention", "stance": "accusation"}
                                  for t in targets]}


# --- (a) discussion credit is level - base, exactly ------------------------------------------------
def test_a_discussion_credit_is_level_minus_off_base(tmp_path):
    roles = {"p1": "villager", "w1": "wolf"}
    on = _game(tmp_path, "on", [_disc_case("villager", "p1", d, "sp1") for d in (1, 2, 3, 4)],
               roles=roles, day_res=[{"day": d, "voted_player": "w1"} for d in (1, 2, 3, 4)])
    off = _game(tmp_path, "off", [_disc_case("villager", "p1", d, "sp1", mem=False) for d in (1, 2, 3, 4)],
                roles=roles, day_res=[{"day": 1, "voted_player": "w1"}, {"day": 2, "voted_player": "w1"},
                                      {"day": 3, "voted_player": "w1"}, {"day": 4, "voted_player": "p1"}])
    sp = _store(tmp_path, {"strategy_points/villager/day_discussion": [{"key": "sp1", "value": {}}]})
    credit_apply(sp, on, base_rates={}, discussion=True, off_window=off)

    v = _by_key(sp, "sp1")
    assert (v["follow_count"], v["positive_count"], v["negative_count"]) == (4, 4, 0)
    br = json.loads((sp.parent / "base_rates.json").read_text())
    assert br["villager/day_discussion"] == [0.5, 4]          # OFF base, NOT 0 (the level-not-lift bug)
    base = base_for(br, "villager/day_discussion")
    assert base == 0.5
    assert sp_lift(v, base) == pytest.approx((1.0 - 0.5) * 4 / (4 + 5))   # lift = utility - base, shrunk


# --- (b) healer night credit rides the attack-join (v1, 2026-07-13) --------------------------------
def test_b_healer_credit_via_attack_join(tmp_path):
    roles = {"h1": "healer", "w1": "wolf", "v1": "villager"}
    nres = [{"day": 1, "wolves_target": "v1", "serial_killer_target": None,
             "vigilante_target": None, "deaths": []}]
    win = _game(tmp_path, "hsave", [_night_case("healer", "h1", "v1", "sp_h")],
                roles=roles, night_res=nres)
    sp = _store(tmp_path, {"strategy_points/healer/night_action": [{"key": "sp_h", "value": {}}]})
    credit_apply(sp, win, base_rates={}, discussion=False)
    v = _by_key(sp, "sp_h")
    assert (v["follow_count"], v["positive_count"]) == (1, 1)   # town save = the ★ construct's good half

    # shielding a threat from the vigilante's correct shot = the validated error half (negative)
    nres2 = [{"day": 1, "wolves_target": None, "serial_killer_target": None,
              "vigilante_target": "w1", "deaths": []}]
    win2 = _game(tmp_path, "hshield", [_night_case("healer", "h1", "w1", "sp_h")],
                 roles=roles, night_res=nres2)
    credit_apply(sp, win2, base_rates={}, discussion=False)
    v = _by_key(sp, "sp_h")
    assert (v["follow_count"], v["negative_count"]) == (1, 1)

    # unattacked heal = a prediction miss, neutral like the held bullet
    nres3 = [{"day": 1, "wolves_target": "w1", "serial_killer_target": None,
              "vigilante_target": None, "deaths": ["w1"]}]
    win3 = _game(tmp_path, "hmiss", [_night_case("healer", "h1", "v1", "sp_h")],
                 roles=roles, night_res=nres3)
    credit_apply(sp, win3, base_rates={}, discussion=False)
    v = _by_key(sp, "sp_h")
    assert (v["follow_count"], v["neutral_count"]) == (1, 1)


# --- (c) floor base comes from the OFF arm, never the ON-window incidental mem-off cases ------------
def test_c_floor_base_from_off_arm_not_on_incidentals(tmp_path):
    roles = {"p1": "villager", "w1": "wolf"}
    on = _game(tmp_path, "on", [_disc_case("villager", "p1", 1, "sp1"),
                                _disc_case("villager", "p1", 2, "sp1", mem=False)],
               roles=roles, day_res=[{"day": 1, "voted_player": "w1"}, {"day": 2, "voted_player": "p1"}])
    off = _game(tmp_path, "off", [_disc_case("villager", "p1", 1, "sp1", mem=False)],
                roles=roles, day_res=[{"day": 1, "voted_player": "w1"}])   # OFF lynches the wolf -> +1.0
    sp = _store(tmp_path, {"strategy_points/villager/day_discussion": [{"key": "sp1", "value": {}}]})
    credit_apply(sp, on, base_rates={}, discussion=True, off_window=off)

    br = json.loads((sp.parent / "base_rates.json").read_text())
    assert br["villager/day_discussion"] == [1.0, 1]          # from the OFF arm, not the ON incidental -1


# --- (d) fossil credit is zeroed for SPs absent from the current window -----------------------------
def test_d_out_of_window_sp_credit_zeroed(tmp_path):
    roles = {"p1": "villager", "w1": "wolf"}
    w1 = _game(tmp_path, "w1", [_vote_case("villager", "p1", "w1", "sp_fossil")], roles=roles,
               day_res=[{"day": 1, "voted_player": "w1", "vote_counts": {"w1": 3}}])
    w2 = _game(tmp_path, "w2", [_vote_case("villager", "p1", "w1", "sp_new")], roles=roles,
               day_res=[{"day": 1, "voted_player": "w1", "vote_counts": {"w1": 3}}])
    sp = _store(tmp_path, {"strategy_points/villager/day_vote": [
        {"key": "sp_fossil", "value": {}}, {"key": "sp_new", "value": {}}]})

    credit_apply(sp, w1, base_rates={}, discussion=False)
    f1 = _by_key(sp, "sp_fossil")
    assert (f1["follow_count"], f1["positive_count"]) == (1, 1)   # credited in window 1

    credit_apply(sp, w2, base_rates={}, discussion=False)         # window 2 does NOT touch sp_fossil
    f2 = _by_key(sp, "sp_fossil")
    assert (f2["follow_count"], f2["positive_count"], f2["negative_count"], f2["neutral_count"]) == (0, 0, 0, 0)
    assert (f2["retrieved_count"], f2["override_count"], f2["not_relevant_count"]) == (0, 0, 0)
    assert _by_key(sp, "sp_new")["follow_count"] == 1            # the in-window SP is still credited


# --- (e) adoption counters are set from eval cases and the evict rule can now fire ------------------
def test_e_evict_counters_set_from_cases_and_evict_fires(tmp_path):
    roles = {"p1": "villager", "w1": "wolf"}
    cases = [_vote_case("villager", "p1", "w1", "sp_evict", verdict="override") for _ in range(9)]
    win = _game(tmp_path, "w", cases, roles=roles, day_res=[{"day": 1, "voted_player": "w1"}])
    sp = _store(tmp_path, {"strategy_points/villager/day_vote": [{"key": "sp_evict", "value": {}}]})

    credit_apply(sp, win, base_rates={}, discussion=False)
    v = _by_key(sp, "sp_evict")
    assert (v["retrieved_count"], v["override_count"], v["not_relevant_count"], v["follow_count"]) == (9, 9, 0, 0)

    ns = json.loads(sp.read_text())["namespaces"]
    stats = prune_and_evict(ns, {"villager/day_vote": [0.0, 50]}, LoopConfig())
    assert stats["evicted"] == 1                                # evict is LIVE for the first time
    assert ns["strategy_points/villager/day_vote"] == []


# --- (f) the standing baseline-coherence invariant -------------------------------------------------
def test_f_baseline_coherence_invariant():
    # legacy tagger grading (retired from credit 2026-07-13): old records must still verify
    with pytest.raises(AssertionError, match="baseline INCOHERENT"):
        assert_baseline_coherence({"wolf/night_action": "tagger"}, {"wolf/night_action": [0.0, 5]})
    assert assert_baseline_coherence({"wolf/night_action": "tagger"},
                                     {"tagger/wolf/night_action": [-0.5, 10]}) is None
    # deterministic channel needs its own <cell> base
    with pytest.raises(AssertionError, match="baseline INCOHERENT"):
        assert_baseline_coherence({"villager/day_vote": "deterministic"}, {})
    assert_baseline_coherence({"villager/day_vote": "deterministic"}, {"villager/day_vote": [0.3, 9]})
    # a present-but-degenerate (n=0) base still raises (it would silently halo)
    with pytest.raises(AssertionError, match="missing/degenerate"):
        assert_baseline_coherence({"villager/day_vote": "deterministic"}, {"villager/day_vote": [0.3, 0]})
    # conceal channels are SELF-KEYED (the channel string is its own base key)
    with pytest.raises(AssertionError, match="baseline INCOHERENT"):
        assert_baseline_coherence({"conceal/wolf/day_discussion": "conceal"}, {})
    assert_baseline_coherence({"conceal/wolf/day_discussion": "conceal"},
                              {"conceal/wolf/day_discussion": [0.2, 6]})


# --- (g) the read-partition: a negative through a stated-and-wrong threat-read is excluded ----------
def test_g_read_partition_excludes_misread_friendly_fire(tmp_path):
    roles = {"g1": "vigilante", "v1": "villager", "w1": "wolf"}
    wrong_read = [{"player": "v1", "why": "…", "suspected_role": "wolf", "confidence": "high"}]
    win = _game(tmp_path, "ff", [_night_case("vigilante", "g1", "v1", "sp_v", reads=wrong_read)],
                roles=roles, night_res=[{"day": 1, "deaths": []}])
    sp = _store(tmp_path, {"strategy_points/vigilante/night_action": [{"key": "sp_v", "value": {}}]})
    stats = credit_apply(sp, win, base_rates={}, discussion=False)
    v = _by_key(sp, "sp_v")
    assert v["follow_count"] == 0                                # instance excluded from the SP ledger
    assert stats["read_excluded"] == 1                           # …and surfaced, not silently dropped

    # a LOW-confidence wrong read does NOT fire the partition — friendly fire credits normally
    low_read = [{"player": "v1", "why": "…", "suspected_role": "wolf", "confidence": "low"}]
    win2 = _game(tmp_path, "ff2", [_night_case("vigilante", "g1", "v1", "sp_v", reads=low_read)],
                 roles=roles, night_res=[{"day": 1, "deaths": []}])
    stats2 = credit_apply(sp, win2, base_rates={}, discussion=False)
    v = _by_key(sp, "sp_v")
    assert (v["follow_count"], v["negative_count"]) == (1, 1)
    assert stats2["read_excluded"] == 0


# --- (h) endpoint self-lynch guard: a lynched deceiver's discussion SPs read negative ---------------
def test_h_endpoint_self_lynch_is_negative(tmp_path):
    roles = {"s1": "serial_killer", "v1": "villager"}
    # the SK is lynched on its own day: the raw SK rule ("any non-self lynch = positive") is blind here
    win = _game(tmp_path, "sk", [_disc_case("serial_killer", "s1", 1, "sp_s")],
                roles=roles, day_res=[{"day": 1, "voted_player": "s1"}])
    sp = _store(tmp_path, {"strategy_points/serial_killer/day_discussion": [{"key": "sp_s", "value": {}}]})
    credit_apply(sp, win, base_rates={}, discussion=True)
    v = _by_key(sp, "sp_s")
    assert (v["follow_count"], v["negative_count"]) == (1, 1)


# --- (i) move grain: a landed push is scored on the push, not the day smear -------------------------
def test_i_move_grain_bus_beats_day_smear(tmp_path):
    roles = {"w1": "wolf", "w2": "wolf", "v1": "villager"}
    # w1 accused its packmate w2 and the room lynched w2: the day-grain tick would read NEGATIVE
    # (a packmate fell); the landed push is a BUS — plurality by construction — and scores positive.
    win = _game(tmp_path, "bus", [_disc_case("wolf", "w1", 1, "sp_w", accuses=["w2"])],
                roles=roles, day_res=[{"day": 1, "voted_player": "w2"}])
    sp = _store(tmp_path, {"strategy_points/wolf/day_discussion": [{"key": "sp_w", "value": {}}]})
    credit_apply(sp, win, base_rates={}, discussion=True)
    v = _by_key(sp, "sp_w")
    assert (v["follow_count"], v["positive_count"]) == (1, 1)

    # town side of the same refinement: a landed push onto a REAL threat credits…
    win2 = _game(tmp_path, "tpush", [_disc_case("villager", "v1", 1, "sp_t", accuses=["w1"])],
                 roles=roles, day_res=[{"day": 1, "voted_player": "w1"}])
    sp2 = _store(tmp_path, {"strategy_points/villager/day_discussion": [{"key": "sp_t", "value": {}}]})
    credit_apply(sp2, win2, base_rates={}, discussion=True)
    assert _by_key(sp2, "sp_t")["positive_count"] == 1

    # …and a landed push onto another VILLAGER is the read-partition case: excluded, not negative
    roles3 = {"v1": "villager", "v2": "villager", "w1": "wolf"}
    win3 = _game(tmp_path, "tmiss", [_disc_case("villager", "v1", 1, "sp_t", accuses=["v2"])],
                 roles=roles3, day_res=[{"day": 1, "voted_player": "v2"}])
    sp3 = _store(tmp_path, {"strategy_points/villager/day_discussion": [{"key": "sp_t", "value": {}}]})
    stats = credit_apply(sp3, win3, base_rates={}, discussion=True)
    assert _by_key(sp3, "sp_t")["follow_count"] == 0
    assert stats["read_excluded"] == 1


# --- (j) the concealment floor: typed SPs, both guards, own channel + OFF base ----------------------
def test_j_concealment_floor_guards_and_base(tmp_path):
    roles = {"w1": "wolf", "v1": "villager", "v2": "villager"}
    conceal_sp = {"key": "sp_c", "value": {"sp_type": "concealment"}}
    # day 1: w1 SPOKE and drew 0 of the day's 3 accusations (all on v1) -> ratio 0 -> positive
    channel = [_speech(1, "w1"), _speech(1, "v1", targets=["v1"]), _speech(1, "v2", targets=["v1", "v1"])]
    win = _game(tmp_path, "cz", [_disc_case("wolf", "w1", 1, "sp_c")], roles=roles,
                day_res=[{"day": 1, "voted_player": None}], night_res=[], day_channel=channel)
    sp = _store(tmp_path, {"strategy_points/wolf/day_discussion": [conceal_sp]})
    # OFF arm: a mem-off wolf player-day with the SAME census (spoke, 0 heat) -> conceal base = +1.0
    off = _game(tmp_path, "cz_off", [_disc_case("wolf", "w1", 1, "sp_c", mem=False)], roles=roles,
                day_res=[{"day": 1, "voted_player": None}], night_res=[], day_channel=channel)
    credit_apply(sp, win, base_rates={}, discussion=True, off_window=off)
    v = _by_key(sp, "sp_c")
    assert (v["follow_count"], v["positive_count"]) == (1, 1)    # credited by the floor, not the endpoint
    br = json.loads((sp.parent / "base_rates.json").read_text())
    assert br["conceal/wolf/day_discussion"] == [1.0, 1]         # same-instrument OFF base, self-keyed
    assert base_for(br, "wolf/day_discussion", "concealment") == 1.0   # sp_type routes to the conceal base

    # guard 2 — silence cannot farm it: same day but w1 never spoke -> no verdict at all
    channel_silent = [_speech(1, "v1", targets=["v1"]), _speech(1, "v2", targets=["v1", "v1"])]
    win2 = _game(tmp_path, "cs", [_disc_case("wolf", "w1", 1, "sp_c")], roles=roles,
                 day_res=[{"day": 1, "voted_player": None}], night_res=[], day_channel=channel_silent)
    credit_apply(sp, win2, base_rates={}, discussion=True)
    assert _by_key(sp, "sp_c")["follow_count"] == 0

    # guard 1 — a day with NO accusations anywhere credits nobody's concealment
    channel_quiet = [_speech(1, "w1"), _speech(1, "v1")]
    win3 = _game(tmp_path, "cq", [_disc_case("wolf", "w1", 1, "sp_c")], roles=roles,
                 day_res=[{"day": 1, "voted_player": None}], night_res=[], day_channel=channel_quiet)
    credit_apply(sp, win3, base_rates={}, discussion=True)
    assert _by_key(sp, "sp_c")["follow_count"] == 0


# --- (k) the pass-gate: a follow claimed on a passed turn earns nothing --------------------------
def test_k_passed_turn_follow_earns_nothing(tmp_path):
    roles = {"p1": "villager", "w1": "wolf"}
    win = _game(tmp_path, "pg", [_disc_case("villager", "p1", 1, "sp1", spoke=False)],
                roles=roles, day_res=[{"day": 1, "voted_player": "w1"}])
    sp = _store(tmp_path, {"strategy_points/villager/day_discussion": [{"key": "sp1", "value": {}}]})
    stats = credit_apply(sp, win, base_rates={}, discussion=True)
    assert _by_key(sp, "sp1")["follow_count"] == 0
    assert stats["skipped"].get("passed_turn/villager/day_discussion") == 1

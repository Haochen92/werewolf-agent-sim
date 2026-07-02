"""Unit tests for the scheduler-access audit join/classification logic (Workstream 2, diag A/B/C).

Pure functions over hand-built synthetic records — no batch files, no LLM. Covers the timeline
reconstruction (the night-N-announced-day-N+1 convention), the pre-registered bandwagon and
find-disclosure matchers, and the four-way reveal/withhold classification.
"""

from __future__ import annotations

from evaluation.src.experiments.scheduler_access_audit import (
    alive_at_start_of_day,
    bandwagon_seq,
    death_day_of,
    floor_access,
    gate_silencing,
    is_find_disclosure,
    is_role_claim,
    reveal_withhold,
)


def _msg(day, seq, player, message="hi", passed=False, tier="proactive", owes=None, targets=None):
    return {
        "day": day,
        "seq": seq,
        "player": player,
        "message": "" if passed else message,
        "passed": passed,
        "firing_reason": {"tier": tier, "owes": owes or []},
        "addressed_targets": targets or [],
    }


def _accuse(target, stance="accusation", form="mention"):
    return {"target": target, "addressed_form": form, "stance": stance}


# --------------------------------------------------------------------------- timeline


def test_alive_at_start_of_day_night_announced_next_day():
    # night 1 (result day=1) kills p6; it should still count p6 alive on day 1, gone by day 2.
    record = {
        "roles": {f"player_{i}": "villager" for i in range(1, 4)} | {"player_6": "villager"},
        "day_resolutions": [],
        "night_resolutions": [{"day": 1, "deaths": ["player_6"]}],
    }
    assert "player_6" in alive_at_start_of_day(record, 1)
    assert "player_6" not in alive_at_start_of_day(record, 2)


def test_alive_at_start_of_day_lynch_same_day_gone_next():
    record = {
        "roles": {"player_1": "wolf", "player_2": "villager"},
        "day_resolutions": [{"day": 2, "voted_player": "player_1"}],
        "night_resolutions": [],
    }
    assert "player_1" in alive_at_start_of_day(record, 2)      # lynch resolves end of day 2
    assert "player_1" not in alive_at_start_of_day(record, 3)


def test_death_day_of():
    record = {
        "roles": {"player_1": "wolf", "player_5": "villager"},
        "day_resolutions": [{"day": 2, "voted_player": "player_1"}],
        "night_resolutions": [{"day": 3, "deaths": ["player_5"]}],
    }
    assert death_day_of(record, "player_1") == 3   # lynched day 2 -> absent day 3
    assert death_day_of(record, "player_5") == 4   # night 3 -> absent day 4


# --------------------------------------------------------------------------- (a) bandwagon


def test_bandwagon_needs_two_distinct_accusers():
    record = {
        "day_channel": [
            _msg(1, 0, "player_1", targets=[_accuse("player_3")]),                 # 1 accuser
            _msg(1, 1, "player_1", targets=[_accuse("player_3")]),                 # same accuser -> still 1
            _msg(1, 2, "player_2", targets=[_accuse("player_3")]),                 # 2nd distinct -> forms here
        ],
    }
    assert bandwagon_seq(record, 1) == 2


def test_bandwagon_ignores_self_accusation_and_nonaccusation():
    record = {
        "day_channel": [
            _msg(1, 0, "player_3", targets=[_accuse("player_3")]),                  # self -> ignored
            _msg(1, 1, "player_1", targets=[_accuse("player_3", stance="defense")]),  # not accusation
            _msg(1, 2, "player_2", targets=[_accuse("player_3")]),                   # only 1 real accuser
        ],
    }
    assert bandwagon_seq(record, 1) is None


# --------------------------------------------------------------------------- (c) matchers


def test_find_disclosure_requires_name_basis_and_threat():
    assert is_find_disclosure("I investigated player_8 and they are a wolf.", "player_8")
    # missing threat token
    assert not is_find_disclosure("I investigated player_8 last night.", "player_8")
    # missing investigation basis (bare suspicion)
    assert not is_find_disclosure("player_8 is definitely a wolf, trust me.", "player_8")
    # names a different player
    assert not is_find_disclosure("I investigated player_2 and found a wolf.", "player_8")


def test_role_claim_matcher():
    assert is_role_claim("As the investigator, I know player 7 is clear.")
    assert not is_role_claim("I think player_7 is suspicious.")


# --------------------------------------------------------------------------- C classification


def _find_record(run_id, inv, target, find_night, inv_msgs, lynch_day=None, target_night_death=None):
    dc = [_msg(m[0], m[1], inv, message=m[2]) for m in inv_msgs]
    day_res = []
    if lynch_day is not None:
        day_res.append({"day": lynch_day, "voted_player": target})
    night_res = []
    if target_night_death is not None:
        night_res.append({"day": target_night_death, "deaths": [target]})
    return {
        "run_id": run_id,
        "roles": {inv: "investigator", target: "wolf", "player_9": "villager"},
        "investigator_results": [
            {"day": find_night, "player_investigated": target, "role_revealed": "wolf"}
        ],
        "day_channel": dc,
        "day_resolutions": day_res,
        "night_resolutions": night_res,
    }


def test_reveal_withhold_four_classes():
    records = [
        # CONVERTED: target lynched on/after available day (find night 1 -> avail day 2)
        _find_record("g_conv", "player_1", "player_2", 1,
                     [(2, 0, "player_2 is a wolf, I investigated them")], lynch_day=2),
        # REVEALED_IGNORED: disclosed while pending, never lynched
        _find_record("g_rev", "player_1", "player_2", 1,
                     [(2, 0, "I investigated player_2 and they are a wolf")]),
        # WITHHELD: spoke while pending but never disclosed the find
        _find_record("g_wh", "player_1", "player_2", 1,
                     [(2, 0, "I am keeping an eye on player_2's behavior")]),
        # NO_FLOOR: investigator never took a non-pass turn at all
        _find_record("g_nf", "player_1", "player_2", 1, []),
        # LATE_FLOOR: target dies night 2 (absent day 3); inv only speaks day 3 (after pending window)
        _find_record("g_late", "player_1", "player_2", 1,
                     [(3, 0, "well player_2 turned out to be a wolf")],
                     target_night_death=2),
    ]
    out = reveal_withhold(records)
    classes = {d["run_id"]: d["class"] for d in out["detail"]}
    assert classes["g_rev"] == "REVEALED_IGNORED"
    assert classes["g_wh"] == "WITHHELD"
    assert classes["g_nf"] == "NO_FLOOR"
    assert classes["g_late"] == "LATE_FLOOR"
    assert out["converted_to_lynch"] == 1
    assert out["unconverted"] == 4


def test_reveal_withhold_dedups_reinvestigated_target():
    rec = _find_record("g_dup", "player_1", "player_2", 1,
                       [(2, 0, "keeping an eye on player_2")])
    rec["investigator_results"].append(
        {"day": 2, "player_investigated": "player_2", "role_revealed": "wolf"})
    out = reveal_withhold([rec])
    assert out["total_threat_finds"] == 1  # not 2


# --------------------------------------------------------------------------- A / B census


def test_floor_access_counts_tiers_and_passes():
    record = {
        "roles": {"player_1": "wolf", "player_2": "villager"},
        "day_resolutions": [],
        "night_resolutions": [],
        "day_channel": [
            _msg(1, 0, "player_1", tier="proactive"),
            _msg(1, 1, "player_1", tier="reactive", owes=["player_2"]),
            _msg(1, 2, "player_1", passed=True, tier="proactive"),
            _msg(1, 3, "player_2", tier="proactive"),
        ],
    }
    out = floor_access([record])
    wolf = out["per_role"]["wolf"]
    assert wolf["real_utterances"] == 2
    assert wolf["passes"] == 1
    assert wolf["reactive_share"] == 0.5
    villager = out["per_role"]["villager"]
    assert villager["spoke_zero_rate"] == 0.0  # spoke once, alive


def test_gate_silencing_reports_indistinguishable():
    record = {
        "roles": {"player_1": "wolf"},
        "day_channel": [
            _msg(1, 0, "player_1", passed=True, tier="proactive"),
            _msg(1, 1, "player_1", tier="proactive"),
        ],
    }
    out = gate_silencing([record])
    # A pass with empty message and proactive tier is all that's persisted -> not distinguishable.
    assert out["distinguishable"] is False
    assert out["passes_with_nonempty_message"] == 0
    assert out["pass_tier_distribution"] == {"proactive": 1}

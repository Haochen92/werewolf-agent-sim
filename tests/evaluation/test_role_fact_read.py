"""Logic tests for the role-fact reader's deterministic layer (fact sheet + golden matching).

The LLM judgment itself is validated by the --golden calibration run, not unit tests; what unit
tests can lock down is the fact sheet the judgment depends on — attacker attribution per night,
the alive set and counts, and the speaker-knowledge lines that separate lying from hallucinating.
"""

from __future__ import annotations

from evaluation.src.judges.role_fact_read import build_fact_sheet

ROLES = {
    "player_1": "wolf", "player_2": "wolf", "player_3": "serial_killer",
    "player_4": "villager", "player_5": "healer", "player_6": "investigator",
    "player_7": "vigilante", "player_8": "villager", "player_9": "villager",
}

RECORD = {
    "game_id": "g", "config_name": "test", "roles": ROLES,
    # night 1: wolves kill p4; SK targets p5 but fails; vigilante shoots p9 and lands
    "night_resolutions": [{
        "day": 1, "deaths": ["player_4", "player_9"],
        "wolves_target": "player_4", "kill_successful": True,
        "serial_killer_target": "player_5", "serial_killer_kill_landed": False,
        "vigilante_target": "player_9", "vigilante_kill_landed": True,
        "healer_target": "player_5", "healer_saved": True,
    }],
    "day_resolutions": [{"day": 2, "voted_player": "player_1", "votes": []}],
    "day_summaries": [{"day": 1, "structured": {"role_claims": [
        {"player": "player_6", "claimed_role": "investigator"}]}}],
    "investigator_results": [{"day": 1, "player_investigated": "player_2",
                              "role_revealed": "wolf"}],
}


def _cand(speaker, day=3, unit="message", text="whatever"):
    return {"speaker": speaker, "day": day, "unit": unit, "text": text,
            "anchors": [{"kind": "dead_id", "fact": "f", "span": "s"}]}


def test_deaths_carry_correct_attacker_and_lynch():
    fs = build_fact_sheet(RECORD, _cand("player_8"))
    assert "player_4 — villager — died night 1, killed by the wolves" in fs["deaths"]
    assert "player_9 — villager — died night 1, killed by the vigilante" in fs["deaths"]
    assert "player_1 — wolf — lynched by vote, day 2" in fs["deaths"]
    # SK's failed attack must NOT be attributed a kill
    assert "serial killer" not in fs["deaths"]


def test_alive_counts_include_zeroed_roles():
    fs = build_fact_sheet(RECORD, _cand("player_8"))
    assert "player_4" not in fs["alive"] and "player_8" in fs["alive"]
    assert "0 investigator" not in fs["alive_counts"]  # investigator alive
    assert "1 wolf" in fs["alive_counts"]  # one wolf lynched, one alive


def test_speaker_knowledge_wolf_pack_and_own_attacks():
    fs = build_fact_sheet(RECORD, _cand("player_2"))
    assert "player_1, player_2" in fs["knowledge"]
    assert "the wolves attacked player_4" in fs["knowledge"]


def test_speaker_knowledge_vigilante_own_shot_and_investigator_checks():
    fs = build_fact_sheet(RECORD, _cand("player_7"))
    assert "targeted player_9" in fs["knowledge"] and "shot landed" in fs["knowledge"]
    fs = build_fact_sheet(RECORD, _cand("player_6"))
    assert "player_2 is wolf (night 1)" in fs["knowledge"]


def test_claims_log_and_unit_label():
    fs = build_fact_sheet(RECORD, _cand("player_8", unit="updated_strategy"))
    assert fs["claims"] == "player_6 claimed investigator"
    assert fs["unit"] == "private strategy note"

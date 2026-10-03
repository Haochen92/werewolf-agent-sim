"""The hallucination bench's $0 parts: a frozen case rebuilds the turn's payload through the engine's
own builders, the arm comparison counts per-case changes, and curation keeps what still fails."""
from evaluation.src.cli_runner.regen_replay.both.hallucination_bench import summarize
from evaluation.src.data.builders.hallucination_bench import curate
from evaluation.src.replay.hallucination_bench import hydrate_state, turn_payload

STATE = {
    "roles": {"p1": "wolf", "p2": "villager", "p3": "investigator", "p4": "serial_killer"},
    "current_day": 2, "current_round": 0,
    "surviving_villagers": ["p2", "p3", "p4"], "surviving_wolves": ["p1"], "human_players": [],
    "day_channel": [{"day": 2, "seq": 0, "player": "p2", "message": "who did it?"}],
    "day_summaries": [{"day": 1, "summary": "quiet day", "structured": {}}],
    "dead_roster": [{"player": "p5", "role": "healer", "day": 1, "phase": "night"}],
    "agent_strategies": {"p3": "watch p1"},
    "investigator_results": [{"day": 1, "player_investigated": "p1", "role_revealed": "wolf"}],
    "vigilante_results": [], "vigilante_bullets": 0, "wolf_channel": [],
}


def _case(phase: str, speaker: str = "p3", role: str = "investigator") -> dict:
    return {"case_id": f"c-{phase}", "phase": phase, "day": 2, "speaker": speaker, "role": role,
            "state": STATE, "firing_reason": {"tier": "proactive", "owes": []},
            "memory": {"observations": [], "strategy_points": []}}


def test_state_hydrates_to_engine_types():
    s = hydrate_state(STATE)
    assert s["day_channel"][0].message == "who did it?"
    assert s["investigator_results"][0].player_investigated == "p1"
    assert s["dead_roster"][0].phase == "night"


def test_payload_comes_from_the_engine_builders_with_role_gating():
    discuss = turn_payload(_case("day_discussion"))
    assert discuss["previous_strategy"] == "watch p1"
    assert discuss["investigator_results"][0].role_revealed == "wolf"  # the investigator's own results
    vote = turn_payload(_case("day_vote", speaker="p2", role="villager"))
    assert vote["allow_abstain"] is True
    assert "investigator_results" not in vote  # never on another role's payload


def test_summary_compares_arms_case_by_case():
    cases = {"a": {"kind": "positive", "phase": "day_vote", "role": "wolf", "source": "census"},
             "b": {"kind": "control", "phase": "day_vote", "role": "wolf", "source": "census"}}
    row = lambda cid, bad: {"case_id": cid, "valid": True, "bad": bad}  # noqa: E731
    out = summarize({"old": [row("a", True), row("a", True), row("b", False)],
                     "new": [row("a", False), row("a", True), row("b", False)]}, cases)
    assert out["arms"]["old"]["bad"]["positive"] == "2/2 (100%)"
    assert out["paired_vs_first"]["new"] == {"cases": 2, "better": 1, "worse": 0, "two_sided_sign_p": 1.0}


def test_curation_keeps_positives_that_still_fail_and_every_control():
    cases = [{"case_id": "still", "kind": "positive"}, {"case_id": "fixed", "kind": "positive"},
             {"case_id": "ctl", "kind": "control"}]
    judged = [{"case_id": "still", "valid": True, "bad": True}, {"case_id": "still", "valid": True, "bad": False},
              {"case_id": "fixed", "valid": True, "bad": False}, {"case_id": "ctl", "valid": True, "bad": False}]
    kept = curate(cases, judged, min_bad_rate=0.5)
    assert [c["case_id"] for c in kept] == ["still", "ctl"]
    assert kept[0]["screen"] == {"bad": 1, "samples": 2}

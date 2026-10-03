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
    cases = {"a": {"kind": "positive", "slice": "curated", "phase": "day_vote", "role": "wolf", "source": "census"},
             "b": {"kind": "control", "slice": "control", "phase": "day_vote", "role": "wolf", "source": "census"}}
    row = lambda cid, bad: {"case_id": cid, "valid": True, "bad": bad}  # noqa: E731
    out = summarize({"old": [row("a", True), row("a", True), row("b", False)],
                     "new": [row("a", False), row("a", True), row("b", False)]}, cases)
    assert out["arms"]["old"]["bad"]["slice:curated"] == "2/2 (100%)"
    assert out["paired_vs_first"]["new"] == {"cases": 2, "better": 1, "worse": 0, "two_sided_sign_p": 1.0}


def test_curation_slices_still_failing_random_and_controls():
    cases = [{"case_id": f"p{i}", "kind": "positive"} for i in range(6)] + [{"case_id": "ctl", "kind": "control"}]
    judged = [{"case_id": f"p{i}", "valid": True, "bad": i < 3} for i in range(6)]  # p0-p2 still fail
    kept = curate(cases, judged, min_bad_rate=0.5, random_slice=2, seed=0)
    slices = {c["case_id"]: c["slice"] for c in kept}
    assert sum(v == "random" for v in slices.values()) == 2 and slices["ctl"] == "control"
    # every still-failing case is kept, in exactly one slice; passing ones only if drawn at random
    assert {"p0", "p1", "p2"} <= set(slices)
    assert all(slices[p] == "random" for p in ("p3", "p4", "p5") if p in slices)

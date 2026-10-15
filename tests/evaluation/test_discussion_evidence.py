"""The discussion-evidence runner's offline parts: a website replay rebuilt into the batch-record
shape, and the census/structural counts that need no model."""
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[2] / "evaluation/experiments/discussion_evidence.py"
_spec = importlib.util.spec_from_file_location("discussion_evidence", _PATH)
de = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(de)

REPLAY = {
    "game_id": "g1", "winner": "villagers", "model": "m", "memory": False,
    "events": [
        {"seq": 1, "day": 1, "type": "roles_assigned",
         "roles": {"p1": "wolf", "p2": "villager", "p3": "investigator", "p4": "serial_killer"}},
        {"seq": 2, "day": 1, "type": "input_request", "player": "p2", "action_kind": "day_discuss"},
        {"seq": 3, "day": 1, "type": "speech", "channel_seq": 0, "player": "p2", "message": "hi all"},
        {"seq": 4, "day": 1, "type": "pass_marker", "channel_seq": 1, "player": "p3",
         "pass_reason": "novelty_gated"},
        {"seq": 5, "day": 1, "type": "vote_cast", "voter": "p2", "votee": "p1"},
        {"seq": 6, "day": 1, "type": "lynch_result", "outcome": "tie", "player": None,
         "vote_counts": {"p1": 1}, "no_lynch_streak": 1},
        {"seq": 7, "day": 1, "type": "night_result", "save": None,
         "deaths": [{"player": "p2", "role": "villager", "attacker_types": ["serial_killer"]}]},
        {"seq": 8, "day": 1, "type": "investigation_result", "player": "p3", "target": "p1", "role": "wolf"},
        {"seq": 9, "day": 2, "type": "speech", "channel_seq": 0, "player": "p3",
         "message": "I checked p1 last night and they are a wolf"},
        {"seq": 10, "day": 2, "type": "day_summary_structured",
         "data": {"accusations": [], "role_claims": [], "village_dynamics": {"drivers": "p3"}}},
        {"seq": 11, "day": 2, "type": "game_over", "winner": "villagers"},
    ],
}


def test_replay_becomes_a_batch_record():
    r = de.record_from_replay(REPLAY)
    assert r["roles"]["p1"] == "wolf" and r["humans"] == ["p2"]
    assert [(e["player"], e["passed"]) for e in r["day_channel"]] == [("p2", False), ("p3", True), ("p3", False)]
    assert r["day_resolutions"] == [{"day": 1, "votes": [{"voter": "p2", "votee": "p1"}],
                                     "vote_counts": {"p1": 1}, "voted_player": None}]
    night = r["night_resolutions"][0]
    assert night["deaths"] == ["p2"] and night["serial_killer_target"] == "p2"
    assert r["investigator_results"] == [{"day": 1, "player_investigated": "p1", "role_revealed": "wolf"}]
    assert r["day_summaries"][0]["day"] == 2


def test_human_seats_are_context_not_measured():
    r = de.record_from_replay(REPLAY)
    s = de.structural([r])
    assert s["human_seats"] == 1 and s["agent_messages"] == 1  # only p3's day-2 line
    assert s["passes"] == {"novelty_gated": 1}
    units = de._units([r])
    assert [u["speaker"] for u in units] == ["p3"]
    # the fact sheet the judge reads is built from the rebuilt record without error
    assert "p2" in de._prompt(r, units[0])

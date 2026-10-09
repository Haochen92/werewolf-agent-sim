"""The model admission run's offline parts: which calling mode it recommends, and the three real
prompts its caching probe sends (evaluation/src/model_admission/probes.py)."""
from Agents.schemas.roles import WOLVES, lineup, side_of
from evaluation.src.model_admission import probes


def _result(mode, passed, reasoning):
    total = 27
    return {"mode": mode, "passed": f"{passed}/{total}", "all_passed": passed == total,
            "mean_per_call": {"reasoning": reasoning}}


def test_with_thinking_asked_a_mode_that_reasons_beats_one_that_silently_does_not():
    results = [_result("forced_tool", 27, 0), _result("auto_tool", 26, 40), _result("json_mode", 27, 350)]
    mode, why = probes.recommend_mode(results, "medium")
    assert mode == "json_mode" and "forced_tool also passed but did not reason" in why
    assert probes.recommend_mode(results, "minimal")[0] == "forced_tool"


def test_no_mode_passing_every_call_recommends_nothing():
    mode, why = probes.recommend_mode([_result("forced_tool", 20, 0), _result("json_mode", 25, 300)], None)
    assert mode is None and "json_mode at 25/27" in why


def test_real_prompts_fall_back_to_the_mode_that_passed_most():
    assert probes.best_mode([_result("forced_tool", 0, 0), _result("auto_tool", 17, 1200),
                             _result("json_mode", 26, 1700)]) == "json_mode"


def _ten_seat_case() -> dict:
    """A day 2 discussion case in the bench's shape, from a ten-seat game (the frozen bench is
    nine-seat, and the ten-seat prompts render only a state that carries its lineup)."""
    dealt = lineup("serial_killer", "speculator")
    players = [f"player_{i}" for i in range(1, 11)]
    roles = dict(zip(players, dealt))
    wolves = [p for p in players if side_of(roles[p]) == WOLVES]
    state = {
        "roles": roles, "lineup": dealt, "current_day": 2, "current_round": 0,
        "surviving_villagers": [p for p in players if p not in wolves and p != "player_6"],
        "surviving_wolves": wolves, "human_players": [],
        "day_channel": [
            {"day": 2, "seq": 0, "player": "player_2", "message": "Nobody claimed anything yesterday."},
            {"day": 2, "seq": 1, "player": "player_3", "message": "The healer died last night; who gains?"},
        ],
        "day_summaries": [{"day": 1, "summary": "A quiet first day.", "structured": {}}],
        "dead_roster": [{"player": "player_6", "role": "healer", "day": 1, "phase": "night"}],
        "agent_strategies": {}, "night_actions": [], "wolf_channel": [], "uses_left": {},
    }
    return {"case_id": "ten-seat", "phase": "day_discussion", "day": 2, "speaker": "player_1",
            "role": roles["player_1"], "state": state, "firing_reason": {"tier": "proactive", "owes": []}}


def test_the_caching_probe_renders_a_next_turn_that_extends_the_first_and_another_seat():
    case = _ten_seat_case()
    variants = probes.turn_variants(case)
    texts = {name: probes._text(*probes._render(c)[::2]) for name, c in variants.items()}
    assert variants["other_seat"]["speaker"] != case["speaker"]
    assert len(texts["next_turn"]) > len(texts["first"])
    # The same seat's next prompt shares most of the first; another seat shares less of it.
    same = probes._shared_prefix(texts["first"], texts["next_turn"])
    other = probes._shared_prefix(texts["first"], texts["other_seat"])
    assert same > other > 0
    assert "I want to hear from everyone" in texts["next_turn"]

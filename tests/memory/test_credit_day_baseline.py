"""Credit compares each followed decision with memory-off play on the same game day (2026-10-28).

Lessons fire at particular stages, so an all-days memory-off base mixes easy late days with hard
early ones. Hand-built games with inline decisions: the memory-off pack loses its day-2 kill and lands
its day-3 kill, so the chat channel's base is -1 on day 2, +1 on day 3, and in between over all days.
"""

from __future__ import annotations

import json

from Agents.memory.consolidation.credit import _discussion_off_base, credit_apply
from Agents.memory.consolidation.credit_rules import compute_base_rates
from tests.factories.builders import strategy_point
from tests.memory.test_ten_seat_grading import ROLES, kill_choice, night, night_case, rec

CELL = "chanteuse/night_action"
CHAT = "chanteuse/night_action/chat"


def test_a_day_two_lesson_is_compared_with_the_day_two_base(tmp_path):
    rates = compute_base_rates(_off_window(day2=20, day3=20), by_day=True)
    assert rates[CHAT] == (0.0, 40) and rates[f"{CHAT}@day2"] == (-1.0, 20)

    v = _credit(tmp_path, _on_window(follow_days=[2]), rates)
    assert v["credit_base"] == -1.0


def test_a_thin_day_falls_back_to_the_all_days_base(tmp_path):
    rates = compute_base_rates(_off_window(day2=20, day3=5), by_day=True)
    assert rates[CHAT] == (-0.6, 25) and rates[f"{CHAT}@day3"] == (1.0, 5)

    assert _credit(tmp_path, _on_window(follow_days=[3]), rates)["credit_base"] == -0.6
    # one follow on a thick day, one on a thin day: the follow-weighted mean of each one's base
    assert _credit(tmp_path, _on_window(follow_days=[2, 3]), rates)["credit_base"] == -0.8


def test_a_channel_without_memory_off_data_stays_unscored(tmp_path):
    v = _credit(tmp_path, _on_window(follow_days=[2]), {})
    assert v["follow_count"] == 1 and v["credit_base"] is None


def test_the_all_days_base_when_the_flag_is_off(tmp_path):
    off = _off_window(day2=20, day3=20)
    pooled = compute_base_rates(off)
    assert pooled == {k: r for k, r in compute_base_rates(off, by_day=True).items() if "@day" not in k}

    on = _on_window(follow_days=[2])
    assert _credit(tmp_path, on, pooled, by_day=False)["credit_base"] == 0.0
    by_day_rates = compute_base_rates(off, by_day=True)  # day keys present, but not read
    assert _credit(tmp_path, on, by_day_rates, by_day=False)["credit_base"] == 0.0


def test_the_discussion_base_is_split_by_day_too():
    lynch_town = {"day": 2, "voted_player": "p1"}
    lynch_wolf = {"day": 3, "voted_player": "p7"}
    games = [{"game_id": f"d{i}", "roles": ROLES, "night_resolutions": [],
              "day_resolutions": [lynch_town, lynch_wolf],
              "eval_cases": [_spoken("p8", 2), _spoken("p8", 3)]} for i in range(3)]
    rates = _discussion_off_base(games, by_day=True)
    assert rates["illusionist/day_discussion"] == (0.0, 6)
    assert rates["illusionist/day_discussion@day2"] == (1.0, 3)   # a town lynch: good for the pack
    assert rates["illusionist/day_discussion@day3"] == (-1.0, 3)  # a packmate lynched
    assert set(_discussion_off_base(games)) == {"illusionist/day_discussion"}


# --- helpers ---

def _credit(tmp_path, on: list, base_rates: dict, by_day: bool = True) -> dict:
    """Credit one chat lesson over ``on`` and return its stored value."""
    sp = tmp_path / "strategy_points.json"
    sp.write_text(json.dumps({"namespaces": {f"strategy_points/{CELL}": [strategy_point("k", cell=CELL)]}}))
    credit_apply(sp, on, base_rates=base_rates, by_day=by_day)
    return json.loads(sp.read_text())["namespaces"][f"strategy_points/{CELL}"][0]["value"]


def _off_window(day2: int, day3: int) -> list[dict]:
    """Memory-off games: ``day2`` pack chats on a saved (negative) night, ``day3`` on a kill (positive)."""
    lost = [_game(f"off2_{i}", [_pack_night(2, "saved")], [night_case("p7", 2, "chat")]) for i in range(day2)]
    landed = [_game(f"off3_{i}", [_pack_night(3, "killed")], [night_case("p7", 3, "chat")]) for i in range(day3)]
    return lost + landed


def _on_window(follow_days: list[int]) -> list[dict]:
    """One memory-on game per day in ``follow_days``, the chat following lesson ``k`` on a kill."""
    return [_game(f"on{d}", [_pack_night(d, "killed")], [_followed(night_case("p7", d, "chat"))])
            for d in follow_days]


def _game(gid: str, nights: list, cases: list) -> dict:
    return {"game_id": gid, "roles": ROLES, "night_resolutions": nights, "day_resolutions": [],
            "eval_cases": cases}


def _pack_night(day: int, result: str) -> dict:
    return night(day, [rec("wolves", "kill", "p1", result)], [kill_choice("p7", "p1")])


def _followed(case: dict) -> dict:
    return {**case, "memory_enabled": True, "strategy_index_to_key": {"1": "k"},
            "strategy_verdicts": [{"strategy_index": 1, "verdict": "follow"}]}


def _spoken(player: str, day: int) -> dict:
    return {"action_phase": "day_discussion", "player_id": player, "player_role": ROLES[player], "day": day,
            "agent_message": {"message": "I have a feeling about this.", "addressed_targets": []}}

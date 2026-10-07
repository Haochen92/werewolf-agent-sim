"""Night 1's default is drawn by lot, not left to the model.

With nothing in the record, the model takes the lowest-numbered seat (95 of 96 replayed night 1
choices, whatever order the list came in: discussion_evidence.md §7.5). So the engine draws the
default and the prompt offers it, on night 1 only, to the solo roles and once to the pack.
"""
from __future__ import annotations

from Agents.prompts import INVESTIGATOR_NIGHT, WOLF_NIGHT_DISCUSS
from Agents.prompts.prompt_inputs import build_agent_prompt_input, night_one_lot


SEATED = [f"player_{i}" for i in range(1, 10)]


def _payload(player_id: str, role: str, day: int = 1, game_id: str = "game-a") -> dict:
    wolves = ["player_2", "player_6"]
    return {
        "player_id": player_id,
        "player_role": role,
        "current_day": day,
        "current_round": 0,
        "game_id": game_id,
        "surviving_players": list(SEATED),
        "surviving_wolves": wolves,
        "surviving_villagers": [p for p in SEATED if p not in wolves],
        "day_channel": [],
        "day_summaries": [],
        "wolf_channel": [],
        "investigator_results": [],
        "vigilante_results": [],
        "dead_roster": [],
        "cast_role_counts": {},
    }


def _drawn(line: str) -> str:
    # "Night 1: ... drawn for you: player_7. Take it..." -> player_7
    after = line.split(": ")[-1]
    return after.split(".")[0]


def test_the_lot_is_another_living_player():
    line = night_one_lot(_payload("player_4", "investigator"))

    assert line.startswith("Night 1:")
    drawn = _drawn(line)
    assert drawn in SEATED
    assert drawn != "player_4"


def test_the_lot_is_the_same_on_a_retry():
    first = night_one_lot(_payload("player_4", "investigator"))
    again = night_one_lot(_payload("player_4", "investigator"))

    assert first == again


def test_the_lots_differ_across_players_and_games():
    drawn = set()
    for seat in SEATED:
        drawn.add(_drawn(night_one_lot(_payload(seat, "healer"))))
    for game in ("game-a", "game-b", "game-c", "game-d"):
        drawn.add(_drawn(night_one_lot(_payload("player_4", "healer", game_id=game))))

    assert len(drawn) > 1


def test_the_lot_is_not_always_the_lowest_number():
    lowest_taken = 0
    for game in ("game-a", "game-b", "game-c", "game-d", "game-e", "game-f"):
        if _drawn(night_one_lot(_payload("player_4", "serial_killer", game_id=game))) == "player_1":
            lowest_taken += 1

    assert lowest_taken < 6


def test_no_lot_after_night_one():
    assert night_one_lot(_payload("player_4", "investigator", day=2)) == ""


def test_no_lot_for_the_vigilante_or_a_villager():
    assert night_one_lot(_payload("player_4", "vigilante")) == ""
    assert night_one_lot(_payload("player_4", "villager")) == ""


def test_the_pack_draws_one_lot_among_the_non_wolves():
    first_wolf = night_one_lot(_payload("player_2", "wolf"))
    second_wolf = night_one_lot(_payload("player_6", "wolf"))

    assert "drawn for the pack" in first_wolf
    assert first_wolf == second_wolf
    assert _drawn(first_wolf) not in ("player_2", "player_6")


def test_the_night_prompts_carry_the_lot_on_night_one_only():
    night_one = INVESTIGATOR_NIGHT.invoke(build_agent_prompt_input(_payload("player_4", "investigator"))).to_string()
    night_two = INVESTIGATOR_NIGHT.invoke(
        build_agent_prompt_input(_payload("player_4", "investigator", day=2))
    ).to_string()
    pack = WOLF_NIGHT_DISCUSS.invoke(build_agent_prompt_input(_payload("player_2", "wolf"))).to_string()

    assert "a lot has been drawn for you" in night_one
    assert "a lot has been drawn" not in night_two
    assert "a lot has been drawn for the pack" in pack

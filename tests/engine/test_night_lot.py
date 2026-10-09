"""Night 1's default is drawn by lot, not left to the model.

With nothing in the record, the model takes the lowest-numbered seat (95 of 96 replayed night 1
choices, whatever order the list came in: discussion_evidence.md §7.5). So the engine draws the
default and the prompt offers it, on night 1 only, to the solo roles and once to the pack.
"""
from __future__ import annotations

import pytest

from Agents.prompts import night_template, wolf_chat_template
from Agents.prompts.prompt_inputs import build_agent_prompt_input, night_one_lot
from Agents.schemas.roles import ROLE_SPECS, lineup, roles


SEATED = [f"player_{i}" for i in range(1, 11)]
LINEUP = lineup("serial_killer", "speculator")
INVESTIGATOR_NIGHT = night_template("investigator")
PACK_CHAT = wolf_chat_template("chanteuse")


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
        # A wolf's payload on the pack's turns (the chat, the carrier's); its skill turn sets False.
        "pack_turn": True,
        "day_channel": [],
        "day_summaries": [],
        "wolf_channel": [],
        "night_actions": [],
        "dead_roster": [],
        "cast_role_counts": {},
        "lineup": LINEUP,
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


@pytest.mark.parametrize("role", ["investigator", "healer", "serial_killer", "sentinel", "trailseer", "sigilist"])
def test_every_role_that_must_choose_draws_its_own_lot(role):
    line = night_one_lot(_payload("player_4", role))

    assert "a lot has been drawn for you" in line
    assert _drawn(line) in SEATED and _drawn(line) != "player_4"


def test_no_lot_for_the_vigilante_or_the_neutrals():
    # No default is offered to a role outside the lot roles (the necromancer sits out night 1).
    for role in ("vigilante", "speculator", "fortune_teller", "necromancer"):
        assert night_one_lot(_payload("player_4", role)) == "", role


def test_the_pack_draws_one_lot_among_the_non_wolves():
    pack_roles = [role for role in roles if ROLE_SPECS[role].pack]
    assert pack_roles == ["chanteuse", "illusionist"]
    first_wolf = night_one_lot(_payload("player_2", "chanteuse"))
    second_wolf = night_one_lot(_payload("player_6", "illusionist"))

    assert "drawn for the pack" in first_wolf
    assert first_wolf == second_wolf
    assert _drawn(first_wolf) not in ("player_2", "player_6")


def test_the_night_prompts_carry_the_lot_on_night_one_only():
    night_one = INVESTIGATOR_NIGHT.invoke(build_agent_prompt_input(_payload("player_4", "investigator"))).to_string()
    night_two = INVESTIGATOR_NIGHT.invoke(
        build_agent_prompt_input(_payload("player_4", "investigator", day=2))
    ).to_string()
    pack = PACK_CHAT.invoke(build_agent_prompt_input(_payload("player_2", "chanteuse"))).to_string()

    assert "a lot has been drawn for you" in night_one
    assert "a lot has been drawn" not in night_two
    assert "a lot has been drawn for the pack" in pack


def test_a_wolfs_own_skill_turn_draws_its_own_lot():
    # The chanteuse's block is not the pack's kill: its night 1 lot is its own, among the non-wolves.
    skill = dict(_payload("player_2", "chanteuse"), pack_turn=False)
    line = night_one_lot(skill)
    assert "drawn for you" in line and _drawn(line) in skill["surviving_villagers"]
    assert night_one_lot(dict(_payload("player_6", "illusionist"), pack_turn=False)) == ""

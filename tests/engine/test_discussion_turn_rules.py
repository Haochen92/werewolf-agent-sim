"""The per-turn rules a discussion turn gets: a town seat on the open floor of a voting day is asked
for the reason behind a vote it leans to (evil and neutral seats are not: silence can be their better
play), and a reactive turn is told to answer only what is new (2026-10-12, the first Haiku game)."""

import pytest

from Agents.prompts.day_discuss import PROACTIVE_ROUND_RULES, TOWN_VOTE_REASON_RULE
from Agents.prompts.prompt_inputs import _discussion_stage_rules, _firing_brief
from Agents.schemas import FiringReason


@pytest.mark.parametrize("role", ["investigator", "sentinel", "vigilante", "healer"])
def test_a_town_seat_on_the_open_floor_of_a_voting_day_is_asked_for_its_vote_reason(role):
    rules = _discussion_stage_rules({"day_round": "proactive", "voting_available": True, "player_role": role})
    assert rules == PROACTIVE_ROUND_RULES + TOWN_VOTE_REASON_RULE


@pytest.mark.parametrize("role", ["chanteuse", "illusionist", "necromancer", "serial_killer", "speculator",
                                  "fortune_teller"])
def test_an_evil_or_neutral_seat_gets_the_open_floor_unchanged(role):
    rules = _discussion_stage_rules({"day_round": "proactive", "voting_available": True, "player_role": role})
    assert rules == PROACTIVE_ROUND_RULES


def test_no_vote_reason_on_a_day_without_a_vote():
    rules = _discussion_stage_rules({"day_round": "proactive", "voting_available": False,
                                     "player_role": "investigator"})
    assert rules == PROACTIVE_ROUND_RULES


def test_a_reactive_turn_is_told_to_answer_only_what_is_new():
    brief = _firing_brief(FiringReason(tier="reactive", owes=["player_4"]))
    assert brief.startswith("You were directly addressed by player_4.")
    assert "instead of restating it" in brief
    assert _firing_brief(FiringReason(tier="proactive", owes=[])) == ""

"""The decision tags' structural parts: the decisions a saved extraction input records, a tag's status
against them, and the day an observation's own text states (decisions §13)."""

from __future__ import annotations

from Agents.memory.extraction.decision_tags import recorded_decisions, stated_day, tag_status
from Agents.memory.extraction.offline import _with_decision_fields

ROLES = {"player_1": "sentinel", "player_2": "illusionist", "player_6": "chanteuse", "player_9": "sigilist"}

RECORD = """=== Day Discussions ===
[Day 1] game_master (unknown): There is no vote on day 1, so no one voted and no one is eliminated.
[Day 2] player_1 (sentinel): Last night I watched player_9, and no one visited them.
[Day 2] game_master (unknown): Here's the vote result for day 2:
  player_1 voted to abstain
  player_2 voted to eliminate player_9
[Day 3] player_2 (illusionist): I have nothing new.

=== Wolf Night Discussions ===
[Day 1, Round 1] player_2: Let's go with player_8.
[Day 1, Round 2] player_6: Agreed.
[Day 1, Round 4] player_2 votes: player_8

=== Night Actions (exact, from the game engine) ===
Night 1: player_1 (sentinel) watch player_9. No one visited player_9 tonight.
Night 1: the wolves kill player_8. player_8 died. They were a healer.
Night 1: player_6 (chanteuse) block player_9. player_9 was roleblocked tonight."""


def test_recorded_decisions_reads_each_kind_of_line():
    found = recorded_decisions(RECORD)
    assert ("player_1", "day_discussion", 2, "") in found
    assert ("player_1", "day_vote", 2, "") in found and ("player_2", "day_vote", 2, "") in found
    assert ("player_2", "night_action", 1, "chat") in found and ("player_6", "night_action", 1, "chat") in found
    assert ("player_2", "night_action", 1, "kill") in found  # the carrier's round-4 line
    assert ("player_6", "night_action", 1, "skill") in found and ("player_1", "night_action", 1, "skill") in found
    assert not any(p == "game_master" for p, *_ in found)


def test_tag_status():
    found = recorded_decisions(RECORD)
    assert tag_status(ROLES, "sentinel", "night_action", 1, "none", found) == "recorded"
    assert tag_status(ROLES, "sigilist", "night_action", 1, "none", found) == "not_recorded"  # kept its sigil
    assert tag_status(ROLES, "illusionist", "night_action", 1, "kill", found) == "recorded"
    assert tag_status(ROLES, "illusionist", "night_action", 1, "skill", found) == "not_recorded"
    assert tag_status(ROLES, "chanteuse", "night_action", 1, "several", found) == "recorded"
    assert tag_status(ROLES, "sentinel", "day_vote", 3, "none", found) == "not_recorded"
    assert tag_status(ROLES, "sentinel", "day_vote", 0, "none", found) == "several"


def test_stated_day_reads_one_number_for_the_phase():
    assert stated_day({"action_phase": "night_action", "approach": "On night 2 I watched the healer."}) == 2
    assert stated_day({"action_phase": "day_vote", "approach": "Voted on day 3 after the night 2 kill."}) == 3
    assert stated_day({"action_phase": "day_vote", "approach": "Voted with the room.",
                       "situation": "On day 4, two claims stood."}) == 4
    assert stated_day({"action_phase": "day_discussion", "approach": "Compared day 2 and day 3 claims."}) is None


def test_an_untagged_observation_loads_as_not_tagged():
    assert _with_decision_fields({"perspective": "healer", "action_phase": "night_action"})["decision_day"] == -1
    wolf = _with_decision_fields({"perspective": "chanteuse", "action_phase": "night_action"})
    assert wolf["pack_turn"] == "several"
    assert _with_decision_fields({"perspective": "healer", "decision_day": 3})["decision_day"] == 3

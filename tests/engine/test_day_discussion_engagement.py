"""Anti-repetition day-discussion instruction (added 2026-07-05).

Transcript-quality finding: four players opened a day with near-identical "I agree we can't keep
abstaining..." low-information restatements. A voting day's first `opener_floor` (default 3) real
utterances bypass the proactive novelty gate by design; the pre-voting opening round now lowers that
bypass to one and adds its own role-neutral rules. The general engagement rule still requires every
speaker to add NEW information or explicitly name-and-advance a prior point rather than restate one.
These tests pin both shared policies across EVERY role's day-discussion prompt.
"""
from __future__ import annotations

from Agents.prompts.day_discuss import (
    ENGAGE_WITH_DISCUSSION_RULE,
    HEALER_DAY_DISCUSS,
    INVESTIGATOR_DAY_DISCUSS,
    OPENING_NO_VOTE_DISCUSSION_RULES,
    SERIAL_KILLER_DAY_DISCUSS,
    VIGILANTE_DAY_DISCUSS,
    VILLAGER_DAY_DISCUSS,
    WOLF_DAY_DISCUSS,
)
from Agents.game_config import GameConfig
from Agents.nodes.day.flow import discussion_stage_controls
from Agents.prompts.prompt_inputs import build_agent_prompt_input

# (role, discuss template) — one entry per surviving day-acting role.
_ROLE_TEMPLATES = [
    ("villager", VILLAGER_DAY_DISCUSS),
    ("healer", HEALER_DAY_DISCUSS),
    ("investigator", INVESTIGATOR_DAY_DISCUSS),
    ("wolf", WOLF_DAY_DISCUSS),
    ("serial_killer", SERIAL_KILLER_DAY_DISCUSS),
    ("vigilante", VIGILANTE_DAY_DISCUSS),
]


def _input_for(role: str, *, voting_available: bool = True) -> dict:
    return build_agent_prompt_input(
        {
            "player_id": "player_1",
            "player_role": role,
            "current_day": 3,
            "surviving_players": ["player_1", "player_2", "player_3"],
            "surviving_wolves": ["player_1"],
            "surviving_villagers": ["player_2", "player_3"],
            "voting_available": voting_available,
        }
    )


def test_engagement_rule_present_in_every_role_discuss_prompt():
    # Load-bearing phrases: the no-restatement ban and the name-and-advance requirement.
    assert "Do NOT restate a" in ENGAGE_WITH_DISCUSSION_RULE
    assert "NAMING the player" in ENGAGE_WITH_DISCUSSION_RULE
    for role, tmpl in _ROLE_TEMPLATES:
        rendered = "\n".join(m.content for m in tmpl.format_messages(**_input_for(role)))
        assert "Engage with what has already been said" in rendered, role
        assert "Do NOT restate a" in rendered, role
        assert "NAMING the player who made it" in rendered, role


def test_opening_no_vote_rules_are_uniform_across_role_prompts():
    normalized_rules = " ".join(OPENING_NO_VOTE_DISCUSSION_RULES.split())
    assert "No elimination vote occurs" in OPENING_NO_VOTE_DISCUSSION_RULES
    assert "may simply not have received a" in OPENING_NO_VOTE_DISCUSSION_RULES
    assert 'ask the whole table for "thoughts,"' in normalized_rules
    assert 'a "blank slate,"' in normalized_rules

    for role, tmpl in _ROLE_TEMPLATES:
        opening = "\n".join(
            message.content
            for message in tmpl.format_messages(**_input_for(role, voting_available=False))
        )
        regular = "\n".join(
            message.content
            for message in tmpl.format_messages(**_input_for(role, voting_available=True))
        )
        assert "Opening round: no vote today" in opening, role
        assert "Opening round: no vote today" not in regular, role


def test_pre_voting_round_reduces_only_its_novelty_bypass():
    config = GameConfig(first_voting_day=2, opener_floor=3)
    assert discussion_stage_controls(1, config) == (False, 1)
    assert discussion_stage_controls(2, config) == (True, 3)

    # A deliberately disabled bypass stays disabled; the pre-voting rule never raises it.
    assert discussion_stage_controls(1, GameConfig(opener_floor=0)) == (False, 0)

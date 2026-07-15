"""Anti-repetition day-discussion instruction (added 2026-07-05).

Transcript-quality finding: four players opened a day with near-identical "I agree we can't keep
abstaining..." low-information restatements. The proactive novelty gate does NOT catch these because
the day's first `opener_floor` (default 3) real utterances bypass it by design, so the openers are
exactly the ungated slots. The fix is prompt-level: a shared, role-neutral rule requiring a speaker
to add NEW information or explicitly name-and-advance a prior point rather than restate one. These
tests pin that the rule is rendered in EVERY role's day-discussion prompt.
"""
from __future__ import annotations

from Agents.prompts.day_discuss import (
    ENGAGE_WITH_DISCUSSION_RULE,
    HEALER_DAY_DISCUSS,
    INVESTIGATOR_DAY_DISCUSS,
    SERIAL_KILLER_DAY_DISCUSS,
    VIGILANTE_DAY_DISCUSS,
    VILLAGER_DAY_DISCUSS,
    WOLF_DAY_DISCUSS,
)
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


def _input_for(role: str) -> dict:
    return build_agent_prompt_input(
        {
            "player_id": "player_1",
            "player_role": role,
            "current_day": 3,
            "surviving_players": ["player_1", "player_2", "player_3"],
            "surviving_wolves": ["player_1"],
            "surviving_villagers": ["player_2", "player_3"],
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

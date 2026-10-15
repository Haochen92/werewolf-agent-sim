"""Anti-repetition day-discussion instruction (added 2026-07-05).

Transcript-quality finding: four players opened a day with near-identical "I agree we can't keep
abstaining..." low-information restatements. The engagement rule requires every speaker to add
NEW information or explicitly name-and-advance a prior point rather than restate one, and day 1
carries its own no-vote rules. These tests pin both shared policies across EVERY role's
day-discussion prompt. (The novelty gate and its opener floor, which this once also described,
went with the scheduler's proactive tier on 2026-10-07.)
"""
from __future__ import annotations

from Agents.prompts.day_discuss import (
    ENGAGE_WITH_DISCUSSION_RULE,
    DAY_ONE_NO_VOTE_RULES,
    day_discuss_template,
)
from Agents.game_config import GameConfig
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.roles import ALL_LINEUPS, roles

# (role, discuss template) — one entry per role of the pool.
_ROLE_TEMPLATES = [(role, day_discuss_template(role)) for role in roles]


def _lineup_for(role: str) -> list[str]:
    """A dealt lineup that has the role (the drawn roles are in two of the four)."""
    return next(lineup for lineup in ALL_LINEUPS if role in lineup)


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
            "lineup": _lineup_for(role),
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
    normalized_rules = " ".join(DAY_ONE_NO_VOTE_RULES.split())
    assert "little public information" in normalized_rules
    assert "no elimination vote will be held" in normalized_rules
    assert "not required to manufacture a read or commitment" in normalized_rules
    assert "passing is equally valid" in normalized_rules

    for role, tmpl in _ROLE_TEMPLATES:
        opening = "\n".join(
            message.content
            for message in tmpl.format_messages(**_input_for(role, voting_available=False))
        )
        regular = "\n".join(
            message.content
            for message in tmpl.format_messages(**_input_for(role, voting_available=True))
        )
        assert "Day 1: no vote" in opening, role
        assert "Day 1: no vote" not in regular, role



def _rendered_for_round(role: str, template, day_round: str, *, voting_available: bool = True) -> str:
    prompt_input = build_agent_prompt_input(
        {
            "player_id": "player_1",
            "player_role": role,
            "current_day": 3,
            "surviving_players": ["player_1", "player_2", "player_3"],
            "surviving_wolves": ["player_1"],
            "surviving_villagers": ["player_2", "player_3"],
            "voting_available": voting_available,
            "day_round": day_round,
            "lineup": _lineup_for(role),
        }
    )
    messages = template.format_messages(**prompt_input)
    parts = []
    for message in messages:
        parts.append(message.content)
    return "\n".join(parts)


def test_each_round_of_the_day_gets_its_own_rules_block_in_every_role_prompt():
    # Phase 2: the payload's day_round picks the block; a reactive turn gets none of them.
    headings = {
        "opening": "== Opening round ==",
        "proactive": "== Open floor ==",
        "closing": "== Closing defence ==",
    }
    for role, template in _ROLE_TEMPLATES:
        for day_round, heading in headings.items():
            rendered = _rendered_for_round(role, template, day_round)
            assert heading in rendered, (role, day_round)
            for other_round, other_heading in headings.items():
                if other_round != day_round:
                    assert other_heading not in rendered, (role, day_round, other_heading)
        discussion = _rendered_for_round(role, template, "discussion")
        for heading in headings.values():
            assert heading not in discussion, (role, heading)


def test_the_day_one_opening_says_there_is_no_vote():
    for role, template in _ROLE_TEMPLATES:
        day_one = _rendered_for_round(role, template, "opening", voting_available=False)
        voting_day = _rendered_for_round(role, template, "opening", voting_available=True)
        assert "== Opening round ==" in day_one, role
        assert "Day 1: no vote" in day_one, role
        assert "Day 1: no vote" not in voting_day, role

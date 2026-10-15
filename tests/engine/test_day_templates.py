"""The ten-seat day templates, built from the role cards: every dealt role's discussion and vote turns
render in the shared-prefix layout (the public record first), ask for the reads, carry their schema's
fields, and name no undealt role."""
from __future__ import annotations

from importlib import import_module

import pytest

from Agents.prompts.common import VERDICT_EXAMPLES_PASS, memory_verdict_example
from Agents.prompts.compose import preamble
from Agents.prompts.day_discuss import day_discuss_template
from Agents.prompts.day_vote import day_vote_template
from Agents.schemas import day_discuss_output, day_vote_output
from Agents.schemas.roles import ALL_LINEUPS

POOL = sorted({role for cast in ALL_LINEUPS for role in cast})
NAMES = {role: import_module(f"Agents.prompts.roles.{role}").CARD.name for role in POOL}


def _messages(template, cast, shown=("strategy_verdicts", "memory_applicability")):
    values = {name: f"<{name}>" for name in template.input_variables}
    values["preamble"] = preamble(cast)
    # The verdict slots as a turn shown ``shown`` fills them (prompt_inputs.build_agent_prompt_input).
    values["discuss_verdict_example"] = memory_verdict_example(list(shown), indent="    ")
    values["discuss_verdict_example_pass"] = memory_verdict_example(list(shown), VERDICT_EXAMPLES_PASS, indent="    ")
    values["memory_verdict_example"] = memory_verdict_example(list(shown))
    return template.format_messages(**{k: v for k, v in values.items() if k in template.input_variables})


def _turns(cast):
    for role in cast:
        yield role, day_discuss_template(role), day_discuss_output(cast)
        yield role, day_vote_template(role), day_vote_output(cast)


@pytest.mark.parametrize("cast", ALL_LINEUPS)
def test_every_turn_renders_with_the_reads_first(cast):
    for role, template, schema in _turns(cast):
        system, human = (m.content for m in _messages(template, cast))
        assert human.startswith("== Previous days ==") and "Core Strategy" not in system, role
        assert "<tell_book>\nBefore your decision, record your current read" in human, role
        for field in schema.model_fields:
            assert f'"{field}"' in human, (role, field)


def test_a_turn_shown_no_memory_has_no_verdict_example_to_copy():
    # Haiku copied the example's "strategy_index": 1 on turns shown no lessons (2026-10-14).
    cast = ALL_LINEUPS[0]
    for role, template, _ in _turns(cast):
        human = _messages(template, cast, shown=())[-1].content
        assert '"strategy_verdicts"' not in human and '"memory_applicability"' not in human, role
        assert '"updated_strategy"' in human, role


@pytest.mark.parametrize("cast", ALL_LINEUPS)
def test_no_turn_names_an_undealt_role(cast):
    for role, template, _ in _turns(cast):
        text = "\n".join(m.content for m in _messages(template, cast)).lower()
        for other, name in NAMES.items():
            if other not in cast:
                assert name.lower() not in text, f"{role}'s turn names the undealt {name}"


def test_the_examples_name_no_seat_and_no_role():
    # A seat or a role named in a JSON example gets copied (discussion_evidence.md section 7.5).
    for role in POOL:
        for template in (day_discuss_template(role), day_vote_template(role)):
            human = template.format_messages(**{n: f"<{n}>" for n in template.input_variables})[1].content
            contract = human[human.index("You must respond with a valid JSON"):]
            assert "player_2" not in contract and '"suspected_role": "wolf"' not in contract, role


def test_town_roles_take_the_shared_vote_rules_and_the_others_their_own():
    for role in POOL:
        card = import_module(f"Agents.prompts.roles.{role}").CARD
        human = day_vote_template(role).format_messages(
            **{n: f"<{n}>" for n in day_vote_template(role).input_variables})[1].content
        shared = "a threat to the town — a wolf or the lone killer" in human
        assert shared == (card.side == "town"), role


def test_the_wolves_keep_their_channel_and_cover_reminder():
    system, human = (m.content for m in _messages(day_discuss_template("illusionist"), ALL_LINEUPS[0]))
    assert "Your private wolf channel" in human and "try to speak like a town player" in human
    assert "## ILLUSIONIST" in human and "## ILLUSIONIST" not in system

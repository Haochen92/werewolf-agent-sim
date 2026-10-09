"""The ten-seat day templates, built from the role cards: every dealt role's discussion and vote turns
render, ask for the reads first, carry their schema's fields, and name no undealt role."""
from __future__ import annotations

from importlib import import_module

import pytest

from Agents.prompts.compose import preamble
from Agents.prompts.day_discuss import day_discuss_template
from Agents.prompts.day_vote import day_vote_template
from Agents.schemas import day_discuss_output, day_vote_output
from Agents.schemas.roles import ALL_LINEUPS

POOL = sorted({role for cast in ALL_LINEUPS for role in cast})
NAMES = {role: import_module(f"Agents.prompts.roles.{role}").CARD.name for role in POOL}


def _messages(template, cast):
    values = {name: f"<{name}>" for name in template.input_variables}
    values["preamble"] = preamble(cast)
    return template.format_messages(**values)


def _turns(cast):
    for role in cast:
        yield role, day_discuss_template(role), day_discuss_output(cast)
        yield role, day_vote_template(role), day_vote_output(cast)


@pytest.mark.parametrize("cast", ALL_LINEUPS)
def test_every_turn_renders_with_the_reads_first(cast):
    for role, template, schema in _turns(cast):
        system, human = (m.content for m in _messages(template, cast))
        assert human.startswith("<tell_book>\nBefore your decision, record your current read"), role
        for field in schema.model_fields:
            assert f'"{field}"' in system, (role, field)


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
            system = template.format_messages(**{n: f"<{n}>" for n in template.input_variables})[0].content
            contract = system[system.index("You must respond with a valid JSON"):]
            assert "player_2" not in contract and '"suspected_role": "wolf"' not in contract, role


def test_town_roles_take_the_shared_vote_rules_and_the_others_their_own():
    for role in POOL:
        card = import_module(f"Agents.prompts.roles.{role}").CARD
        system = day_vote_template(role).format_messages(
            **{n: f"<{n}>" for n in day_vote_template(role).input_variables})[0].content
        shared = "a threat to the town — a wolf or the lone killer" in system
        assert shared == (card.side == "town"), role


def test_the_wolves_keep_their_channel_and_cover_reminder():
    system, human = (m.content for m in _messages(day_discuss_template("illusionist"), ALL_LINEUPS[0]))
    assert "Your private wolf channel" in human and "try to speak like a town player" in human
    assert "## ILLUSIONIST" in system

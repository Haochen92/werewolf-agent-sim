"""The ten-seat night templates, built from the role cards: every dealt role's own turn and the pack's
two turns render, ask for the reads first, carry their schema's fields, and name no undealt role."""
from __future__ import annotations

from importlib import import_module

import pytest

from Agents.prompts.compose import preamble
from Agents.prompts.night import carrier_template, night_template, wolf_chat_template
from Agents.schemas import carrier_output, night_output, wolf_chat_output
from Agents.schemas.roles import ALL_LINEUPS

WOLVES = ("chanteuse", "illusionist")
POOL = sorted({role for cast in ALL_LINEUPS for role in cast})
NAMES = {role: import_module(f"Agents.prompts.roles.{role}").CARD.name for role in POOL}


def _render(template, cast) -> str:
    values = {name: f"<{name}>" for name in template.input_variables}
    values["preamble"] = preamble(cast)
    return "\n".join(m.content for m in template.format_messages(**values))


def _turns(cast):
    for role in cast:
        yield role, night_template(role), night_output(role, cast)
    for wolf in WOLVES:
        yield wolf, wolf_chat_template(wolf), wolf_chat_output(cast)
        yield wolf, carrier_template(wolf), carrier_output(cast)


@pytest.mark.parametrize("cast", ALL_LINEUPS)
def test_every_turn_renders_with_the_reads_first(cast):
    for role, template, schema in _turns(cast):
        text = _render(template, cast)
        human = template.format_messages(**{n: f"<{n}>" for n in template.input_variables})[1].content
        assert human.index("record your current read") < human.index("Night of Day"), role
        assert "{read_targets}" not in text and "<read_targets>" in text, role
        for field in schema.model_fields:
            assert f'"{field}"' in text, (role, field)


@pytest.mark.parametrize("cast", ALL_LINEUPS)
def test_no_turn_names_an_undealt_role(cast):
    for role, template, _ in _turns(cast):
        text = _render(template, cast).lower()
        for other, name in NAMES.items():
            if other not in cast:
                assert name.lower() not in text, f"{role}'s turn names the undealt {name}"


def test_the_lot_is_offered_where_the_card_says():
    for role in POOL:
        lot = import_module(f"Agents.prompts.roles.{role}").CARD.night.lot
        assert ("night_lot" in night_template(role).input_variables) == lot, role
    for wolf in WOLVES:
        assert "night_lot" in wolf_chat_template(wolf).input_variables
        assert "night_lot" in carrier_template(wolf).input_variables


def test_a_wolf_reads_its_own_card_and_the_pack_chat():
    text = _render(wolf_chat_template("illusionist"), ALL_LINEUPS[0])
    assert "## ILLUSIONIST" in text and "Wolf night chat history" in text and "up to 3 rounds" in text

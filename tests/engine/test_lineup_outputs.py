"""The ten-seat output schemas: what the model is shown depends on who was dealt, and nothing else."""
from __future__ import annotations

import json
from importlib import import_module

import pytest
from langchain_core.utils.function_calling import convert_to_openai_tool

from Agents.schemas import (
    carrier_output,
    day_discuss_output,
    day_vote_output,
    night_output,
    wolf_chat_output,
)
from Agents.schemas.roles import ALL_LINEUPS, lineup

SK_SPECULATOR = lineup("serial_killer", "speculator")
NECRO_FORTUNE = lineup("necromancer", "fortune_teller")
TESTED_ORDER = ["strategy_verdicts", "memory_applicability", "reads", "updated_strategy"]


def _enum(model, field, nested=None):
    schema = model.model_json_schema()
    props = schema["$defs"][nested]["properties"] if nested else schema["properties"]
    return props[field]["enum"]


def _every_schema(cast):
    return [day_discuss_output(cast), day_vote_output(cast), wolf_chat_output(cast), carrier_output(cast),
            *(night_output(role, cast) for role in cast)]


def test_the_same_lineup_gets_the_same_classes():
    assert day_vote_output(SK_SPECULATOR) is day_vote_output(list(SK_SPECULATOR))
    assert night_output("healer", SK_SPECULATOR) is night_output("healer", SK_SPECULATOR)
    assert day_vote_output(SK_SPECULATOR) is not day_vote_output(NECRO_FORTUNE)


def test_an_undealt_role_has_no_night_schema():
    with pytest.raises(ValueError):
        night_output("fortune_teller", SK_SPECULATOR)


@pytest.mark.parametrize("cast", ALL_LINEUPS)
def test_the_enums_name_only_dealt_roles(cast):
    for model in _every_schema(cast):
        reads = _enum(model, "suspected_role", nested="PlayerRead")
        assert reads == ["unclear", *cast], model.__name__
    assert _enum(day_discuss_output(cast), "claim") == ["none", *cast]


@pytest.mark.parametrize("cast", [cast for cast in ALL_LINEUPS if "fortune_teller" in cast])
def test_the_fortune_teller_bets_a_dealt_role(cast):
    assert _enum(night_output("fortune_teller", cast), "bet_role") == ["none", *cast]


def test_every_dealt_role_has_a_night_output_on_its_card_field():
    for cast in ALL_LINEUPS:
        for role in cast:
            words = import_module(f"Agents.prompts.roles.{role}").CARD.night
            model = night_output(role, cast)
            fields = list(model.model_fields)
            assert fields[:4] == TESTED_ORDER, role
            assert fields[4] == words.target_field, role
            if words.no_action:
                assert f'"{words.no_action}"' in model.model_fields[words.target_field].description, role


def test_the_second_fields():
    assert list(night_output("necromancer", NECRO_FORTUNE).model_fields)[4:] == ["necromancer_target", "body"]
    assert list(night_output("fortune_teller", NECRO_FORTUNE).model_fields)[4:] == ["bet_target", "bet_role"]
    pick = _enum(night_output("speculator", SK_SPECULATOR), "speculator_pick")
    assert pick == ["town", "wolves", "lone_killer", "self", "not_yet"]
    assert _enum(night_output("illusionist", SK_SPECULATOR), "conceal") == ["conceal", "no_conceal"]


def test_the_day_and_pack_turns_keep_the_tested_order():
    assert list(day_discuss_output(SK_SPECULATOR).model_fields) == [
        *TESTED_ORDER, "pass_turn", "message", "claim", "addressed_targets",
    ]
    assert list(day_vote_output(SK_SPECULATOR).model_fields) == [*TESTED_ORDER, "vote_target"]
    assert list(wolf_chat_output(SK_SPECULATOR).model_fields) == [*TESTED_ORDER, "pass_turn", "message"]
    assert list(carrier_output(SK_SPECULATOR).model_fields) == [*TESTED_ORDER, "kill_target"]


def test_everything_but_the_verdict_lists_is_required():
    # flash-lite fails to parse optional fields, so every field the turn asks for is required.
    for model in _every_schema(SK_SPECULATOR):
        schema = model.model_json_schema()
        optional = set(schema["properties"]) - set(schema["required"])
        assert optional == {"strategy_verdicts", "memory_applicability"}, model.__name__


def test_no_class_docstring_reaches_the_model():
    for model in _every_schema(SK_SPECULATOR):
        assert "description" not in model.model_json_schema(), model.__name__


def test_the_reads_keep_the_medium_fold():
    read = day_vote_output(SK_SPECULATOR).model_fields["reads"].annotation.__args__[0]
    assert read(player="player_2", why="x", suspected_role="healer", confidence="medium").confidence == "low"


def test_the_model_sees_plain_class_names():
    # A filled class keeps its own name as the tool name and as every nested definition's key, in
    # every structured mode: tool calling, and the raw JSON schema of json_schema / json_mode.
    healer = night_output("healer", SK_SPECULATOR)
    assert healer.__name__ == "HealerOutput"
    assert convert_to_openai_tool(healer)["function"]["name"] == "HealerOutput"
    schema = healer.model_json_schema()
    assert list(schema["$defs"]) == ["MemoryVerdict", "PlayerRead", "StrategyVerdict"]
    assert schema["properties"]["reads"]["items"] == {"$ref": "#/$defs/PlayerRead"}
    assert "Literal" not in json.dumps(schema)

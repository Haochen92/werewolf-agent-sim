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
# Reads before the strategy note and the action is the tested commitment lever (T1c, 2026-07); reads
# moved ahead of the verdicts on 2026-10-13 so the schema agrees with the prompt's opening line.
TESTED_ORDER = ["reads", "strategy_verdicts", "memory_applicability", "updated_strategy"]


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
        *TESTED_ORDER, "pass_turn", "message", "claim", "claimed_night_actions", "addressed_targets",
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


# --- the speaker's claimed night actions (slice 9a, owner 2026-10-17) ---

def test_a_claimed_night_action_is_all_required_names_no_role_and_has_no_class_docstring():
    for cast in ALL_LINEUPS:
        claim = day_discuss_output(cast).model_json_schema()["$defs"]["NightActionClaim"]
        assert claim["required"] == ["night", "action", "target", "result", "seen"]
        assert "description" not in claim
        assert not set(claim["properties"]["result"]["enum"]) & {*cast, "not_a_wolf"}


def test_the_claimed_actions_ride_the_spoken_entry_when_the_line_names_them():
    from types import SimpleNamespace

    from Agents.turn.resolve import resolve_decision

    model = day_discuss_output(SK_SPECULATOR)
    claim = model.model_fields["claimed_night_actions"].annotation.__args__[0]
    said = claim(night=1, action="follow", target="player_7", result="not_said", seen=["player_8"])
    unsaid = claim(night=1, action="block", target="player_5", result="not_said", seen=[])  # the truth, not said
    unsaid_sighting = claim(night=1, action="watch", target="player_7", result="not_said", seen=["player_2"])
    reply = model(reads=[], updated_strategy="", pass_turn=False, claim="trailseer",
                  message="I followed player_7 last night and they went to player_8.",
                  claimed_night_actions=[said, unsaid, unsaid_sighting], addressed_targets=[])
    payload = {"player_id": "player_3", "current_day": 2, "day_channel": [], "day_round": "discussion"}
    turn = resolve_decision(reply, {"strategy": None, "strategy_verdicts": [], "memory_verdicts": [], "reads": []},
                            "day_channel", payload, [])
    assert [a.model_dump() for a in turn.entry.claimed_night_actions] == [
        {"night": 1, "action": "follow", "target": "player_7", "result": "not_said", "seen": ["player_8"]}]
    human = SimpleNamespace(pass_turn=False, message="I followed player_7.", addressed_targets=[])
    assert resolve_decision(human, {"strategy": None, "strategy_verdicts": [], "memory_verdicts": [], "reads": []},
                            "day_channel", payload, []).entry.claimed_night_actions == []


def test_the_speaker_and_the_summariser_share_one_action_list():
    from Agents.schemas.output import ClaimedNightAction

    spoken = day_discuss_output(SK_SPECULATOR).model_json_schema()["$defs"]["NightActionClaim"]["properties"]["action"]
    summary = ClaimedNightAction.model_json_schema()["properties"]["action"]
    assert spoken["enum"] == summary["enum"] and "visit" in spoken["enum"]

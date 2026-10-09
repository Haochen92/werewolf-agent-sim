"""The pack's night: sequential chat -> the carrier's kill -> parallel skills; routing, round
advance, the carrier's choice, the human contract.

The load-bearing invariants: chat rounds emit ONE Send at a time, the carrier first and then the
rest in roster order (each wolf must be able to read what was said before its turn); a round
advances only when every living wolf has spoken in it; the chat ends early when every wolf passed
in the same round, and is capped at WOLF_CHAT_ROUNDS; a lone wolf skips the chat; the carrier's
kill is a NightChoice and a WolfChannel entry with vote=target; then every wolf's skill turn fans
out in parallel, skipping a wolf whose ability is used up. PREPARE_PACK_NIGHT owns the round
advance, route_pack_speaker the chat hop, route_carrier the kill, pack_fan_out_skills the skills.
(The nine-seat pack vote and its tally are gone: the carrier alone names the kill.)
"""

import pytest

from langgraph.graph import END

from Agents.nodes.night import pack as pack_nodes
from Agents.nodes.night.pack import (
    CARRIER_ROUND,
    WOLF_CHAT_ROUNDS,
    carrier_kill,
    pack_fan_out_skills,
    prepare_pack_night,
    route_carrier,
    route_pack_speaker,
)
from Agents.schemas.game_events import DiscussionPassReason, WolfChannel
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import lineup
from Agents.schemas.turn import ResolvedNightChoice
from tests.factories.builders import human_turn_request
from Agents.turn.human_turn import HumanTurnContractError, validate_human_response

LINEUP = lineup("serial_killer", "speculator")
ROLES = {"w1": "chanteuse", "w2": "illusionist", "v1": "healer", "v2": "sentinel", "v3": "serial_killer"}


def _entry(wolf, round_, message="...", day=1, passed=False):
    return WolfChannel(day=day, round=round_, wolf=wolf, message="" if passed else message, vote="",
                       passed=passed, pass_reason=DiscussionPassReason.VOLUNTARY if passed else None)


def _pass(wolf, round_):
    return _entry(wolf, round_, passed=True)


def _state(wolf_channel=(), round_=1, wolves=("w1", "w2"), carrier="w2", humans=(), uses_left=None):
    return {
        "day_channel": [], "day_summaries": [], "dead_roster": [], "cast_role_counts": {},
        "lineup": LINEUP, "night_actions": [], "wolf_channel": list(wolf_channel),
        "surviving_wolves": list(wolves), "surviving_villagers": ["v1", "v2", "v3"],
        "roles": dict(ROLES), "uses_left": {"illusionist": 2} if uses_left is None else uses_left,
        "agent_strategies": {}, "human_players": list(humans), "current_day": 1,
        "current_round": round_, "carrier": carrier if wolves else "", "wolves_target": None,
        "night_choices": [],
    }


# ---- the chat: one wolf at a time, the carrier first ------------------------------------------

def test_chat_round_sends_exactly_one_wolf_the_carrier_first():
    sends = route_pack_speaker(_state())
    assert len(sends) == 1
    assert sends[0].node == "PACK_CHAT"
    assert sends[0].arg["player_id"] == "w2"  # the carrier, though w1 is first in the roster
    assert sends[0].arg["player_role"] == "illusionist"


def test_second_speaker_fires_after_the_first_spoke():
    sends = route_pack_speaker(_state(wolf_channel=[_entry("w2", 1)]))
    assert [s.arg["player_id"] for s in sends] == ["w1"]


def test_generation_failure_pass_advances_to_the_next_wolf():
    failed = WolfChannel(
        day=1,
        round=1,
        wolf="w2",
        message="",
        vote="",
        passed=True,
        pass_reason=DiscussionPassReason.GENERATION_FAILED,
    )

    sends = route_pack_speaker(_state(wolf_channel=[failed]))

    assert [send.arg["player_id"] for send in sends] == ["w1"]


def test_a_chat_payload_carries_the_packs_rosters_and_chat():
    channel = [_entry("w2", 1, message="v1 tonight?")]
    payload = route_pack_speaker(_state(wolf_channel=channel))[0].arg
    assert payload["surviving_wolves"] == ["w1", "w2"]
    assert payload["surviving_villagers"] == ["v1", "v2", "v3"]
    assert payload["wolf_channel"] == channel
    assert payload["carrier"] == "w2"
    assert payload["lineup"] == LINEUP


def test_spent_chat_routes_to_the_carrier_marker():
    assert route_pack_speaker(_state(round_=CARRIER_ROUND)) == "START_CARRIER"


def test_lone_wolf_skips_the_chat_straight_to_the_carrier():
    assert prepare_pack_night(_state(wolves=("w1",), carrier="w1"))["current_round"] == CARRIER_ROUND


def test_extinct_pack_ends_the_subgraph():
    # A shot and a lynch can wipe the pack while the game continues (the lone killer still
    # alive): the night must no-op, not crash.
    assert route_pack_speaker(_state(wolves=())) == END


def test_extinct_pack_subgraph_runs_end_to_end_without_a_kill():
    # Zero wolves -> zero Sends -> zero LLM calls: safe to invoke the real compiled subgraph.
    from Agents.graphs.night.pack import pack_night_graph_compiled

    result = pack_night_graph_compiled.invoke(_state(wolves=()))
    assert result.get("wolves_target") is None
    assert result.get("night_choices", []) == []


# ---- round advance (PREPARE_PACK_NIGHT): only when every wolf has spoken ----------------------

def test_partial_round_does_not_advance():
    out = prepare_pack_night(_state(wolf_channel=[_entry("w2", 1)]))
    assert out == {"current_round": 1}


def test_complete_round_advances():
    out = prepare_pack_night(_state(wolf_channel=[_entry("w2", 1), _entry("w1", 1)]))
    assert out == {"current_round": 2}


def test_a_round_where_one_wolf_passed_still_advances_to_the_next_round():
    out = prepare_pack_night(_state(wolf_channel=[_entry("w2", 1), _pass("w1", 1)]))
    assert out == {"current_round": 2}


def test_the_chat_ends_early_when_every_wolf_passed_in_the_same_round():
    channel = [_entry("w2", 1), _entry("w1", 1), _pass("w2", 2), _pass("w1", 2)]
    out = prepare_pack_night(_state(wolf_channel=channel, round_=2))
    assert out == {"current_round": CARRIER_ROUND}


def test_passes_in_different_rounds_do_not_end_the_chat():
    channel = [_pass("w2", 1), _entry("w1", 1), _entry("w2", 2), _pass("w1", 2)]
    out = prepare_pack_night(_state(wolf_channel=channel, round_=2))
    assert out == {"current_round": 3}


def test_the_chat_is_capped_at_three_rounds():
    assert WOLF_CHAT_ROUNDS == 3 and CARRIER_ROUND == 4
    channel = [_entry(w, r) for r in (1, 2, 3) for w in ("w2", "w1")]
    out = prepare_pack_night(_state(wolf_channel=channel, round_=WOLF_CHAT_ROUNDS))
    assert out == {"current_round": CARRIER_ROUND}


def test_only_tonights_entries_count_toward_the_round():
    # Last night's round-1 lines are still on the channel; they say nothing about tonight.
    yesterday = [_entry("w2", 1, day=0), _entry("w1", 1, day=0)]
    assert prepare_pack_night(_state(wolf_channel=yesterday)) == {"current_round": 1}


# ---- the carrier's kill -----------------------------------------------------------------------

def test_the_carrier_alone_is_sent_to_name_the_kill():
    sends = route_carrier(_state(round_=CARRIER_ROUND))
    assert [(s.node, s.arg["player_id"]) for s in sends] == [("CARRIER_KILL", "w2")]


def test_a_human_carrier_goes_to_the_uncached_twin():
    sends = route_carrier(_state(round_=CARRIER_ROUND, humans=("w2",)))
    assert [s.node for s in sends] == ["CARRIER_KILL_HUMAN"]


def test_no_living_carrier_ends_the_subgraph():
    assert route_carrier(_state(round_=CARRIER_ROUND, carrier="w9")) == END


def test_the_carriers_kill_is_a_choice_and_a_channel_entry_with_the_target_as_vote(monkeypatch):
    kill = NightChoice("w2", "illusionist", "kill", "v1")
    monkeypatch.setattr(pack_nodes, "run_memory_informed_night_action",
                        lambda *args, **kwargs: ResolvedNightChoice(entry=kill))
    payload = route_carrier(_state(round_=CARRIER_ROUND))[0].arg

    update = carrier_kill(payload, None, None)

    assert update["night_choices"] == [kill]
    assert update["wolves_target"] == "v1"
    assert update["wolf_channel"] == [
        WolfChannel(day=1, round=CARRIER_ROUND, wolf="w2", message="", vote="v1")
    ]


# ---- the skills: every wolf in parallel, after the kill --------------------------------------

def test_skills_fan_out_every_wolf_in_parallel():
    sends = pack_fan_out_skills({**_state(round_=CARRIER_ROUND), "wolves_target": "v1"})
    assert [(s.node, s.arg["player_id"], s.arg["player_role"]) for s in sends] == [
        ("PACK_SKILL", "w1", "chanteuse"), ("PACK_SKILL", "w2", "illusionist"),
    ]
    assert all(s.arg["wolves_target"] == "v1" for s in sends)


def test_a_wolf_with_no_uses_left_is_skipped():
    sends = pack_fan_out_skills(_state(round_=CARRIER_ROUND, uses_left={"illusionist": 0}))
    assert [s.arg["player_id"] for s in sends] == ["w1"]


def test_a_human_wolfs_skill_goes_to_the_uncached_twin():
    sends = pack_fan_out_skills(_state(round_=CARRIER_ROUND, humans=("w1",)))
    assert [s.node for s in sends] == ["PACK_SKILL_HUMAN", "PACK_SKILL"]


def test_no_skill_to_use_goes_straight_to_the_barrier():
    lone = _state(round_=CARRIER_ROUND, wolves=("w2",), uses_left={"illusionist": 0})
    assert pack_fan_out_skills(lone) == "COLLECT_PACK"


# ---- human contract ---------------------------------------------------------------------------

def _request(**over):
    base = dict(player_id="w1", role="chanteuse", phase="wolf_channel", valid_targets=[],
                surviving_players=["w1", "w2", "v1"], can_pass=True)
    base.update(over)
    return human_turn_request(**base)


def test_human_wolf_chat_is_a_message_or_a_pass():
    assert validate_human_response(_request(), {"message": "v1 tonight?"}).message
    assert validate_human_response(_request(), {"pass_turn": True}).pass_turn
    with pytest.raises(HumanTurnContractError):
        validate_human_response(_request(), {"message": "hi", "target": "v1"})
    with pytest.raises(HumanTurnContractError):
        validate_human_response(_request(), {"message": "  "})


def test_human_carrier_takes_a_valid_target_only():
    req = _request(phase="kill_target", valid_targets=["v1", "v2"])
    assert validate_human_response(req, {"target": "v2"}).target == "v2"
    with pytest.raises(HumanTurnContractError):
        validate_human_response(req, {"target": "w2"})
    with pytest.raises(HumanTurnContractError):
        validate_human_response(req, {"pass_turn": True})


def test_a_human_necromancer_must_name_a_body_to_act():
    req = _request(player_id="n1", role="necromancer", phase="necromancer_target",
                   valid_targets=["v1", "v2", "stay_put"], bodies=["d1"])
    assert validate_human_response(req, {"target": "v1", "body": "d1"}).body == "d1"
    with pytest.raises(HumanTurnContractError):
        validate_human_response(req, {"target": "v1"})
    with pytest.raises(HumanTurnContractError):
        validate_human_response(req, {"target": "v1", "body": "v2"})
    # Staying put needs no body.
    assert validate_human_response(req, {"target": "stay_put"}).target == "stay_put"

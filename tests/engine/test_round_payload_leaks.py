"""Leak checks for the Phase 2 turns: the rounds' payloads, held lines, and round_players on the wire.

The payload builders are the only enforced leak boundary; the round turns and the sweep turns
are new callers of them, so the standing checks in tests/leak_test.py are run over their output here.
"""
from __future__ import annotations

from Agents.nodes.day import flow
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas import DayChannel, DiscussionPassReason, FiringReason
from Agents.schemas.game_events import InvestigatorResult, NightActionRecord, WolfChannel
from server.game.translate import Translator
from tests.leak_test import (
    check_held_lines_reach_only_their_author,
    check_investigator_results_isolation,
    check_round_players_are_seat_ids,
    check_vigilante_results_isolation,
    check_wolf_channel_isolation,
    check_wolf_identity_isolation,
)


ROLES = {
    "player_1": "villager",
    "player_2": "investigator",
    "player_3": "healer",
    "player_4": "wolf",
    "player_5": "vigilante",
    "player_6": "serial_killer",
    "player_7": "wolf",
}
SEATS = ["player_1", "player_2", "player_3", "player_4", "player_5", "player_6", "player_7"]
HELD_TEXT = "player_6 has been far too quiet about the healer's save."


def day_state(**over) -> dict:
    state = {
        "current_day": 2,
        "roles": dict(ROLES),
        "human_players": [],
        "day_channel": [
            DayChannel(day=2, seq=0, player="player_1", message="I am a villager.", day_round="opening"),
            DayChannel(day=2, seq=1, player="player_3", message="", passed=True,
                       pass_reason=DiscussionPassReason.NOVELTY_GATED, gated=True,
                       gated_candidate=HELD_TEXT,
                       firing_reason=FiringReason(tier="proactive", sweep=1)),
        ],
        "day_summaries": [],
        "wolf_channel": [WolfChannel(day=1, round=1, wolf="player_4", message="take player_2 tonight",
                                     vote="")],
        "investigator_results": [InvestigatorResult(day=1, player_investigated="player_7",
                                                    role_revealed="wolf")],
        "vigilante_results": ["Your shot at player_6 failed: immune at night."],
        "vigilante_bullets": 1,
        "night_actions": [
            NightActionRecord(day=1, actor="player_3", action="protect", target="player_2",
                              outcome="your protection was not needed"),
            NightActionRecord(day=1, actor="wolves", action="kill", target="player_2",
                              outcome="your kill was blocked"),
            NightActionRecord(day=1, actor="player_5", action="shoot", target="player_6",
                              outcome="the shot did not land"),
        ],
        "surviving_villagers": ["player_1", "player_2", "player_3", "player_5", "player_6"],
        "surviving_wolves": ["player_7", "player_4"],
        "agent_strategies": {},
    }
    state.update(over)
    return state


def prompt_log_for(payloads: list[dict]) -> list[dict]:
    """The prompt_log the pipeline would record for these turns (Agents/turn/eval.log_prompt)."""
    log = []
    for payload in payloads:
        log.append({
            "player_id": payload["player_id"],
            "player_role": payload["player_role"],
            "output_key": "day_channel",
            "day": payload["current_day"],
            "round": 1,
            "prompt_input": build_agent_prompt_input(payload),
        })
    return log


def round_payloads(day_round: str, players: list[str]) -> list[dict]:
    state = day_state(day_round=day_round, round_players=players)
    payloads = []
    for send in flow.fan_out_round(state, {}):
        payloads.append(send.arg)
    return payloads


def standing_checks(log: list[dict]) -> list[str]:
    leaks = []
    leaks.extend(check_wolf_identity_isolation(log, ROLES))
    leaks.extend(check_wolf_channel_isolation(log))
    leaks.extend(check_investigator_results_isolation(log))
    leaks.extend(check_vigilante_results_isolation(log))
    return leaks


# --- the round payloads ---------------------------------------------------------------------

def test_opening_and_closing_payloads_pass_the_standing_leak_checks():
    opening = round_payloads("opening", SEATS)
    closing = round_payloads("closing", ["player_6", "player_4"])

    assert len(opening) == 7
    assert len(closing) == 2
    assert standing_checks(prompt_log_for(opening)) == []
    assert standing_checks(prompt_log_for(closing)) == []


def test_a_round_payload_carries_each_private_field_to_its_own_role_only():
    for payload in round_payloads("opening", SEATS):
        role = payload["player_role"]
        assert ("surviving_wolves" in payload) == (role == "wolf"), payload["player_id"]
        assert ("wolf_channel" in payload) == (role == "wolf"), payload["player_id"]
        assert ("investigator_results" in payload) == (role == "investigator"), payload["player_id"]
        assert ("vigilante_results" in payload) == (role == "vigilante"), payload["player_id"]
        for record in payload.get("night_actions", []):
            if role == "wolf":
                assert record.actor == "wolves"
            else:
                assert record.actor == payload["player_id"]


def test_a_sweep_turn_payload_passes_the_standing_leak_checks():
    sweep = FiringReason(tier="proactive", sweep=1)
    payloads = []
    for player in SEATS:
        send = flow.build_speaker_send(day_state(), player, ROLES[player], sweep)
        assert send.arg["day_round"] == "proactive"
        payloads.append(send.arg)

    assert standing_checks(prompt_log_for(payloads)) == []


# --- held lines -----------------------------------------------------------------------------

def test_a_held_line_reaches_its_author_and_nobody_else():
    log = prompt_log_for(round_payloads("closing", ["player_3", "player_6"]))
    log.extend(prompt_log_for(round_payloads("opening", SEATS)))

    author_prompts = []
    for entry in log:
        if entry["player_id"] == "player_3":
            author_prompts.append(entry)
    assert author_prompts
    for entry in author_prompts:
        assert HELD_TEXT in entry["prompt_input"]["day_channel"]

    assert check_held_lines_reach_only_their_author(log, [("player_3", HELD_TEXT)]) == []


def test_the_held_line_check_flags_a_planted_leak():
    log = prompt_log_for(round_payloads("closing", ["player_6"]))
    log[0]["prompt_input"]["day_channel"] += "\n" + HELD_TEXT

    leaks = check_held_lines_reach_only_their_author(log, [("player_3", HELD_TEXT)])

    assert len(leaks) == 1
    assert "player_6" in leaks[0]


# --- round_players on the wire --------------------------------------------------------------

def test_round_players_reaching_the_wire_are_seat_ids_only():
    state = day_state()
    opening = flow.start_opening(state)
    closing_state = day_state(day_channel=[
        DayChannel(day=2, seq=0, player="player_1", message="a",
                   addressed_targets=[{"target": "player_4", "addressed_form": "mention",
                                       "stance": "accusation"}]),
        DayChannel(day=2, seq=1, player="player_2", message="b",
                   addressed_targets=[{"target": "player_4", "addressed_form": "mention",
                                       "stance": "accusation"}]),
    ])
    closing = flow.start_closing(closing_state, {})

    translator = Translator()
    translator.roles = dict(ROLES)
    wire_lists = []
    for node_name, delta in [("START_OPENING", opening), ("START_CLOSING", closing)]:
        chunk = {"type": "updates", "ns": ["DAY_PHASE:x"], "data": {node_name: delta}}
        for event in translator.translate(chunk):
            if event.type == "round_opened":
                wire_lists.append(event.players)

    assert wire_lists == [SEATS, ["player_4"]]
    assert check_round_players_are_seat_ids([opening["round_players"], closing["round_players"]], ROLES) == []
    assert check_round_players_are_seat_ids(wire_lists, ROLES) == []


def test_the_round_players_check_flags_anything_but_a_seat_id():
    planted = [["player_1", "player_4 (wolf)"], [{"player": "player_4", "role": "wolf"}], "player_1"]

    leaks = check_round_players_are_seat_ids(planted, ROLES)

    assert len(leaks) == 3

"""Leak checks for the night payloads and for the inputs a finished game hands the checkers.

The payload builders are the only enforced leak boundary. tests/engine/test_round_payload_leaks.py
pins the day builders; this pins the two night builders (a solo actor's turn, a wolf's pack turn)
and the lift of the dead roster, the held lines and the night records out of the final state
(``leak_inputs``), which the batch runner passed none of before 2026-10-14.
"""
from __future__ import annotations

from Agents.nodes.night.pack import _pack_payload
from Agents.nodes.night.solo import night_turn_payload
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas import DayChannel, DiscussionPassReason, FiringReason
from Agents.schemas.game_events import DeathRecord, NightActionRecord, WolfChannel
from Agents.schemas.roles import ROLE_SPECS, lineup
from tests.leak_test import (
    check_eliminated_players_excluded,
    check_night_record_isolation,
    check_wolf_channel_isolation,
    check_wolf_identity_isolation,
    leak_inputs,
    run_leak_tests,
)


ROLES = {
    "player_1": "sentinel",
    "player_2": "investigator",
    "player_3": "healer",
    "player_4": "chanteuse",
    "player_5": "vigilante",
    "player_6": "serial_killer",
    "player_7": "illusionist",
    "player_8": "necromancer",
    "player_9": "speculator",
    "player_10": "fortune_teller",
}
WOLVES = ["player_4", "player_7"]
TOWN_AND_OTHERS = [p for p in ROLES if p not in WOLVES]
HELD_TEXT = "player_6 has been far too quiet about the healer's save."

NIGHT_RECORDS = [
    NightActionRecord(day=1, actor="player_3", action="protect", target="player_2",
                      outcome="your protection was not needed"),
    NightActionRecord(day=1, actor="wolves", action="kill", target="player_2",
                      outcome="your kill was blocked"),
    NightActionRecord(day=1, actor="player_5", action="shoot", target="player_6",
                      outcome="the shot did not land"),
    NightActionRecord(day=1, actor="player_2", action="investigate", target="player_7",
                      outcome="player_7 reads Suspicious.", result="suspicious", seen=["player_7"]),
]


def night_state(**over) -> dict:
    state = {
        "current_day": 2,
        "roles": dict(ROLES),
        "human_players": [],
        "day_channel": [
            DayChannel(day=2, seq=0, player="player_1", message="I am the sentinel.", day_round="opening"),
        ],
        "day_summaries": [],
        "dead_roster": [],
        "wolf_channel": [WolfChannel(day=2, round=1, wolf="player_4", message="take player_2 tonight",
                                     vote="")],
        "lineup": lineup("serial_killer", "speculator"),
        "uses_left": {"vigilante": 1, "illusionist": 2, "investigator": 2, "sentinel": 2},
        "night_actions": NIGHT_RECORDS,
        "surviving_villagers": TOWN_AND_OTHERS,
        "surviving_wolves": WOLVES,
        "agent_strategies": {},
        "carrier": "player_4",
        "wolves_target": "",
    }
    state.update(over)
    return state


def entry(payload: dict, output_key: str) -> dict:
    """The prompt_log entry the pipeline would record for this turn (Agents/turn/eval.log_prompt)."""
    return {
        "player_id": payload["player_id"],
        "player_role": payload["player_role"],
        "output_key": output_key,
        "day": payload["current_day"],
        "round": payload.get("current_round", 0),
        "prompt_input": build_agent_prompt_input(payload),
    }


def night_log(state: dict | None = None) -> list[dict]:
    """One night turn per living player: solo actors through their own builder, wolves through
    the pack's."""
    state = state or night_state()
    log = []
    for player in state["surviving_villagers"]:
        role = ROLES[player]
        log.append(entry(night_turn_payload(state, player, role), ROLE_SPECS[role].target_field))
    for wolf in state["surviving_wolves"]:
        log.append(entry(_pack_payload(state, wolf), "wolf_channel"))
    return log


# --- the night payloads ----------------------------------------------------------------------

def test_a_solo_night_payload_carries_no_pack_field_and_only_its_own_record():
    state = night_state()
    for player in TOWN_AND_OTHERS:
        payload = night_turn_payload(state, player, ROLES[player])
        assert "surviving_wolves" not in payload, player
        assert "surviving_villagers" not in payload, player
        assert "wolf_channel" not in payload, player
        assert player not in payload["surviving_players"], player
        for record in payload["night_actions"]:
            assert record.actor == player, (player, record.actor)
        assert ("uses_left" in payload) == (ROLE_SPECS[ROLES[player]].uses is not None), player
        assert ("speculator_pick" in payload) == (ROLES[player] == "speculator"), player
        assert ("fortune_points" in payload) == (ROLES[player] == "fortune_teller"), player
        assert ("bodies" in payload) == (ROLES[player] == "necromancer"), player


def test_a_pack_payload_carries_the_pack_to_a_wolf_and_the_pack_record_only():
    state = night_state()
    for wolf in WOLVES:
        payload = _pack_payload(state, wolf)
        assert payload["surviving_wolves"] == WOLVES
        assert payload["wolf_channel"] == state["wolf_channel"]
        assert wolf not in payload["surviving_players"]
        for record in payload["night_actions"]:
            assert record.actor in ("wolves", wolf), (wolf, record.actor)


def test_the_night_payloads_pass_the_standing_leak_checks():
    log = night_log()
    assert len(log) == len(ROLES)
    assert check_wolf_identity_isolation(log, ROLES) == []
    assert check_wolf_channel_isolation(log) == []
    assert check_night_record_isolation(log, NIGHT_RECORDS, ROLES) == []


def test_the_night_record_check_flags_a_record_planted_in_another_players_payload():
    log = night_log()
    town = next(e for e in log if e["player_id"] == "player_1")
    town["prompt_input"]["night_actions"] += "\nplayer_7 reads Suspicious."

    leaks = check_night_record_isolation(log, NIGHT_RECORDS, ROLES)

    assert len(leaks) == 1
    assert "player_1" in leaks[0] and "player_2's night record" in leaks[0]


# --- the inputs lifted from a finished game ---------------------------------------------------

def finished_game() -> dict:
    return night_state(
        day_channel=[
            DayChannel(day=2, seq=0, player="player_1", message="I am the sentinel.", day_round="opening"),
            DayChannel(day=2, seq=1, player="player_3", message="", passed=True,
                       pass_reason=DiscussionPassReason.NOVELTY_GATED, gated=True,
                       gated_candidate=HELD_TEXT,
                       firing_reason=FiringReason(tier="proactive", sweep=1)),
            DayChannel(day=2, seq=2, player="player_5", message="", passed=True,
                       pass_reason=DiscussionPassReason.VOLUNTARY),
        ],
        dead_roster=[
            DeathRecord(player="player_2", role="investigator", day=1, phase="night"),
            DeathRecord(player="player_9", role="speculator", day=2, phase="day"),
        ],
        surviving_villagers=[p for p in TOWN_AND_OTHERS if p not in ("player_2", "player_9")],
    )


def test_leak_inputs_lift_the_dead_roster_the_held_lines_and_the_night_records():
    inputs = leak_inputs(finished_game())

    assert [d.player for d in inputs["deaths"]] == ["player_2", "player_9"]
    assert inputs["gated_candidates"] == [HELD_TEXT]
    assert inputs["night_records"] == NIGHT_RECORDS


def test_leak_inputs_of_an_empty_result_feed_nothing():
    assert leak_inputs({}) == {"deaths": [], "gated_candidates": [], "night_records": []}


def test_a_full_run_over_the_night_log_with_the_lifted_inputs_is_clean():
    result = finished_game()
    assert run_leak_tests(night_log(result), ROLES, **leak_inputs(result)) == []


def test_a_full_run_flags_a_dead_player_who_was_still_prompted():
    result = finished_game()
    log = night_log(result) + [entry(night_turn_payload(result, "player_2", "investigator"),
                                     "investigator_target")]
    leaks = run_leak_tests(log, ROLES, **leak_inputs(result))
    assert len(leaks) == 1 and "dead player player_2" in leaks[0]


# --- the dead stay unprompted ------------------------------------------------------------------

def _prompt(player: str, day: int, output_key: str) -> dict:
    return {"player_id": player, "player_role": ROLES[player], "output_key": output_key,
            "day": day, "round": 1, "prompt_input": {}}


def test_a_player_killed_at_night_may_act_that_night_but_not_the_next_day():
    deaths = [DeathRecord(player="player_2", role="investigator", day=1, phase="night")]
    log = [_prompt("player_2", 1, "day_channel"), _prompt("player_2", 1, "investigator_target")]
    assert check_eliminated_players_excluded(log, deaths) == []

    log.append(_prompt("player_2", 2, "day_channel"))
    leaks = check_eliminated_players_excluded(log, deaths)
    assert len(leaks) == 1 and "player_2" in leaks[0]


def test_a_player_lynched_by_day_gets_no_night_turn_that_day():
    deaths = [DeathRecord(player="player_9", role="speculator", day=2, phase="day")]
    log = [_prompt("player_9", 2, "day_channel"), _prompt("player_9", 2, "day_votes")]
    assert check_eliminated_players_excluded(log, deaths) == []

    log.append(_prompt("player_9", 2, "speculator_pick"))
    leaks = check_eliminated_players_excluded(log, deaths)
    assert len(leaks) == 1 and "player_9" in leaks[0]


def test_the_eliminated_check_takes_death_dicts_as_well():
    deaths = [{"player": "player_2", "role": "investigator", "day": 1, "phase": "night"}]
    log = [_prompt("player_2", 3, "day_channel")]
    assert len(check_eliminated_players_excluded(log, deaths)) == 1

"""The read-out wills as data (ReadOutWill, Agents/rules/night_record.py `read_out_will`), slice 6 of
the deduction engine, and the rebuild of the mornings and the wills from prose for a payload from
before they were kept (Agents/rules/public_prose.py).

A revealed town player's record is read out twice at its reveal, in the same node, from the same
records: the moderator's sentence, which the players read, and the same record as data, which the
deduction engine reads (catalogue L11, R8). These tests hold the two together: the prose read back
equals the data, at every morning and every lynch of random games and of whole games on the real
graph; every payload carries the data, and only from the reveal on; the data survives a checkpoint;
and the frozen replay cases, which carry only prose, are rebuilt to what the engine would have kept.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from Agents.deduction import seat_view_from_payload
from Agents.memory.checkpointer import durable_serde
from Agents.nodes.day import flow
from Agents.nodes.night.pack import _pack_payload
from Agents.nodes.night.solo import night_turn_payload
from Agents.rules.night_record import read_out_will
from Agents.rules.public_prose import announcement_from_prose, public_data_from_summaries, wills_from_prose
from Agents.schemas import FiringReason
from Agents.schemas.game_events import DaySummary, ReadOutWill, WillClause
from tests.engine.test_night_payload_leaks import night_state
from tests.engine.test_round_payload_leaks import day_state
from tests.factories.random_nights import random_game

# --- the prose and the data agree ---------------------------------------------------------------

def test_every_will_read_out_in_random_games_is_the_data_its_node_committed():
    rng = random.Random(20261017)
    kinds_seen = set()
    for _ in range(1500):
        game = random_game(rng)
        for message, wills in game.messages:
            assert wills_from_prose(message) == wills, message
            for will in wills:
                kinds_seen.add(f"read at {will.phase}")
                kinds_seen |= {f"{clause.action} {clause.result}" for clause in will.clauses}
                if not will.clauses:
                    kinds_seen.add("nothing on record")
    assert kinds_seen >= {
        "read at night", "read at day", "nothing on record", "None roleblocked", "hold_fire held",
        "protect saved", "protect no_attack", "protect self_bet_saved", "shoot killed", "shoot saved",
        "shoot immune", "investigate suspicious", "investigate not_suspicious", "watch seen", "follow seen",
        "sigil hit", "sigil saved", "sigil miss",
    }, kinds_seen


@pytest.mark.parametrize("game", [
    {"lone_killer": "serial_killer", "neutral": "speculator"},
    {"lone_killer": "necromancer", "neutral": "fortune_teller"},
])
def test_in_a_whole_game_every_ai_turn_has_exactly_the_wills_read_out_before_it(monkeypatch, game):
    """On the real graph: the state's wills equal the prose read back, and every AI turn's payload
    carries exactly the wills (and mornings) its own game-master prose had read out by then."""
    from Agents.prompts import prompt_inputs
    from tests.engine.test_ten_seat_game import _play

    carried = []
    engine_entry = prompt_inputs._own_result_lines

    def spy(payload):
        carried.append(dict(payload))
        return engine_entry(payload)

    monkeypatch.setattr(prompt_inputs, "_own_result_lines", spy)
    # Its own seed: a game id already played in this process would resume on that game's state.
    result, _, _ = _play(monkeypatch, game, seed=7)
    mornings, wills = public_data_from_summaries(result["day_summaries"])
    assert result["read_out_wills"] and wills == result["read_out_wills"]
    assert mornings == result["night_announcements"]
    assert carried
    for payload in carried:
        mornings, wills = public_data_from_summaries(payload["day_summaries"])
        assert payload["read_out_wills"] == wills
        assert payload["night_announcements"] == mornings


# --- the data rides every seat's payload, from the reveal on --------------------------------------

WILL = ReadOutWill(holder="player_2", role="investigator", day=1, phase="night",
                   clauses=[WillClause(night=1, action="investigate", target="player_5", result="suspicious")])


def test_every_night_payload_carries_the_wills():
    state = night_state(read_out_wills=[WILL])
    for player, role in state["roles"].items():
        if player in state["surviving_wolves"]:
            assert _pack_payload(state, player)["read_out_wills"] == [WILL]
        else:
            assert night_turn_payload(state, player, role)["read_out_wills"] == [WILL]


def test_every_day_payload_carries_the_wills():
    state = day_state(read_out_wills=[WILL])
    sweep = FiringReason(tier="proactive", sweep=1)
    for player, role in state["roles"].items():
        assert flow.build_speaker_send(state, player, role, sweep).arg["read_out_wills"] == [WILL]
    for send in flow.fan_out_day(state, "vote"):
        assert send.arg["read_out_wills"] == [WILL]


def test_a_will_is_in_the_public_record_from_its_reveal_and_never_before():
    """Random games: at each point a seat reasons from (after a lynch, after a morning), the
    public record holds exactly the wills of the messages read out so far."""
    rng = random.Random(7)
    for _ in range(300):
        game = random_game(rng)
        for point, snapshot in enumerate(game.snapshots):
            read_so_far = [will for _, wills in game.messages[:point + 1] for will in wills]
            assert snapshot.wills == read_so_far


def test_the_wills_survive_a_checkpoint_round_trip_and_stored_dicts_read_like_live_models():
    serde = durable_serde()
    assert serde.loads_typed(serde.dumps_typed([WILL])) == [WILL]
    live = seat_view_from_payload({"read_out_wills": [WILL], "night_announcements": []})
    stored = seat_view_from_payload({"read_out_wills": [WILL.model_dump()], "night_announcements": []})
    assert live == stored and live.wills == [WILL]


# --- a payload from before: rebuilt from the prose -------------------------------------------------

MORNING_TWO = ("Night of day 2: player_4 was killed by the wolves last night. They were a investigator. The "
               "record of player_4, the investigator: night 1, checked player_6: Suspicious. player_5 was "
               "killed by a reanimated wolf last night. Their role is hidden by a reanimated illusionist. The "
               "Speculator has picked Town.")


def test_a_payload_without_the_keys_rebuilds_them_from_its_game_master_prose():
    summaries = [DaySummary(day=2, summary=MORNING_TWO, source="game_master"),
                 DaySummary(day=2, summary="player_3 said things.", source="discussion")]
    view = seat_view_from_payload({"day_summaries": summaries})
    assert view.announcements == [announcement_from_prose(MORNING_TWO)]
    assert view.wills == [ReadOutWill(holder="player_4", role="investigator", day=2, phase="night", clauses=[
        WillClause(night=1, action="investigate", target="player_6", result="suspicious")])]
    # A payload that has the keys keeps them, even empty: day 1 has no morning yet.
    assert seat_view_from_payload({"day_summaries": summaries, "night_announcements": [],
                                   "read_out_wills": []}).wills == []


def test_a_morning_the_reader_does_not_recognise_is_left_out_not_misread():
    garbled = MORNING_TWO.replace("killed by the wolves", "eaten by the wolves")
    with pytest.raises(ValueError):
        announcement_from_prose(garbled)
    assert public_data_from_summaries([DaySummary(day=2, summary=garbled, source="game_master")]) == ([], [])


FROZEN = Path("evidence/reasoning_failures/data")
FROZEN_FILES = ["haiku_effort_replay/turn_cases.jsonl", "haiku_effort_replay/vote_cases.jsonl",
                "deduction_injection/cases.jsonl", "deduction_injection/silence_cases.jsonl"]


@pytest.mark.parametrize("name", FROZEN_FILES)
def test_the_frozen_cases_rebuild_to_the_data_the_engine_would_have_kept(name):
    """Every frozen case's prose is read in full, and agrees with the engine data the case does
    carry: each will equals the one built from the case's own night records, each morning's
    deaths equal the dead roster's night deaths, and the pick the state's."""
    from evaluation.src.replay.hallucination_bench import hydrate_state

    cases = [json.loads(line) for line in (FROZEN / name).read_text().splitlines() if line.strip()]
    assert cases
    for case in cases:
        assert "night_announcements" not in case["state"] and "read_out_wills" not in case["state"]
        state = hydrate_state(case["state"])
        game_master = [s.summary for s in state["day_summaries"] if s.source == "game_master"]
        assert len(state["night_announcements"]) == sum(text.startswith("Night of day") for text in game_master)

        built = [read_out_will(death.player, death.role, state["night_actions"], death.day, death.phase)
                 for death in state["dead_roster"] if death.role]
        assert state["read_out_wills"] == [will for will in built if will is not None], case["case_id"]

        announced = [(a.night, d.player, d.role) for a in state["night_announcements"] for d in a.deaths]
        on_roster = [(d.day, d.player, d.role) for d in state["dead_roster"] if d.phase == "night"]
        assert announced == on_roster, case["case_id"]
        picks = [a.pick for a in state["night_announcements"] if a.pick]
        assert picks == ([state["speculator_pick"]] if state.get("speculator_pick") else []), case["case_id"]

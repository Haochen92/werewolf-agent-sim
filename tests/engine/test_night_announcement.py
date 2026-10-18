"""The morning announcement as data (Agents/rules/announcement.py), slice 4 of the deduction engine.

The resolution node writes the morning twice: the moderator's prose, which the players read, and
the same morning as data, which the deduction engine reads. Both come from one NightReport at one
point in the node; these tests hold them together. The prose is parsed with the announcement's
own grammar (Agents/rules/public_prose.py, not taken from the node), on random legal nights and on whole
games with read-out wills, and the parse must equal the data. Then: the data rides every seat's
payload, day and night, and survives a checkpoint; and the night records carry the attacker types
and the bet's role the engine used to parse out of their prose.
"""

from __future__ import annotations

import random

import pytest

from Agents.deduction import seat_view_from_payload
from Agents.memory.checkpointer import durable_serde
from Agents.nodes.day import flow
from Agents.nodes.night.pack import _pack_payload
from Agents.nodes.night.solo import night_turn_payload
from Agents.rules.night import resolve_night
from Agents.rules.night_record import night_action_records
from Agents.rules.public_prose import announcement_from_prose
from Agents.schemas import FiringReason
from Agents.schemas.game_events import AnnouncedDeath, NightAnnouncement
from Agents.schemas.night import NightChoice
from tests.engine.deduction.test_own_results import _game
from tests.engine.test_night_payload_leaks import night_state
from tests.engine.test_round_payload_leaks import day_state
from tests.factories.random_nights import random_night, resolve_through_the_node

# The morning's grammar, as the players read it, now lives in Agents/rules/public_prose.py: the
# deduction engine uses it to rebuild the morning for a payload from before the data was kept. It
# raises on any sentence it does not recognise, which fails these tests.
parse_morning = announcement_from_prose


# --- the prose and the data agree ---------------------------------------------------------------

def test_the_data_says_exactly_what_the_prose_says_on_random_nights():
    rng = random.Random(20261017)
    kinds_seen = set()
    for _ in range(4000):
        game = random_night(rng)
        assert parse_morning(game.morning) == game.announcement, game.morning
        announcement = game.announcement
        kinds_seen |= {death.hidden_by or "revealed" for death in announcement.deaths}
        kinds_seen |= {save.saver for save in announcement.saves}
        kinds_seen |= {"pick"} if announcement.pick else set()
        kinds_seen |= {"no_one_died"} if announcement.no_one_died else set()
    assert kinds_seen == {"revealed", "illusionist", "reanimated_illusionist", "healer", "reanimated_healer",
                          "self_bet", "pick", "no_one_died"}


def test_a_will_read_out_in_the_morning_is_not_part_of_the_data():
    """A night-2 death of the healer reads out its night-1 record; the data holds the death alone."""
    roles, player_of = _game("serial_killer", "speculator")
    healer, sentinel = player_of["healer"], player_of["sentinel"]
    alive = list(roles)
    night_one = [NightChoice(healer, "healer", "protect", sentinel)]
    earlier = night_action_records(night_one, resolve_night(night_one, roles, 1), roles)
    update = resolve_through_the_node([NightChoice(player_of["chanteuse"], "chanteuse", "kill", healer)],
                                      roles, 2, alive, earlier_records=earlier)
    morning = update["day_summaries"][0].summary
    assert f"The record of {healer}, the healer: night 1, protected {sentinel}" in morning
    assert parse_morning(morning) == update["night_announcements"][0] == NightAnnouncement(
        night=2, deaths=[AnnouncedDeath(player=healer, attacker_types=["wolves"], role="healer")])


@pytest.mark.parametrize("game", [
    {"lone_killer": "serial_killer", "neutral": "speculator"},
    {"lone_killer": "necromancer", "neutral": "fortune_teller"},
])
def test_in_a_whole_game_every_morning_has_its_data_and_every_ai_turn_gets_it(monkeypatch, game):
    from Agents.prompts import prompt_inputs
    from tests.engine.test_ten_seat_game import _play

    # Every AI turn's prompt input goes through the engine's entry; record what each payload carried.
    carried = []
    engine_entry = prompt_inputs._own_result_lines

    def spy(payload):
        carried.append((payload.get("current_day"), payload.get("player_role"),
                        len(payload.get("night_announcements", []))))
        return engine_entry(payload)

    monkeypatch.setattr(prompt_inputs, "_own_result_lines", spy)
    result, _, _ = _play(monkeypatch, game, seed=5)
    mornings = [message.message for message in result["day_channel"]
                if message.player == "game_master" and message.message.startswith("Night of day")]
    assert mornings and len(mornings) == len(result["night_announcements"])
    for morning, announcement in zip(mornings, result["night_announcements"]):
        assert parse_morning(morning) == announcement
    # On day n and on night n, the mornings of nights 1 to n-1 are on the payload, for every role.
    assert {day for day, _, _ in carried} >= {1, 2}
    assert all(count == day - 1 for day, _, count in carried), carried


# --- the data rides every seat's payload ---------------------------------------------------------

MORNING = NightAnnouncement(night=1, deaths=[AnnouncedDeath(player="player_2", attacker_types=["wolves"],
                                                            role="investigator")])


def test_every_night_payload_carries_the_morning():
    state = night_state(night_announcements=[MORNING])
    for player, role in state["roles"].items():
        if player in state["surviving_wolves"]:
            assert _pack_payload(state, player)["night_announcements"] == [MORNING]
        else:
            assert night_turn_payload(state, player, role)["night_announcements"] == [MORNING]


def test_every_day_payload_carries_the_morning():
    state = day_state(night_announcements=[MORNING])
    sweep = FiringReason(tier="proactive", sweep=1)
    for player, role in state["roles"].items():
        assert flow.build_speaker_send(state, player, role, sweep).arg["night_announcements"] == [MORNING]
    for send in flow.fan_out_day(state, "vote"):
        assert send.arg["night_announcements"] == [MORNING]


def test_the_seat_view_reads_a_stored_morning_like_a_live_one():
    live = seat_view_from_payload({"night_announcements": [MORNING]})
    stored = seat_view_from_payload({"night_announcements": [MORNING.model_dump()]})
    assert live == stored and live.announcements == [MORNING]


def test_the_morning_survives_a_checkpoint_round_trip():
    serde = durable_serde()
    assert serde.loads_typed(serde.dumps_typed([MORNING])) == [MORNING]


# --- the record's structured fields -------------------------------------------------------------

def test_a_saved_targets_records_name_its_attackers_and_the_prose_is_unchanged():
    roles, player_of = _game("necromancer", "speculator")
    target = player_of["sentinel"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", target),
               NightChoice(target, "sentinel", "watch", player_of["healer"]),
               NightChoice(player_of["sigilist"], "sigilist", "sigil", target),
               NightChoice(player_of["vigilante"], "vigilante", "kill", player_of["trailseer"]),
               NightChoice(player_of["healer"], "healer", "protect", target)]
    records = {record.actor: record for record in night_action_records(choices, resolve_night(choices, roles, 2), roles)}
    assert records[player_of["healer"]].attacker_types == ["wolves"]
    assert records[player_of["healer"]].outcome == f"{target} was attacked by the wolves, and your protection saved them."
    assert records["wolves"].attacker_types == ["wolves"]
    assert records[player_of["vigilante"]].attacker_types == []  # the trailseer died: no survived attack
    assert records[player_of["sigilist"]].attacker_types == []  # a sigil's own record is not an attacked one


def test_a_self_bet_saves_records_name_the_attackers_on_every_side():
    roles, player_of = _game("serial_killer", "fortune_teller")
    fortune_teller = player_of["fortune_teller"]
    choices = [NightChoice(player_of["serial_killer"], "serial_killer", "kill", fortune_teller),
               NightChoice(player_of["vigilante"], "vigilante", "kill", fortune_teller),
               NightChoice(fortune_teller, "fortune_teller", "bet", fortune_teller),
               NightChoice(player_of["healer"], "healer", "protect", fortune_teller)]
    records = night_action_records(choices, resolve_night(choices, roles, 2), roles)
    assert [record.attacker_types for record in records] == [["serial_killer", "vigilante"]] * 4
    assert [record.result for record in records] == ["self_bet_saved", "self_bet_saved", "self_bet", "self_bet_saved"]


def test_a_bets_record_names_the_role_it_bet_on_and_old_records_still_load():
    roles, player_of = _game("serial_killer", "fortune_teller")
    healer = player_of["healer"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", healer),
               NightChoice(player_of["fortune_teller"], "fortune_teller", "bet", healer, role_named="healer")]
    record = night_action_records(choices, resolve_night(choices, roles, 1), roles)[1]
    assert (record.result, record.bet_role, record.outcome) == (
        "scored_2", "healer", f"{healer} died and was a healer: two points.")
    old = record.model_dump(exclude={"attacker_types", "bet_role"})
    assert type(record).model_validate(old).bet_role is None

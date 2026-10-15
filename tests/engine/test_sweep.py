"""The proactive sweep (Phase 2 step 4c): who gets the floor when nobody owes an answer.

The scheduler is stateless, so which sweep is running is read back from the transcript's sweep
marks; these cases pin that reading on hand-built days, with no model and no graph.
"""
from __future__ import annotations

from Agents.game_config import GameConfig
from Agents.schemas import (
    AddressedTarget,
    DayChannel,
    DiscussionPassReason,
    FiringReason,
)
from Agents.turn.scheduler import select_next_speaker


SURVIVORS = ["player_1", "player_2", "player_3", "player_4"]


# --- builders: one per kind of transcript entry ------------------------------------------

def opening_pass(seq: int, player: str) -> DayChannel:
    return DayChannel(day=2, seq=seq, player=player, message="", day_round="opening",
                      passed=True, pass_reason=DiscussionPassReason.VOLUNTARY)


def opening_line(seq: int, player: str) -> DayChannel:
    return DayChannel(day=2, seq=seq, player=player, message="I am the healer.",
                      day_round="opening")


def sweep_pass(seq: int, player: str, sweep: int) -> DayChannel:
    return DayChannel(day=2, seq=seq, player=player, message="", day_round="proactive",
                      passed=True, pass_reason=DiscussionPassReason.VOLUNTARY,
                      firing_reason=FiringReason(tier="proactive", sweep=sweep))


def sweep_line(seq: int, player: str, sweep: int, targets=None) -> DayChannel:
    if targets is None:
        targets = []
    return DayChannel(day=2, seq=seq, player=player, message="a new point", day_round="proactive",
                      addressed_targets=targets,
                      firing_reason=FiringReason(tier="proactive", sweep=sweep))


def sweep_held(seq: int, player: str, sweep: int) -> DayChannel:
    return DayChannel(day=2, seq=seq, player=player, message="", day_round="proactive",
                      passed=True, pass_reason=DiscussionPassReason.NOVELTY_GATED,
                      gated=True, gated_candidate="the same point again",
                      firing_reason=FiringReason(tier="proactive", sweep=sweep))


def reactive_line(seq: int, player: str, owes: list[str]) -> DayChannel:
    responses = []
    for creditor in owes:
        responses.append(AddressedTarget(target=creditor, addressed_form="response", stance="defense"))
    return DayChannel(day=2, seq=seq, player=player, message="I answer you.",
                      addressed_targets=responses,
                      firing_reason=FiringReason(tier="reactive", owes=owes))


def accuse(target: str) -> list[AddressedTarget]:
    return [AddressedTarget(target=target, addressed_form="mention", stance="accusation")]


def quiet_opening() -> list[DayChannel]:
    day = []
    for seq, player in enumerate(SURVIVORS):
        day.append(opening_pass(seq, player))
    return day


def next_turn(day: list[DayChannel], max_sweeps: int = 2):
    return select_next_speaker(day, SURVIVORS, GameConfig(max_proactive_sweeps=max_sweeps))


# --- sweep 1 --------------------------------------------------------------------------------

def test_first_sweep_goes_round_the_silent_survivors_in_seat_order():
    day = quiet_opening()

    decision = next_turn(day)

    assert decision.terminate is False
    assert decision.speaker == "player_1"
    assert decision.firing_reason.tier == "proactive"
    assert decision.firing_reason.sweep == 1

    day.append(sweep_pass(4, "player_1", 1))
    decision = next_turn(day)
    assert decision.speaker == "player_2"
    assert decision.firing_reason.sweep == 1


def test_first_sweep_skips_a_player_who_spoke_in_the_opening():
    day = [
        opening_pass(0, "player_1"),
        opening_line(1, "player_2"),
        opening_pass(2, "player_3"),
        opening_pass(3, "player_4"),
        sweep_pass(4, "player_1", 1),
    ]

    decision = next_turn(day)

    assert decision.speaker == "player_3"
    assert decision.firing_reason.sweep == 1


def test_a_debt_outranks_the_next_sweep_player():
    day = quiet_opening()
    day.append(sweep_line(4, "player_1", 1, targets=accuse("player_4")))

    decision = next_turn(day)

    # player_2 is next in the sweep, but player_4 owes player_1 an answer.
    assert decision.speaker == "player_4"
    assert decision.firing_reason.tier == "reactive"
    assert decision.firing_reason.owes == ["player_1"]
    assert decision.firing_reason.sweep == 0


def test_a_player_who_answered_a_debt_during_the_sweep_is_not_asked_in_it():
    day = quiet_opening()
    day.append(sweep_line(4, "player_1", 1, targets=accuse("player_3")))
    day.append(reactive_line(5, "player_3", owes=["player_1"]))
    day.append(sweep_pass(6, "player_2", 1))

    decision = next_turn(day)

    # player_3 spoke (in answer to player_1), so the sweep moves on to player_4.
    assert decision.speaker == "player_4"
    assert decision.firing_reason.sweep == 1


def test_a_player_who_passed_in_this_sweep_is_not_asked_again_in_it():
    day = quiet_opening()
    day.append(sweep_pass(4, "player_1", 1))
    day.append(sweep_pass(5, "player_2", 1))
    day.append(sweep_line(6, "player_3", 1))

    decision = next_turn(day)

    assert decision.speaker == "player_4"
    assert decision.firing_reason.sweep == 1


# --- sweep 2 --------------------------------------------------------------------------------

def test_no_second_sweep_when_the_first_produced_no_line():
    day = quiet_opening()
    day.append(sweep_pass(4, "player_1", 1))
    day.append(sweep_pass(5, "player_2", 1))
    day.append(sweep_pass(6, "player_3", 1))
    day.append(sweep_pass(7, "player_4", 1))

    decision = next_turn(day)

    assert decision.terminate is True
    assert decision.terminate_reason == "no_obligations"


def test_a_second_sweep_follows_a_first_that_produced_a_line():
    day = [
        opening_pass(0, "player_1"),
        opening_line(1, "player_2"),
        opening_pass(2, "player_3"),
        opening_pass(3, "player_4"),
        sweep_pass(4, "player_1", 1),
        sweep_line(5, "player_3", 1),
        sweep_pass(6, "player_4", 1),
    ]

    decision = next_turn(day)

    # Sweep 2 asks those silent since sweep 1 began: player_1 and player_4 passed, and
    # player_2 spoke only in the opening; player_3 spoke in sweep 1.
    assert decision.terminate is False
    assert decision.speaker == "player_1"
    assert decision.firing_reason.tier == "proactive"
    assert decision.firing_reason.sweep == 2

    day.append(sweep_pass(7, "player_1", 2))
    decision = next_turn(day)
    assert decision.speaker == "player_2"
    assert decision.firing_reason.sweep == 2

    day.append(sweep_pass(8, "player_2", 2))
    decision = next_turn(day)
    assert decision.speaker == "player_4"
    assert decision.firing_reason.sweep == 2


def test_a_player_held_by_the_echo_gate_is_not_asked_again_that_day():
    day = quiet_opening()
    day.append(sweep_held(4, "player_1", 1))
    day.append(sweep_line(5, "player_2", 1))
    day.append(sweep_pass(6, "player_3", 1))
    day.append(sweep_pass(7, "player_4", 1))

    decision = next_turn(day)

    # player_1's line was held in sweep 1: sweep 2 starts with player_3 (a voluntary pass is
    # asked again), not player_1.
    assert decision.speaker == "player_3"
    assert decision.firing_reason.sweep == 2

    day.append(sweep_pass(8, "player_3", 2))
    decision = next_turn(day)
    assert decision.speaker == "player_4"

    day.append(sweep_pass(9, "player_4", 2))
    decision = next_turn(day)
    assert decision.terminate is True
    assert decision.terminate_reason == "no_obligations"


# --- the sweep budget -------------------------------------------------------------------------

def test_the_day_ends_when_the_sweeps_are_used_up():
    day = quiet_opening()
    day.append(sweep_line(4, "player_1", 1))
    day.append(sweep_pass(5, "player_2", 1))
    day.append(sweep_pass(6, "player_3", 1))
    day.append(sweep_pass(7, "player_4", 1))
    day.append(sweep_line(8, "player_2", 2))
    day.append(sweep_pass(9, "player_3", 2))
    day.append(sweep_pass(10, "player_4", 2))

    decision = next_turn(day, max_sweeps=2)

    # Sweep 2 produced a line, but two sweeps is the budget: no third.
    assert decision.terminate is True
    assert decision.terminate_reason == "no_obligations"


def test_one_sweep_budget_stops_after_the_first_sweep():
    day = quiet_opening()
    day.append(sweep_line(4, "player_1", 1))
    day.append(sweep_pass(5, "player_2", 1))
    day.append(sweep_pass(6, "player_3", 1))
    day.append(sweep_pass(7, "player_4", 1))

    decision = next_turn(day, max_sweeps=1)

    assert decision.terminate is True
    assert decision.terminate_reason == "no_obligations"


def test_zero_sweeps_means_no_sweep_at_all():
    day = quiet_opening()

    decision = next_turn(day, max_sweeps=0)

    assert decision.terminate is True
    assert decision.terminate_reason == "no_obligations"


def test_zero_sweeps_still_answers_a_debt_from_the_opening():
    day = quiet_opening()
    day[1] = DayChannel(day=2, seq=1, player="player_2", message="I checked player_4: wolf.",
                        day_round="opening", addressed_targets=accuse("player_4"))

    decision = next_turn(day, max_sweeps=0)

    assert decision.speaker == "player_4"
    assert decision.firing_reason.tier == "reactive"
    assert decision.firing_reason.owes == ["player_2"]

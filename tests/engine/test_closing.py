"""Who gets the closing defence, and the moderator's line that calls them (Agents/rules/closing.py).

The moderator's words are taken as fact by every reader, so the line must name exactly the
accusers the tags record; these cases pin the count, the threshold, the order and the wording.
"""
from __future__ import annotations

import pytest

from Agents.rules.closing import Accused, closing_announcement, closing_speakers
from Agents.schemas import AddressedTarget, DayChannel, DiscussionPassReason, FiringReason


ALIVE = ["player_1", "player_2", "player_3", "player_4", "player_5", "player_6", "player_7"]


def accusation(target: str) -> AddressedTarget:
    return AddressedTarget(target=target, addressed_form="mention", stance="accusation")


def said(seq: int, player: str, targets: list[AddressedTarget], day: int = 2) -> DayChannel:
    return DayChannel(day=day, seq=seq, player=player, message="I suspect them.",
                      addressed_targets=targets)


def accusers_by_player(result: list[Accused]) -> dict[str, tuple[str, ...]]:
    table: dict[str, tuple[str, ...]] = {}
    for trial in result:
        table[trial.player] = trial.accusers
    return table


# --- who qualifies --------------------------------------------------------------------------

def test_two_different_accusers_put_a_player_on_trial():
    day = [
        said(0, "player_2", [accusation("player_5")]),
        said(1, "player_4", [accusation("player_5")]),
    ]

    result = closing_speakers(day, 2, ALIVE)

    assert accusers_by_player(result) == {"player_5": ("player_2", "player_4")}


def test_one_player_accusing_twice_counts_once():
    day = [
        said(0, "player_2", [accusation("player_5")]),
        said(1, "player_2", [accusation("player_5")]),
    ]

    assert closing_speakers(day, 2, ALIVE) == []


def test_nobody_with_two_accusers_means_no_closing():
    day = [
        said(0, "player_2", [accusation("player_5")]),
        said(1, "player_3", [accusation("player_6")]),
        said(2, "player_4", [AddressedTarget(target="player_5", addressed_form="question",
                                             stance="neutral")]),
    ]

    assert closing_speakers(day, 2, ALIVE) == []


def test_only_accusation_tags_count():
    day = [
        said(0, "player_2", [accusation("player_5")]),
        said(1, "player_3", [AddressedTarget(target="player_5", addressed_form="mention",
                                             stance="defense")]),
        said(2, "player_4", [AddressedTarget(target="player_5", addressed_form="question",
                                             stance="neutral")]),
    ]

    assert closing_speakers(day, 2, ALIVE) == []


def test_self_accusation_dead_target_other_days_and_the_moderator_do_not_count():
    day = [
        said(0, "player_2", [accusation("player_5")]),
        said(1, "player_5", [accusation("player_5")]),            # accusing oneself
        said(2, "player_3", [accusation("player_9")]),            # player_9 is dead
        said(3, "player_4", [accusation("player_9")]),
        said(0, "player_6", [accusation("player_5")], day=1),     # yesterday
        said(4, "game_master", [accusation("player_5")]),         # narration
    ]

    assert closing_speakers(day, 2, ALIVE) == []


def test_a_voluntary_pass_carries_no_accusation():
    passed = DayChannel(day=2, seq=1, player="player_4", message="", passed=True,
                        pass_reason=DiscussionPassReason.VOLUNTARY,
                        addressed_targets=[accusation("player_5")])
    day = [said(0, "player_2", [accusation("player_5")]), passed]

    assert closing_speakers(day, 2, ALIVE) == []


def test_a_line_held_by_the_echo_gate_does_not_count_its_accuser():
    # Ruling 2026-10-07 after the step 8 games: the table never heard a held line, so its author
    # is not named as an accuser (before this, held echoes counted).
    held = DayChannel(day=2, seq=1, player="player_4", message="", passed=True,
                      pass_reason=DiscussionPassReason.NOVELTY_GATED, gated=True,
                      gated_candidate="player_5 is lying too.",
                      addressed_targets=[accusation("player_5")],
                      firing_reason=FiringReason(tier="proactive", sweep=1))
    day = [said(0, "player_2", [accusation("player_5")]), held]

    result = closing_speakers(day, 2, ALIVE)

    # one spoken accuser only: nobody is on trial
    assert accusers_by_player(result) == {}


# --- the order and the limit ----------------------------------------------------------------

def test_more_accusers_first_and_at_most_two_players():
    day = [
        said(0, "player_1", [accusation("player_6")]),
        said(1, "player_2", [accusation("player_6")]),
        said(2, "player_3", [accusation("player_5")]),
        said(3, "player_4", [accusation("player_5")]),
        said(4, "player_7", [accusation("player_5")]),
        said(5, "player_1", [accusation("player_2")]),
        said(6, "player_3", [accusation("player_2")]),
    ]

    result = closing_speakers(day, 2, ALIVE)

    called = []
    for trial in result:
        called.append(trial.player)
    # player_5 has three accusers; player_6 and player_2 have two each, and player_2 was
    # accused more recently, so player_2 takes the second place.
    assert called == ["player_5", "player_2"]


def test_accusers_are_listed_in_the_order_they_first_accused():
    day = [
        said(0, "player_7", [accusation("player_5")]),
        said(1, "player_2", [accusation("player_5")]),
        said(2, "player_7", [accusation("player_5")]),
        said(3, "player_4", [accusation("player_5")]),
    ]

    (trial,) = closing_speakers(day, 2, ALIVE)

    assert trial.accusers == ("player_7", "player_2", "player_4")
    assert trial.latest_seq == 3


# --- the moderator's line -------------------------------------------------------------------

def test_the_announcement_names_exactly_the_accusers_the_tags_record():
    day = [
        said(0, "player_2", [accusation("player_5")]),
        said(1, "player_4", [accusation("player_5"), accusation("player_6")]),
        said(2, "player_7", [accusation("player_5")]),
        said(3, "player_1", [accusation("player_6")]),
    ]

    line = closing_announcement(closing_speakers(day, 2, ALIVE))

    assert line == ("Before the vote: player_5 has been accused by player_2, player_4 and player_7; "
                    "player_6 by player_4 and player_1. Each gets a last word.")


def test_the_announcement_for_one_accused():
    trial = Accused(player="player_5", accusers=("player_2", "player_4"), latest_seq=4)

    line = closing_announcement([trial])

    assert line == ("Before the vote: player_5 has been accused by player_2 and player_4. "
                    "player_5 gets a last word.")


def test_no_announcement_without_an_accused_player():
    with pytest.raises(ValueError):
        closing_announcement([])

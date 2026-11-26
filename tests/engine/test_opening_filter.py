"""The opening filter (Agents/turn/round_filter.py): an allow-list over the opening round's lines.

A held opening is a line nobody hears, so what is held, what is kept, and what happens when the
judge fails all decide what the table sees; the judge is faked here, the bookkeeping is real.
"""
from __future__ import annotations

from types import SimpleNamespace

from langchain_core.runnables import RunnableLambda

from Agents.nodes.day import flow
from Agents.schemas import AddressedTarget, DayChannel, DiscussionPassReason, OpeningVerdict, OpeningVerdicts
from Agents.turn import round_filter
from tests.factories.scripted_model import FakeModels


def opening(player: str, message: str, targets=None) -> DayChannel:
    if targets is None:
        targets = []
    return DayChannel(day=2, seq=0, player=player, message=message, day_round="opening",
                      addressed_targets=targets)


def opening_pass(player: str) -> DayChannel:
    return DayChannel(day=2, seq=0, player=player, message="", day_round="opening", passed=True,
                      pass_reason=DiscussionPassReason.VOLUNTARY)


def judge_saying(kinds: dict[str, str], seen: list | None = None):
    """Models whose judge's structured call labels each player with ``kinds``."""
    def answer(prompt_value):
        if seen is not None:
            seen.append(prompt_value.to_string())
        verdicts = []
        for player, kind in kinds.items():
            verdicts.append(OpeningVerdict(player=player, kind=kind, why="test"))
        return OpeningVerdicts(verdicts=verdicts)

    return FakeModels(judge=SimpleNamespace(with_structured_output=lambda _schema: RunnableLambda(answer)))


def failing_judge():
    def answer(_prompt_value):
        raise ConnectionError("provider down")

    return FakeModels(judge=SimpleNamespace(with_structured_output=lambda _schema: RunnableLambda(answer)))


def test_padding_and_a_repeat_are_held_with_their_text_kept():
    # Arrange
    entries = [
        opening("player_1", "I investigated player_4 last night: wolf.",
                [AddressedTarget(target="player_4", addressed_form="mention", stance="accusation")]),
        opening("player_2", "Good that the healer saved someone; now let's look at the votes."),
        opening("player_3", "player_1 investigated player_4, who is a wolf."),
    ]
    models = judge_saying({"player_1": "night_action", "player_2": "other",
                           "player_3": "repeat"})

    # Act
    out = round_filter.filter_openings(entries, models=models)

    # Assert
    kept, padding, repeat = out
    assert kept.passed is False
    assert kept.message == "I investigated player_4 last night: wolf."
    assert kept.opening_kind == "night_action"

    assert padding.passed is True
    assert padding.pass_reason == DiscussionPassReason.OPENING_FILTERED
    assert padding.gated is True
    assert padding.message == ""
    assert padding.gated_candidate == "Good that the healer saved someone; now let's look at the votes."
    assert padding.opening_kind == "other"

    assert repeat.passed is True
    assert repeat.pass_reason == DiscussionPassReason.OPENING_FILTERED
    assert repeat.gated_candidate == "player_1 investigated player_4, who is a wolf."
    assert repeat.opening_kind == "repeat"


def test_a_counterclaim_is_kept():
    # Arrange: two players both claim to be the investigator
    entries = [
        opening("player_2", "I am the investigator."),
        opening("player_6", "No, I am the investigator, and player_2 is lying."),
    ]
    models = judge_saying({"player_2": "claim", "player_6": "claim"})

    # Act
    out = round_filter.filter_openings(entries, models=models)

    # Assert
    assert out[0].passed is False
    assert out[0].opening_kind == "claim"
    assert out[1].passed is False
    assert out[1].message == "No, I am the investigator, and player_2 is lying."
    assert out[1].opening_kind == "claim"


def test_a_held_line_keeps_its_accusation_tags():
    # Arrange
    tag = AddressedTarget(target="player_4", addressed_form="mention", stance="accusation")
    entries = [opening("player_2", "player_4 seems shifty to me.", [tag])]
    models = judge_saying({"player_2": "other"})

    # Act
    (held,) = round_filter.filter_openings(entries, models=models)

    # Assert
    assert held.passed is True
    assert held.addressed_targets == [tag]


def test_every_line_is_kept_when_the_judge_fails():
    # Arrange: a judge that fails
    entries = [
        opening("player_1", "I am the healer."),
        opening("player_2", "Let's all be careful today."),
    ]
    models = failing_judge()

    # Act
    out = round_filter.filter_openings(entries, models=models)

    # Assert
    assert out == entries


def test_a_line_with_no_verdict_is_kept():
    # Arrange: a judge that gives a verdict for player_1 only
    entries = [
        opening("player_1", "I am the healer."),
        opening("player_2", "Let's all be careful today."),
    ]
    models = judge_saying({"player_1": "claim"})

    # Act
    out = round_filter.filter_openings(entries, models=models)

    # Assert
    assert out[1].passed is False
    assert out[1].message == "Let's all be careful today."


def test_passes_are_not_sent_to_the_judge_and_a_silent_round_makes_no_call():
    # Arrange
    seen: list[str] = []
    models = judge_saying({"player_2": "claim"}, seen)

    # Round 1: a round in which every player passes
    silent = [opening_pass("player_1"), opening_pass("player_2")]
    assert round_filter.filter_openings(silent, models=models) == silent
    assert seen == []

    # Round 2: a round with one pass and one line
    mixed = [opening_pass("player_1"), opening("player_2", "I am the healer.")]
    round_filter.filter_openings(mixed, models=models)
    assert len(seen) == 1
    assert "1. player_2: I am the healer." in seen[0]
    assert "player_1" not in seen[0]


def test_a_human_opening_is_never_held():
    # Arrange: a judge that would hold both lines; player_2 is human
    entries = [
        opening("player_1", "Watch player_3 today."),
        opening("player_2", "Watch player_3 today, I mean it."),
    ]
    models = judge_saying({"player_1": "other", "player_2": "other"})
    state = {"human_players": ["player_2"]}

    # Act
    out = flow._filter_keeping_humans(entries, state,
                                      lambda lines: round_filter.filter_openings(lines, models=models))

    # Assert
    assert out[0].passed is True
    assert out[0].pass_reason == DiscussionPassReason.OPENING_FILTERED
    assert out[1] == entries[1]


def test_a_line_whose_own_fields_say_night_action_or_claim_is_kept_whatever_the_judge_says():
    # The judge labelled a trailseer's follow "other" in the persona voice games (2026-10-18).
    from Agents.schemas.game_events import SpokenNightAction

    # Arrange: three lines the judge calls "other"; two say a night action or claim in their fields
    follow = opening("player_1", "Night 3 I followed player_10, and they went to player_2. player_10, why?")
    follow = follow.model_copy(update={"claimed_night_actions": [
        SpokenNightAction(night=3, action="follow", target="player_10", result="not_said", seen=["player_2"])]})
    claim = opening("player_2", "I'm the healer, and I want player_5 to answer for their vote.")
    claim = claim.model_copy(update={"claim": "healer"})
    unnamed = opening("player_3", "Let's look at the votes first.").model_copy(update={"claim": "sentinel"})
    models = judge_saying({"player_1": "other", "player_2": "other", "player_3": "other"})

    # Act
    out = round_filter.filter_openings([follow, claim, unnamed], models=models)

    # Assert
    assert [(e.passed, e.opening_kind) for e in out] == [(False, "night_action"), (False, "claim"), (True, "other")]

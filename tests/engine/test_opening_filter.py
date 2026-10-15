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


def opening(player: str, message: str, targets=None) -> DayChannel:
    if targets is None:
        targets = []
    return DayChannel(day=2, seq=0, player=player, message=message, day_round="opening",
                      addressed_targets=targets)


def opening_pass(player: str) -> DayChannel:
    return DayChannel(day=2, seq=0, player=player, message="", day_round="opening", passed=True,
                      pass_reason=DiscussionPassReason.VOLUNTARY)


def judge_saying(kinds: dict[str, str], seen: list | None = None):
    """A stand-in for get_llm_judge whose structured call labels each player with ``kinds``."""
    def answer(prompt_value):
        if seen is not None:
            seen.append(prompt_value.to_string())
        verdicts = []
        for player, kind in kinds.items():
            verdicts.append(OpeningVerdict(player=player, kind=kind, why="test"))
        return OpeningVerdicts(verdicts=verdicts)

    return lambda: SimpleNamespace(with_structured_output=lambda _schema: RunnableLambda(answer))


def failing_judge():
    def answer(_prompt_value):
        raise ConnectionError("provider down")

    return lambda: SimpleNamespace(with_structured_output=lambda _schema: RunnableLambda(answer))


def test_padding_and_a_repeat_are_held_with_their_text_kept(monkeypatch):
    entries = [
        opening("player_1", "I investigated player_4 last night: wolf.",
                [AddressedTarget(target="player_4", addressed_form="mention", stance="accusation")]),
        opening("player_2", "Good that the healer saved someone; now let's look at the votes."),
        opening("player_3", "player_1 investigated player_4, who is a wolf."),
    ]
    monkeypatch.setattr(round_filter, "get_llm_judge",
                        judge_saying({"player_1": "night_action", "player_2": "other",
                                      "player_3": "repeat"}))

    out = round_filter.filter_openings(entries)

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


def test_a_counterclaim_is_kept(monkeypatch):
    entries = [
        opening("player_2", "I am the investigator."),
        opening("player_6", "No, I am the investigator, and player_2 is lying."),
    ]
    monkeypatch.setattr(round_filter, "get_llm_judge",
                        judge_saying({"player_2": "claim", "player_6": "claim"}))

    out = round_filter.filter_openings(entries)

    assert out[0].passed is False
    assert out[0].opening_kind == "claim"
    assert out[1].passed is False
    assert out[1].message == "No, I am the investigator, and player_2 is lying."
    assert out[1].opening_kind == "claim"


def test_a_held_line_keeps_its_accusation_tags(monkeypatch):
    tag = AddressedTarget(target="player_4", addressed_form="mention", stance="accusation")
    entries = [opening("player_2", "player_4 seems shifty to me.", [tag])]
    monkeypatch.setattr(round_filter, "get_llm_judge", judge_saying({"player_2": "other"}))

    (held,) = round_filter.filter_openings(entries)

    assert held.passed is True
    assert held.addressed_targets == [tag]


def test_every_line_is_kept_when_the_judge_fails(monkeypatch):
    entries = [
        opening("player_1", "I am the healer."),
        opening("player_2", "Let's all be careful today."),
    ]
    monkeypatch.setattr(round_filter, "get_llm_judge", failing_judge())

    out = round_filter.filter_openings(entries)

    assert out == entries


def test_a_line_with_no_verdict_is_kept(monkeypatch):
    entries = [
        opening("player_1", "I am the healer."),
        opening("player_2", "Let's all be careful today."),
    ]
    monkeypatch.setattr(round_filter, "get_llm_judge", judge_saying({"player_1": "claim"}))

    out = round_filter.filter_openings(entries)

    assert out[1].passed is False
    assert out[1].message == "Let's all be careful today."


def test_passes_are_not_sent_to_the_judge_and_a_silent_round_makes_no_call(monkeypatch):
    seen: list[str] = []
    monkeypatch.setattr(round_filter, "get_llm_judge", judge_saying({"player_2": "claim"}, seen))

    silent = [opening_pass("player_1"), opening_pass("player_2")]
    assert round_filter.filter_openings(silent) == silent
    assert seen == []

    mixed = [opening_pass("player_1"), opening("player_2", "I am the healer.")]
    round_filter.filter_openings(mixed)
    assert len(seen) == 1
    assert "1. player_2: I am the healer." in seen[0]
    assert "player_1" not in seen[0]


def test_a_human_opening_is_never_held(monkeypatch):
    entries = [
        opening("player_1", "Watch player_3 today."),
        opening("player_2", "Watch player_3 today, I mean it."),
    ]
    monkeypatch.setattr(round_filter, "get_llm_judge",
                        judge_saying({"player_1": "other", "player_2": "other"}))
    state = {"human_players": ["player_2"]}

    out = flow._filter_keeping_humans(entries, state, round_filter.filter_openings)

    assert out[0].passed is True
    assert out[0].pass_reason == DiscussionPassReason.OPENING_FILTERED
    assert out[1] == entries[1]

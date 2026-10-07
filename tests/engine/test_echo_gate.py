"""The per-line echo gate on sweep turns (Agents/turn/echo_gate.py, called from resolve_decision).

A held line is never heard, so the gate must hold only a clear repeat, never touch the turns the
owner exempted, and fail open; the judge is faked, the decision code around it is real.
"""
from __future__ import annotations

from types import SimpleNamespace

from langchain_core.exceptions import OutputParserException
from langchain_core.runnables import RunnableLambda

from Agents.schemas import (
    AddressedTarget,
    DayChannel,
    DiscussionPassReason,
    FiringReason,
    LineEchoVerdict,
)
from Agents.turn import echo_gate, resolve
from Agents.turn.scheduler import build_reactive_queue


# --- builders -----------------------------------------------------------------------------

def spoken(seq: int, player: str, message: str, targets=None) -> DayChannel:
    if targets is None:
        targets = []
    return DayChannel(day=2, seq=seq, player=player, message=message, addressed_targets=targets)


def voluntary_pass(seq: int, player: str) -> DayChannel:
    return DayChannel(day=2, seq=seq, player=player, message="", passed=True,
                      pass_reason=DiscussionPassReason.VOLUNTARY)


def accusation(target: str) -> AddressedTarget:
    return AddressedTarget(target=target, addressed_form="mention", stance="accusation")


def judge_saying(adds: str, same_point_as: str, seen: list | None = None):
    def answer(prompt_value):
        if seen is not None:
            seen.append(prompt_value.to_string())
        return LineEchoVerdict(new_point="a point", adds=adds, same_point_as=same_point_as)

    return lambda: SimpleNamespace(with_structured_output=lambda _schema: RunnableLambda(answer))


def judge_raising(error: Exception):
    def answer(_prompt_value):
        raise error

    return lambda: SimpleNamespace(with_structured_output=lambda _schema: RunnableLambda(answer))


EARLIER = [
    spoken(0, "player_2", "player_5 claimed healer only after the vote went against them."),
    voluntary_pass(1, "player_3"),
    DayChannel(day=2, seq=2, player="game_master", message="A moderator line."),
]


# --- line_echo_of: when it holds ----------------------------------------------------------

def test_holds_when_the_line_adds_nothing_and_names_an_earlier_speaker(monkeypatch):
    monkeypatch.setattr(echo_gate, "get_llm_judge", judge_saying("nothing", "player_2"))

    echo = echo_gate.line_echo_of("player_5's healer claim came late.", "player_4", EARLIER)

    assert echo == "player_2"


def test_the_adds_answer_is_normalised_before_it_is_read(monkeypatch):
    monkeypatch.setattr(echo_gate, "get_llm_judge", judge_saying("  Nothing. ", "player_2"))

    echo = echo_gate.line_echo_of("player_5's healer claim came late.", "player_4", EARLIER)

    assert echo == "player_2"


def test_keeps_a_line_that_adds_something_even_when_a_player_is_named(monkeypatch):
    monkeypatch.setattr(echo_gate, "get_llm_judge",
                        judge_saying("asks player_5 to name who they protected", "player_2"))

    echo = echo_gate.line_echo_of("player_2 is right; player_5, who did you protect?", "player_4",
                                  EARLIER)

    assert echo == ""


def test_keeps_a_line_whose_named_repeat_is_the_speaker_or_nobody(monkeypatch):
    monkeypatch.setattr(echo_gate, "get_llm_judge", judge_saying("nothing", "player_4"))
    assert echo_gate.line_echo_of("again", "player_4", EARLIER) == ""

    monkeypatch.setattr(echo_gate, "get_llm_judge", judge_saying("nothing", ""))
    assert echo_gate.line_echo_of("again", "player_4", EARLIER) == ""


def test_keeps_a_line_whose_named_repeat_never_spoke(monkeypatch):
    # player_3 only passed and the moderator is not a player: neither can be echoed.
    monkeypatch.setattr(echo_gate, "get_llm_judge", judge_saying("nothing", "player_3"))
    assert echo_gate.line_echo_of("again", "player_4", EARLIER) == ""

    monkeypatch.setattr(echo_gate, "get_llm_judge", judge_saying("nothing", "game_master"))
    assert echo_gate.line_echo_of("again", "player_4", EARLIER) == ""


def test_the_judge_sees_only_spoken_lines_and_is_not_called_before_anyone_spoke(monkeypatch):
    seen: list[str] = []
    monkeypatch.setattr(echo_gate, "get_llm_judge", judge_saying("nothing", "player_2", seen))

    assert echo_gate.line_echo_of("first words", "player_4", [voluntary_pass(0, "player_3")]) == ""
    assert seen == []

    echo_gate.line_echo_of("player_5's claim came late.", "player_4", EARLIER)
    assert len(seen) == 1
    assert "1. player_2: player_5 claimed healer" in seen[0]
    assert "A moderator line." not in seen[0]
    assert "player_3" not in seen[0]


# --- line_echo_of: fail open --------------------------------------------------------------

def test_fails_open_when_the_call_raises(monkeypatch):
    monkeypatch.setattr(echo_gate, "get_llm_judge", judge_raising(ConnectionError("provider down")))

    assert echo_gate.line_echo_of("anything", "player_4", EARLIER) == ""


def test_fails_open_when_the_answer_cannot_be_parsed(monkeypatch):
    monkeypatch.setattr(echo_gate, "get_llm_judge",
                        judge_raising(OutputParserException("not the schema")))

    assert echo_gate.line_echo_of("anything", "player_4", EARLIER) == ""


# --- resolve_decision: where the gate is called -------------------------------------------

NO_REASONING = {"strategy": None, "strategy_verdicts": [], "memory_verdicts": [], "reads": []}


def decision(message: str, targets=None, pass_turn: bool = False) -> SimpleNamespace:
    if targets is None:
        targets = []
    return SimpleNamespace(pass_turn=pass_turn, message=message, addressed_targets=targets)


def payload(firing: FiringReason, day_channel: list[DayChannel], human: bool = False,
            day_round: str = "proactive") -> dict:
    return {"player_id": "player_4", "current_day": 2, "firing_reason": firing,
            "day_channel": day_channel, "day_round": day_round, "human_player": human}


SWEEP = FiringReason(tier="proactive", sweep=1)


def gate_returning(answer: str, calls: list):
    def fake(message, player, earlier):
        calls.append((message, player, len(earlier)))
        return answer

    return fake


def test_a_held_sweep_line_becomes_a_novelty_gated_marker_with_its_text_and_tags(monkeypatch):
    calls: list = []
    monkeypatch.setattr(resolve, "line_echo_of", gate_returning("player_2", calls))
    tags = [accusation("player_5")]

    turn = resolve.resolve_decision(decision("player_5 claimed late.", tags), NO_REASONING,
                                    "day_channel", payload(SWEEP, EARLIER), [])

    entry = turn.entry
    assert len(calls) == 1
    assert entry.passed is True
    assert entry.pass_reason == DiscussionPassReason.NOVELTY_GATED
    assert entry.gated is True
    assert entry.message == ""
    assert entry.gated_candidate == "player_5 claimed late."
    assert entry.addressed_targets == tags
    assert entry.firing_reason == SWEEP
    assert entry.day_round == "proactive"
    assert entry.seq == 3  # today's entries before it: three


def test_a_kept_sweep_line_is_published(monkeypatch):
    calls: list = []
    monkeypatch.setattr(resolve, "line_echo_of", gate_returning("", calls))

    turn = resolve.resolve_decision(decision("A new point."), NO_REASONING, "day_channel",
                                    payload(SWEEP, EARLIER), [])

    assert len(calls) == 1
    assert turn.entry.passed is False
    assert turn.entry.message == "A new point."


def test_a_reactive_answer_is_never_gated(monkeypatch):
    calls: list = []
    monkeypatch.setattr(resolve, "line_echo_of", gate_returning("player_2", calls))
    reactive = FiringReason(tier="reactive", owes=["player_2"])

    turn = resolve.resolve_decision(decision("player_5 claimed late."), NO_REASONING,
                                    "day_channel", payload(reactive, EARLIER, day_round="discussion"), [])

    assert calls == []
    assert turn.entry.passed is False
    assert turn.entry.message == "player_5 claimed late."


def test_a_human_sweep_line_is_never_gated(monkeypatch):
    calls: list = []
    monkeypatch.setattr(resolve, "line_echo_of", gate_returning("player_2", calls))

    turn = resolve.resolve_decision(decision("player_5 claimed late."), NO_REASONING,
                                    "day_channel", payload(SWEEP, EARLIER, human=True), [])

    assert calls == []
    assert turn.entry.passed is False


def test_answering_a_player_who_named_me_is_never_gated(monkeypatch):
    calls: list = []
    monkeypatch.setattr(resolve, "line_echo_of", gate_returning("player_2", calls))
    earlier = [spoken(0, "player_2", "player_4 led the lynch on the healer.",
                      [AddressedTarget(target="player_4", addressed_form="mention", stance="neutral")])]
    answer = [AddressedTarget(target="player_2", addressed_form="response", stance="defense")]

    turn = resolve.resolve_decision(decision("I did not lead it, I voted last.", answer), NO_REASONING,
                                    "day_channel", payload(SWEEP, earlier), [])

    assert calls == []
    assert turn.entry.passed is False
    assert turn.entry.message == "I did not lead it, I voted last."


def test_answering_a_player_who_did_not_name_me_goes_to_the_gate(monkeypatch):
    calls: list = []
    monkeypatch.setattr(resolve, "line_echo_of", gate_returning("player_2", calls))
    earlier = [spoken(0, "player_2", "player_5 led the lynch on the healer.", [accusation("player_5")])]
    reply = [AddressedTarget(target="player_2", addressed_form="response", stance="agreement")]

    turn = resolve.resolve_decision(decision("Yes, player_5 led it.", reply), NO_REASONING,
                                    "day_channel", payload(SWEEP, earlier), [])

    assert len(calls) == 1
    assert turn.entry.pass_reason == DiscussionPassReason.NOVELTY_GATED


def test_an_empty_sweep_line_is_recorded_as_a_voluntary_pass(monkeypatch):
    calls: list = []
    monkeypatch.setattr(resolve, "line_echo_of", gate_returning("player_2", calls))

    for empty in ["", "   ", "null"]:
        turn = resolve.resolve_decision(decision(empty), NO_REASONING, "day_channel",
                                        payload(SWEEP, EARLIER), [])
        assert turn.entry is not None
        assert turn.entry.passed is True
        assert turn.entry.pass_reason == DiscussionPassReason.VOLUNTARY
        assert turn.entry.gated is False
        assert turn.entry.firing_reason == SWEEP
    assert calls == []


def test_an_empty_reactive_line_records_nothing(monkeypatch):
    reactive = FiringReason(tier="reactive", owes=["player_2"])

    turn = resolve.resolve_decision(decision(""), NO_REASONING, "day_channel",
                                    payload(reactive, EARLIER, day_round="discussion"), [])

    assert turn.entry is None


# --- the held marker in the reactive queue -------------------------------------------------

def test_the_reactive_queue_skips_a_held_line():
    held = DayChannel(day=2, seq=1, player="player_4", message="", passed=True,
                      pass_reason=DiscussionPassReason.NOVELTY_GATED, gated=True,
                      gated_candidate="player_5 is the wolf.",
                      addressed_targets=[accusation("player_5")], firing_reason=SWEEP)
    spoken_accusation = spoken(2, "player_3", "player_6 is the wolf.", [accusation("player_6")])

    queue = build_reactive_queue([held, spoken_accusation], per_pair_cap=2, reengagement_cooldown=99)

    debtors = []
    for item in queue:
        debtors.append(item.agent_id)
    # Nobody heard player_4's line, so player_5 owes no answer; player_6 does.
    assert debtors == ["player_6"]

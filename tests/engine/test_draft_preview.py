"""The day-speech draft is a preview of the seat's own agent's turn, and the AI turn's prompt
is untouched by it.

- The golden pins, byte for byte, what every role's AI discuss turn sends the model (a
  prompt change is a research epoch bump; see tests/fixtures/day_discuss_prompt_golden.py).
- With no direction the preview sends exactly that prompt; with one it adds one message
  after it and nothing else; either way nothing is committed or recorded.
"""

from __future__ import annotations

import copy
import json

import pytest

from Agents.nodes.day.actors import preview_discuss
from Agents.schemas import DayDiscussOutput
from Agents.turn import agent_player, pipeline
from Agents.turn.drafting_agent import player_direction
from tests.fixtures.day_discuss_prompt_golden import (
    GOLDEN,
    ROLES,
    capturing_llm,
    render,
    runtime,
    speaker_payload,
)


def _human_payload(role: str) -> dict:
    """The same turn, held by a human seat (what the draft previews)."""
    return {**speaker_payload(role), "human_player": True}


def test_ai_discuss_prompt_is_byte_identical_to_the_golden(monkeypatch):
    assert render(monkeypatch) == json.loads(GOLDEN.read_text())


@pytest.mark.parametrize("role", ROLES)
def test_preview_without_direction_sends_the_real_turns_prompt(monkeypatch, role):
    sent: list = []
    monkeypatch.setattr(agent_player, "get_llm", lambda: capturing_llm(sent))
    line = preview_discuss(_human_payload(role), {"configurable": {}}, runtime())
    assert line == "player_2, answer the question."
    assert [list(m) for m in sent[0]] == json.loads(GOLDEN.read_text())[role]


def test_preview_with_direction_adds_one_message_and_nothing_else(monkeypatch):
    sent: list = []
    monkeypatch.setattr(agent_player, "get_llm", lambda: capturing_llm(sent))
    direction = player_direction("push on player_2 {softly}", "player_2 is odd",
                                 {"player_5": "quiet"}, "player_2")
    preview_discuss(_human_payload("villager"), {"configurable": {}}, runtime(), direction)
    golden = json.loads(GOLDEN.read_text())["villager"]
    assert [list(m) for m in sent[0]] == golden + [["human", direction]]


def test_preview_commits_and_records_nothing(monkeypatch):
    """No state write (the payload is untouched and only a line comes back), no eval case,
    no strategy-adoption write-back to the memory store."""
    sent: list = []
    monkeypatch.setattr(agent_player, "get_llm", lambda: capturing_llm(sent))

    def no_adoption(*a, **k):
        raise AssertionError("the preview must not write strategy adoption back")

    monkeypatch.setattr(pipeline, "process_strategy_adoption", no_adoption)
    payload = _human_payload("wolf")
    before = copy.deepcopy(payload)
    rt = runtime()
    line = preview_discuss(payload, {"configurable": {}}, rt, "be brief")
    assert isinstance(line, str) and line
    assert payload == before
    assert rt.context["eval_sink"].records == []


def test_preview_reports_a_pass_as_empty_and_a_failure_as_an_error(monkeypatch):
    passing = DayDiscussOutput(message="", pass_turn=True, updated_strategy="note",
                               addressed_targets=[], strategy_verdicts=[],
                               memory_applicability=[], reads=[])
    monkeypatch.setattr(agent_player, "get_llm", lambda: _answering(passing))
    payload = {**_human_payload("villager"), "firing_reason": None}  # proactive-free turn
    assert preview_discuss(payload, {"configurable": {}}, runtime()) == ""

    monkeypatch.setattr(agent_player, "get_llm", lambda: _answering(None))
    monkeypatch.setattr(agent_player, "get_llm_game_fallback", lambda: None)
    with pytest.raises(RuntimeError):
        preview_discuss(_human_payload("villager"), {"configurable": {}}, runtime())


def _answering(reply):
    from types import SimpleNamespace

    from langchain_core.runnables import RunnableLambda

    def answer(_prompt):
        if reply is None:
            raise ConnectionError("provider down")
        return reply

    return SimpleNamespace(with_structured_output=lambda _schema: RunnableLambda(answer))


def test_direction_block_wording():
    assert player_direction("") == ""
    assert player_direction("", current="a line") == ""  # a draft alone asks nothing
    assert player_direction("  ", seat_notes={"player_4": "  "}) == ""

    assert player_direction("push on player_5") == (
        "The human playing your seat gives you this direction for your message: "
        "push on player_5\n"
        "Build your message around their direction; everything above still applies. "
        "Speak this turn (pass_turn=false).")
    assert player_direction("softer", current="player_5 is a wolf.") == (
        "The human playing your seat gives you this direction for your message: softer\n"
        "Their current draft of it: player_5 is a wolf.\n"
        "Revise the draft as they ask; everything above still applies. "
        "Speak this turn (pass_turn=false).")
    assert player_direction("", seat_notes={"player_5": "jumped on\n3's slip",
                                            "player_8": "quiet"}, suspect="player_5") == (
        "The human playing your seat keeps these notes on the table: "
        "player_5: jumped on 3's slip; player_8: quiet\n"
        "They suspect player_5.\n"
        "Weigh their notes as their reads, not as facts; everything above still applies. "
        "Speak this turn (pass_turn=false).")
    with_notes = player_direction("ask player_4", seat_notes={"player_4": "dodgy"})
    assert "\nTheir notes on the table: player_4: dodgy\n" in with_notes

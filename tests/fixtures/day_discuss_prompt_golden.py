"""Exact golden for the prompt an AI seat is sent on its day-discussion turn, every role.

A prompt change is a research epoch bump, so the text an AI-only game sends must not move
by a byte unless someone means it to. This renders each role's discuss turn through the
real node (``Agents.nodes.day.actors.discuss``), from a payload built by the real Send
builder over a fixed mid-game board, with the model faked to capture what it was sent.
``day_discuss_prompt_golden.json`` holds the result; the test compares field for field.

Regenerate on purpose only, after a deliberate prompt change::

    poetry run python -m tests.fixtures.day_discuss_prompt_golden
"""

from __future__ import annotations

import json
import pathlib
from types import SimpleNamespace

from langchain_core.runnables import RunnableLambda

from Agents.schemas import DayDiscussOutput
from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DeathRecord,
    FiringReason,
    InvestigatorResult,
    WolfChannel,
)

HERE = pathlib.Path(__file__).resolve().parent
GOLDEN = HERE / "day_discuss_prompt_golden.json"

ROLES = ["villager", "healer", "investigator", "wolf", "serial_killer", "vigilante"]


def board() -> dict:
    """A day-3 board with something in every block the discuss prompt shows: a dead roster,
    a previous day's summary, today's talk, the pack's night talk, private results."""
    roles = {"player_1": "villager", "player_2": "wolf", "player_3": "investigator",
             "player_4": "healer", "player_5": "serial_killer", "player_6": "vigilante",
             "player_7": "wolf", "player_8": "villager", "player_9": "villager"}
    return {
        "roles": roles,
        "human_players": [],
        "current_day": 3,
        "current_round": 0,
        "surviving_wolves": ["player_2", "player_7"],
        "surviving_villagers": ["player_1", "player_3", "player_4", "player_5", "player_6"],
        "dead_roster": [
            DeathRecord(player="player_8", role="villager", day=1, phase="night"),
            DeathRecord(player="player_9", role="villager", day=2, phase="day"),
        ],
        "day_summaries": [DaySummary(day=2, summary="player_9 was lynched on a 4-3 vote.")],
        "day_channel": [
            DayChannel(day=2, seq=0, player="player_1", message="Yesterday's line."),
            DayChannel(day=3, seq=0, player="game_master", message="player_8 was found dead."),
            DayChannel(day=3, seq=1, player="player_4", message="player_2, why abstain?"),
            DayChannel(day=3, seq=2, player="player_6", message="", passed=True),
        ],
        "wolf_channel": [WolfChannel(day=2, round=1, wolf="player_7", message="Go for 8.",
                                     vote="")],
        "investigator_results": [InvestigatorResult(day=2, player_investigated="player_5",
                                                    role_revealed="serial_killer")],
        "vigilante_results": ["Night 2: you held fire."],
        "vigilante_bullets": 2,
        "agent_strategies": {pid: f"{pid}'s note: watch player_2." for pid in roles},
        "no_lynch_streak": 0,
        "day_votes": [],
    }


def speaker_payload(role: str) -> dict:
    """The discuss payload the real Send builder makes for the seat holding ``role``: a
    reactive turn, owed to player_4, on a voting day."""
    from Agents.nodes.day.flow import build_speaker_send

    state = board()
    seat = next(p for p, r in state["roles"].items() if r == role)
    send = build_speaker_send(
        state, seat, role, FiringReason(tier="reactive", owes=["player_4"]))
    return send.arg


def capturing_llm(sent: list) -> SimpleNamespace:
    """A stand-in for get_llm(): records every prompt it is sent and answers with a line."""
    reply = DayDiscussOutput(message="player_2, answer the question.", pass_turn=False,
                             updated_strategy="", addressed_targets=[], strategy_verdicts=[],
                             memory_applicability=[], reads=[])

    def answer(prompt_value):
        sent.append([(m.type, m.content) for m in prompt_value.to_messages()])
        return reply

    return SimpleNamespace(with_structured_output=lambda _schema: RunnableLambda(answer))


def runtime() -> SimpleNamespace:
    """What a turn's runtime carries, with no memory store (so retrieval skips)."""
    from Agents.observability import EvalCaseSink
    from Agents.tracing import Metrics

    return SimpleNamespace(context={"metrics": Metrics(), "eval_sink": EvalCaseSink()},
                           store=None)


def render(monkeypatch) -> dict[str, list[list[str]]]:
    """Every role's discuss prompt, as the AI path sends it: {role: [[type, content], ...]}."""
    from Agents.nodes.day.actors import discuss
    from Agents.turn import agent_player

    rendered = {}
    for role in ROLES:
        sent: list = []
        monkeypatch.setattr(agent_player, "get_llm", lambda sent=sent: capturing_llm(sent))
        discuss(speaker_payload(role), {"configurable": {}}, runtime())
        assert len(sent) == 1, role
        rendered[role] = [list(m) for m in sent[0]]
    return rendered


if __name__ == "__main__":
    import pytest

    with pytest.MonkeyPatch.context() as mp:
        GOLDEN.write_text(json.dumps(render(mp), indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {GOLDEN}")

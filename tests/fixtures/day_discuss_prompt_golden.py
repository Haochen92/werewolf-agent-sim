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

from Agents.rules.night import pack_carrier, resolve_night
from Agents.rules.night_record import night_action_records
from Agents.schemas import day_discuss_output
from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DeathRecord,
    FiringReason,
    WolfChannel,
)
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import lineup

HERE = pathlib.Path(__file__).resolve().parent
GOLDEN = HERE / "day_discuss_prompt_golden.json"

ROLES = lineup("serial_killer", "speculator")

SEATS = {"player_1": "sentinel", "player_2": "chanteuse", "player_3": "investigator",
         "player_4": "healer", "player_5": "serial_killer", "player_6": "vigilante",
         "player_7": "illusionist", "player_8": "trailseer", "player_9": "sigilist",
         "player_10": "speculator"}


def _seat(role: str) -> str:
    return next(p for p, r in SEATS.items() if r == role)


def board(speaker_role: str) -> dict:
    """A day-3 board with something in every block the discuss prompt shows: a dead roster,
    a previous day's summary, today's talk, the pack's night talk, private night records.

    Two players are dead, a night-1 kill and a day-2 lynch, taken from the trailseer, the
    sigilist and the sentinel so that the speaker is never one of them."""
    dead = [_seat(r) for r in ("trailseer", "sigilist", "sentinel") if r != speaker_role][:2]
    killed, lynched = dead
    alive = [p for p in SEATS if p not in dead]
    wolves = ["player_2", "player_7"]
    healer, sentinel, investigator = "player_4", "player_1", "player_3"
    watcher = [sentinel] if sentinel in alive else []

    # Night 1: the pack kills, the serial killer's attack on a protected player is saved, the
    # chanteuse's block on the neutral does nothing, the vigilante holds fire, a check.
    # Night 2: the pack's attack saved, a check, a watch.
    night_1 = [
        NightChoice(pack_carrier(wolves, 1), "chanteuse", "kill", killed),
        NightChoice("player_5", "serial_killer", "kill", "player_6"),
        NightChoice(healer, "healer", "protect", "player_6"),
        NightChoice("player_2", "chanteuse", "block", "player_10"),  # the neutral: no effect
        NightChoice("player_6", "vigilante", "hold_fire", None),
        NightChoice(investigator, "investigator", "investigate", "player_7"),
    ]
    night_2 = [
        NightChoice(pack_carrier(wolves, 2), "illusionist", "kill", investigator),
        NightChoice(healer, "healer", "protect", investigator),
        NightChoice(investigator, "investigator", "investigate", "player_5"),
        *[NightChoice(s, "sentinel", "watch", investigator) for s in watcher],
    ]
    records = []
    for night, choices in ((1, night_1), (2, night_2)):
        outcome = resolve_night(choices, SEATS, night)
        records += [r for r in night_action_records(choices, outcome, SEATS) if r.actor not in outcome.deaths]

    return {
        "roles": dict(SEATS),
        "lineup": list(ROLES),
        "human_players": [],
        "current_day": 3,
        "current_round": 0,
        "surviving_wolves": wolves,
        "surviving_villagers": [p for p in alive if p not in wolves],
        "dead_roster": [
            DeathRecord(player=killed, role=SEATS[killed], day=1, phase="night"),
            DeathRecord(player=lynched, role=SEATS[lynched], day=2, phase="day"),
        ],
        "day_summaries": [DaySummary(day=2, summary=f"{lynched} was lynched on a 4-3 vote.")],
        "day_channel": [
            DayChannel(day=2, seq=0, player="player_3", message="Yesterday's line."),
            DayChannel(day=3, seq=0, player="game_master", message="Night of day 2: player_3 was attacked by the wolves but was saved by the healer!"),
            DayChannel(day=3, seq=1, player="player_4", message="player_2, why abstain?"),
            DayChannel(day=3, seq=2, player="player_6", message="", passed=True),
        ],
        "wolf_channel": [WolfChannel(day=2, round=1, wolf="player_7", message="Go for 3.", vote=""),
                         WolfChannel(day=2, round=4, wolf="player_7", message="", vote="player_3")],
        "night_actions": records,
        "uses_left": {"vigilante": 2, "sigilist": 2, "illusionist": 2, "speculator": 1},
        "speculator_pick": None,
        "agent_strategies": {pid: f"{pid}'s note: watch player_2." for pid in SEATS},
        "no_lynch_streak": 0,
        "day_votes": [],
    }


def speaker_payload(role: str) -> dict:
    """The discuss payload the real Send builder makes for the seat holding ``role``: a
    reactive turn, owed to player_4, on a voting day."""
    from Agents.nodes.day.flow import build_speaker_send

    state = board(role)
    seat = _seat(role)
    send = build_speaker_send(
        state, seat, role, FiringReason(tier="reactive", owes=["player_4"]))
    return send.arg


def capturing_llm(sent: list) -> SimpleNamespace:
    """A stand-in for get_llm(): records every prompt it is sent and answers with a line."""
    reply = day_discuss_output(ROLES)(
        message="player_2, answer the question.", pass_turn=False, claim="none",
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

"""The scripted model as a fixture: every model call of a game answered offline.

`scripted_model` returns a function. Called with a seed (and, optionally, the seats no scripted
player may choose), it makes every seat's model a `ScriptedModel` on `random.Random(seed)`, and
replaces the four helper calls a game makes outside the seats' turns: the rescue model (none),
the day summary (a fixed string), the opening filter (keeps every line) and the echo check
(finds no echo). Everything is set with `monkeypatch`, so it is undone when the test ends.
"""

from __future__ import annotations

import random

import pytest

from Agents.nodes.day import flow
from Agents.turn import agent_player, resolve
from tests.factories.scripted_model import ScriptedModel


@pytest.fixture
def scripted_model(monkeypatch):
    def install(seed: int, spare: frozenset[str] = frozenset()) -> None:
        rng = random.Random(seed)
        monkeypatch.setattr(agent_player, "get_llm", lambda: ScriptedModel(rng, spare))
        monkeypatch.setattr(agent_player, "get_llm_game_fallback", lambda: None)
        monkeypatch.setattr(flow, "run_day_summary_agent",
                            lambda day, messages, max_retries=1, **kw: ("summary", "fake", {}))
        monkeypatch.setattr(flow, "filter_openings", lambda entries: entries)
        monkeypatch.setattr(resolve, "line_echo_of", lambda message, player, earlier: "")

    return install

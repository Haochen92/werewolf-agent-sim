"""The scripted model as a fixture: every model call of a game answered offline.

`scripted_model` returns a function. Called with a seed (and, optionally, the seats no scripted
player may choose), it returns a `ScriptedModels` on `random.Random(seed)`: every seat's model is a
`ScriptedModel` on that one generator, and there is no rescue model. The test passes it to the game
in the graph context (`context={"metrics": ..., "models": models}`).

The function also replaces three helper calls a game makes outside the seats' turns, with
`monkeypatch`, so they are undone when the test ends: the day summary (a fixed string), the opening
filter (keeps every line) and the echo check (finds no echo). These stay replacements of whole
functions, not fake models: a scripted model would answer them with random verdicts, which would
hold random lines and change every game the tests play.
"""

from __future__ import annotations

import random

import pytest

from Agents.nodes.day import flow
from Agents.turn import resolve
from tests.factories.scripted_model import ScriptedModels


@pytest.fixture
def scripted_model(monkeypatch):
    def install(seed: int, spare: frozenset[str] = frozenset()) -> ScriptedModels:
        monkeypatch.setattr(flow, "run_day_summary_agent",
                            lambda day, messages, max_retries=1, **kw: ("summary", "fake", {}))
        monkeypatch.setattr(flow, "filter_openings", lambda entries, models=None: entries)
        monkeypatch.setattr(resolve, "line_echo_of", lambda message, player, earlier, models=None: "")
        return ScriptedModels(random.Random(seed), spare)

    return install

"""The game graph with its own checkpoint store, one per test.

Production compiles the game graph once, at import (`Agents/graphs/parent.py`), with one
in-memory checkpoint store for the whole process, keyed by game id. A test that played a game
id another test had already played would resume on top of that game's final state. This
fixture compiles the same graph, `parent_graph`, with a new in-memory checkpoint store for each
test (the same serializer as production's) and production's lesson store, so no test sees
another test's games.
"""

from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import MemorySaver

from Agents.graphs.parent import parent_graph
from Agents.memory import store
from Agents.memory.checkpointer import durable_serde


@pytest.fixture
def game_graph():
    return parent_graph.compile(store=store, checkpointer=MemorySaver(serde=durable_serde()))

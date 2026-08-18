"""agent_strategies must MERGE per-player across the child->parent fold, not overwrite.

The single-actor night phases (healer/investigator/serial_killer/vigilante) fold their result
back into the orchestrator as a single-key delta -- {that_player: updated_strategy} (see
Agents/graphs/parent.py). The day/wolf phases return the full map, so they were immune, but a
single-key return against an overwrite channel wiped every other seat's note. That silently broke
`previous_strategy` continuity for every seat except the first night actor, blanked nearly all
seats on day 2+, and corrupted the end-of-game map that memory extraction reads on night-ending
games. The channel now reduces with merge_strategies (matching the day/wolf subgraph states), so a
single-key fold updates only that seat. These tests pin that.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from Agents.state import OrchestratorGraph


def _compile(node):
    g = StateGraph(OrchestratorGraph)
    g.add_node("N", node)
    g.add_edge(START, "N")
    g.add_edge("N", END)
    return g.compile()


def test_single_key_fold_preserves_other_seats():
    """A single-actor phase folding back {seat: note} must not drop the other seats."""
    graph = _compile(lambda state: {"agent_strategies": {"vigilante": "SHOT p3"}})
    out = graph.invoke(
        {"agent_strategies": {"p1": "a", "p2": "b", "vigilante": "old"}}
    )
    assert out["agent_strategies"] == {"p1": "a", "p2": "b", "vigilante": "SHOT p3"}


def test_sequential_single_actor_folds_accumulate():
    """Healer -> SK -> vigilante folding one key each keeps all three plus the untouched seats."""
    def healer(state):
        return {"agent_strategies": {"healer": "protect p1"}}

    def sk(state):
        return {"agent_strategies": {"sk": "stalk p2"}}

    def vig(state):
        return {"agent_strategies": {"vig": "hold fire"}}

    g = StateGraph(OrchestratorGraph)
    for name, fn in (("HEALER", healer), ("SK", sk), ("VIG", vig)):
        g.add_node(name, fn)
    g.add_edge(START, "HEALER")
    g.add_edge("HEALER", "SK")
    g.add_edge("SK", "VIG")
    g.add_edge("VIG", END)
    out = g.compile().invoke({"agent_strategies": {"p1": "day-note", "wolf1": "night-note"}})

    assert out["agent_strategies"] == {
        "p1": "day-note",
        "wolf1": "night-note",
        "healer": "protect p1",
        "sk": "stalk p2",
        "vig": "hold fire",
    }

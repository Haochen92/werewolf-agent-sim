"""Wolf-night subgraph: the sequential-talk -> parallel-vote loop (the only multi-agent night).

START -> PREPARE_WOLF_NIGHT -(wolf_fan_out: ONE wolf per pass during the talk rounds, every wolf
in parallel on the vote round)-> WOLF_NIGHT_DISCUSS | WOLF_NIGHT_VOTE ->
COLLECT_WOLF_NIGHT_DISCUSSION -(check_night_end: loop back to PREPARE_WOLF_NIGHT until a kill
target is set, else END). Node bodies live in Agents.nodes (night/wolf.py).
"""

from langgraph.graph import START, StateGraph

from Agents.nodes import wolf_night_discuss, wolf_night_vote
from Agents.memory import store
from Agents.nodes import (
    check_night_end,
    collect_wolf_night_discussion,
    prepare_wolf_night,
    wolf_fan_out,
)
from Agents.state import WolfNightGraph
from Agents.tracing import GraphContext


def build_wolf_night_graph():
    wolf_night_graph = StateGraph(WolfNightGraph, context_schema=GraphContext)

    wolf_night_graph.add_node("PREPARE_WOLF_NIGHT", prepare_wolf_night)
    wolf_night_graph.add_node("WOLF_NIGHT_DISCUSS", wolf_night_discuss)
    wolf_night_graph.add_node("WOLF_NIGHT_VOTE", wolf_night_vote)
    wolf_night_graph.add_node(
        "COLLECT_WOLF_NIGHT_DISCUSSION", collect_wolf_night_discussion
    )

    wolf_night_graph.add_edge(START, "PREPARE_WOLF_NIGHT")
    wolf_night_graph.add_conditional_edges(
        "PREPARE_WOLF_NIGHT", wolf_fan_out, ["WOLF_NIGHT_DISCUSS", "WOLF_NIGHT_VOTE"]
    )
    wolf_night_graph.add_edge("WOLF_NIGHT_DISCUSS", "COLLECT_WOLF_NIGHT_DISCUSSION")
    wolf_night_graph.add_edge("WOLF_NIGHT_VOTE", "COLLECT_WOLF_NIGHT_DISCUSSION")
    wolf_night_graph.add_conditional_edges(
        "COLLECT_WOLF_NIGHT_DISCUSSION", check_night_end
    )

    return wolf_night_graph


wolf_night_graph = build_wolf_night_graph()
wolf_night_graph_compiled = wolf_night_graph.compile(store=store)

from langgraph.graph import START, StateGraph

from Agents.agents import wolf_night_discuss
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
    wolf_night_graph.add_node(
        "COLLECT_WOLF_NIGHT_DISCUSSION", collect_wolf_night_discussion
    )

    wolf_night_graph.add_edge(START, "PREPARE_WOLF_NIGHT")
    wolf_night_graph.add_conditional_edges(
        "PREPARE_WOLF_NIGHT", wolf_fan_out, ["WOLF_NIGHT_DISCUSS"]
    )
    wolf_night_graph.add_edge("WOLF_NIGHT_DISCUSS", "COLLECT_WOLF_NIGHT_DISCUSSION")
    wolf_night_graph.add_conditional_edges(
        "COLLECT_WOLF_NIGHT_DISCUSSION", check_night_end
    )

    return wolf_night_graph


wolf_night_graph = build_wolf_night_graph()
wolf_night_graph_compiled = wolf_night_graph.compile(store=store)

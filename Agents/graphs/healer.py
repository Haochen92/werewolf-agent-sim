from langgraph.graph import END, START, StateGraph

from Agents.agents import healer_act
from Agents.memory import store
from Agents.state import HealerNightGraph
from Agents.tracing import GraphContext


def build_healer_graph():
    healer_graph = StateGraph(HealerNightGraph, context_schema=GraphContext)
    healer_graph.add_node("healer_act", healer_act)
    healer_graph.add_edge(START, "healer_act")
    healer_graph.add_edge("healer_act", END)
    return healer_graph


healer_graph = build_healer_graph()
healer_graph_compiled = healer_graph.compile(store=store)

from langgraph.graph import END, START, StateGraph

from Agents.agents import vigilante_act
from Agents.memory import store
from Agents.graphs.state import VigilanteNightGraph
from Agents.tracing import GraphContext


def build_vigilante_graph():
    vigilante_graph = StateGraph(VigilanteNightGraph, context_schema=GraphContext)
    vigilante_graph.add_node("vigilante_act", vigilante_act)
    vigilante_graph.add_edge(START, "vigilante_act")
    vigilante_graph.add_edge("vigilante_act", END)
    return vigilante_graph


vigilante_graph = build_vigilante_graph()
vigilante_graph_compiled = vigilante_graph.compile(store=store)

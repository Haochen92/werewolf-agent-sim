"""Investigator night subgraph: a one-node graph (START -> investigator_act -> END).

Single-actor night role (see graphs/night/healer.py); the act node lives in
Agents.nodes.night.investigator.
"""

from langgraph.graph import END, START, StateGraph

from Agents.nodes import investigator_act
from Agents.memory import store
from Agents.state import InvestigatorNightGraph
from Agents.tracing import GraphContext


def build_investigator_graph():
    investigator_graph = StateGraph(InvestigatorNightGraph, context_schema=GraphContext)
    investigator_graph.add_node("investigator_act", investigator_act)
    investigator_graph.add_edge(START, "investigator_act")
    investigator_graph.add_edge("investigator_act", END)
    return investigator_graph


investigator_graph = build_investigator_graph()
investigator_graph_compiled = investigator_graph.compile(store=store)

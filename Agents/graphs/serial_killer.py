from langgraph.graph import END, START, StateGraph

from Agents.nodes import serial_killer_act
from Agents.memory import store
from Agents.state import SerialKillerNightGraph
from Agents.tracing import GraphContext


def build_serial_killer_graph():
    serial_killer_graph = StateGraph(SerialKillerNightGraph, context_schema=GraphContext)
    serial_killer_graph.add_node("serial_killer_act", serial_killer_act)
    serial_killer_graph.add_edge(START, "serial_killer_act")
    serial_killer_graph.add_edge("serial_killer_act", END)
    return serial_killer_graph


serial_killer_graph = build_serial_killer_graph()
serial_killer_graph_compiled = serial_killer_graph.compile(store=store)

from langgraph.graph import END, START, StateGraph

from Agents.memory import store
from Agents.agents import (
    healer_discuss,
    healer_vote,
    investigator_discuss,
    investigator_vote,
    serial_killer_discuss,
    serial_killer_vote,
    vigilante_discuss,
    vigilante_vote,
    villager_discuss,
    villager_vote,
    wolf_discuss,
    wolf_vote,
)
from Agents.graphs.nodes import (
    collect_votes,
    fan_out_vote,
    day_scheduler,
    route_after_day_summary,
    start_voting,
    summarize_day_discussion,
    route_speaker
)
from Agents.graphs.state import DayGraphState
from Agents.tracing import GraphContext


def build_day_graph():
    day_graph = StateGraph(DayGraphState, context_schema=GraphContext)

    day_graph.add_node("SCHEDULE", day_scheduler)
    day_graph.add_node("SUMMARIZE_DAY_DISCUSSION", summarize_day_discussion)
    day_graph.add_node("START_VOTING", start_voting)
    day_graph.add_node("COLLECT_VOTES", collect_votes)

    day_graph.add_node("villager_discuss", villager_discuss)
    day_graph.add_node("healer_discuss", healer_discuss)
    day_graph.add_node("wolf_discuss", wolf_discuss)
    day_graph.add_node("investigator_discuss", investigator_discuss)
    day_graph.add_node("serial_killer_discuss", serial_killer_discuss)
    day_graph.add_node("vigilante_discuss", vigilante_discuss)

    day_graph.add_node("villager_vote", villager_vote)
    day_graph.add_node("healer_vote", healer_vote)
    day_graph.add_node("wolf_vote", wolf_vote)
    day_graph.add_node("investigator_vote", investigator_vote)
    day_graph.add_node("serial_killer_vote", serial_killer_vote)
    day_graph.add_node("vigilante_vote", vigilante_vote)

    discuss_nodes = [
        "villager_discuss",
        "healer_discuss",
        "wolf_discuss",
        "investigator_discuss",
        "serial_killer_discuss",
        "vigilante_discuss",
    ]
    vote_nodes = [
        "villager_vote",
        "healer_vote",
        "wolf_vote",
        "investigator_vote",
        "serial_killer_vote",
        "vigilante_vote",
    ]

    day_graph.add_edge(START, "SCHEDULE")
    day_graph.add_conditional_edges(
        "SCHEDULE",
        route_speaker,
        discuss_nodes + ["SUMMARIZE_DAY_DISCUSSION"],
    )
    # Self-loops to route back to scheduler after each speech
    for node in discuss_nodes:
        day_graph.add_edge(node, "SCHEDULE")

    day_graph.add_conditional_edges("SUMMARIZE_DAY_DISCUSSION", route_after_day_summary)
    day_graph.add_conditional_edges("START_VOTING", fan_out_vote, vote_nodes)
    for node in vote_nodes:
        day_graph.add_edge(node, "COLLECT_VOTES")
    day_graph.add_edge("COLLECT_VOTES", END)

    return day_graph


day_graph = build_day_graph()
day_graph_compiled = day_graph.compile(store=store)

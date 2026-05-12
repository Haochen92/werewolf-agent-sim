from langgraph.graph import END, START, StateGraph

from Agents.memory import store
from Agents.agents import (
    healer_discuss,
    healer_vote,
    investigator_discuss,
    investigator_vote,
    villager_discuss,
    villager_vote,
    wolf_discuss,
    wolf_vote,
)
from Agents.nodes import (
    check_round,
    collect_discussion,
    collect_votes,
    fan_out_discuss,
    fan_out_vote,
    prepare_round,
    route_after_day_summary,
    start_voting,
    summarize_day_discussion,
)
from Agents.state import DayGraphState
from Agents.tracing import GraphContext


def build_day_graph():
    day_graph = StateGraph(DayGraphState, context_schema=GraphContext)

    day_graph.add_node("PREPARE_ROUND", prepare_round)
    day_graph.add_node("COLLECT_DISCUSSION", collect_discussion)
    day_graph.add_node("SUMMARIZE_DAY_DISCUSSION", summarize_day_discussion)
    day_graph.add_node("START_VOTING", start_voting)
    day_graph.add_node("COLLECT_VOTES", collect_votes)

    day_graph.add_node("villager_discuss", villager_discuss)
    day_graph.add_node("healer_discuss", healer_discuss)
    day_graph.add_node("wolf_discuss", wolf_discuss)
    day_graph.add_node("investigator_discuss", investigator_discuss)

    day_graph.add_node("villager_vote", villager_vote)
    day_graph.add_node("healer_vote", healer_vote)
    day_graph.add_node("wolf_vote", wolf_vote)
    day_graph.add_node("investigator_vote", investigator_vote)

    day_graph.add_edge(START, "PREPARE_ROUND")
    day_graph.add_conditional_edges(
        "PREPARE_ROUND",
        fan_out_discuss,
        ["villager_discuss", "healer_discuss", "wolf_discuss", "investigator_discuss"],
    )
    day_graph.add_edge("villager_discuss", "COLLECT_DISCUSSION")
    day_graph.add_edge("healer_discuss", "COLLECT_DISCUSSION")
    day_graph.add_edge("wolf_discuss", "COLLECT_DISCUSSION")
    day_graph.add_edge("investigator_discuss", "COLLECT_DISCUSSION")

    day_graph.add_conditional_edges("COLLECT_DISCUSSION", check_round)
    day_graph.add_conditional_edges("SUMMARIZE_DAY_DISCUSSION", route_after_day_summary)
    day_graph.add_conditional_edges(
        "START_VOTING",
        fan_out_vote,
        ["villager_vote", "healer_vote", "wolf_vote", "investigator_vote"],
    )
    day_graph.add_edge("villager_vote", "COLLECT_VOTES")
    day_graph.add_edge("healer_vote", "COLLECT_VOTES")
    day_graph.add_edge("wolf_vote", "COLLECT_VOTES")
    day_graph.add_edge("investigator_vote", "COLLECT_VOTES")
    day_graph.add_edge("COLLECT_VOTES", END)

    return day_graph


day_graph = build_day_graph()
day_graph_compiled = day_graph.compile(store=store)

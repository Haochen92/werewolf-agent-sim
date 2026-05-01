from langgraph.graph import END, START, StateGraph

from Agents.graphs.day import day_graph_compiled
from Agents.graphs.healer import healer_graph_compiled
from Agents.graphs.investigator import investigator_graph_compiled
from Agents.graphs.wolf_night import wolf_night_graph_compiled
from Agents.nodes import (
    check_game_end_day,
    check_game_end_night,
    day_resolution,
    end_game,
    initialize_game,
    night_resolution,
    one_more_day,
    route_after_healer_night,
    route_after_wolf_night,
)
from Agents.state import OrchestratorGraph


def day_phase(state: OrchestratorGraph):
    result = day_graph_compiled.invoke(
        {
            "current_day": state["current_day"],
            "day_channel": state.get("day_channel", []),
            "roles": state["roles"],
            "human_player": state["human_player"],
            "investigator_results": state.get("investigator_results", []),
            "surviving_players": state["surviving_wolves"] + state["surviving_villagers"],
            "surviving_wolves": state["surviving_wolves"],
            "surviving_villagers": state["surviving_villagers"],
            "current_round": 1,
            "day_votes": [],
        }
    )

    return {
        "day_channel": result["day_channel"][len(state.get("day_channel", [])) :],
        "day_votes": result.get("day_votes", []),
    }


def wolf_night_phase(state: OrchestratorGraph):
    result = wolf_night_graph_compiled.invoke(
        {
            "day_channel": state.get("day_channel", []),
            "wolf_channel": state.get("wolf_channel", []),
            "surviving_villagers": state["surviving_villagers"],
            "surviving_wolves": state["surviving_wolves"],
            "human_player": state["human_player"],
            "current_day": state["current_day"],
        }
    )

    return {
        "wolf_channel": result["wolf_channel"][len(state.get("wolf_channel", [])) :],
        "wolves_kill_target": result.get("wolves_kill_target"),
    }


def healer_night_phase(state: OrchestratorGraph):
    result = healer_graph_compiled.invoke(
        {
            "day_channel": state.get("day_channel", []),
            "surviving_players": [
                p
                for p in state["surviving_wolves"] + state["surviving_villagers"]
                if p != state["healer_player"]
            ],
            "player_id": state["healer_player"],
            "player_role": "healer",
            "human_player": state["healer_player"] == state["human_player"],
        }
    )

    return {"healer_target": result["healer_target"]}


def investigator_night_phase(state: OrchestratorGraph):
    result = investigator_graph_compiled.invoke(
        {
            "day_channel": state.get("day_channel", []),
            "investigator_results": state.get("investigator_results", []),
            "surviving_players": [
                p
                for p in state["surviving_wolves"] + state["surviving_villagers"]
                if p != state["investigator_player"]
            ],
            "player_id": state["investigator_player"],
            "player_role": "investigator",
            "human_player": state["investigator_player"] == state["human_player"],
        }
    )

    return {"investigator_target": result["investigator_target"]}


def build_parent_graph():
    parent_graph = StateGraph(OrchestratorGraph)

    parent_graph.add_node("INITIALIZE_GAME", initialize_game)
    parent_graph.add_node("DAY_PHASE", day_phase)
    parent_graph.add_node("DAY_RESOLUTION", day_resolution)
    parent_graph.add_node("WOLF_NIGHT_PHASE", wolf_night_phase)
    parent_graph.add_node("HEALER_NIGHT_PHASE", healer_night_phase)
    parent_graph.add_node("INVESTIGATOR_NIGHT_PHASE", investigator_night_phase)
    parent_graph.add_node("NIGHT_RESOLUTION", night_resolution)
    parent_graph.add_node("ONE_MORE_DAY", one_more_day)
    parent_graph.add_node("END_GAME", end_game)

    parent_graph.add_edge(START, "INITIALIZE_GAME")
    parent_graph.add_edge("INITIALIZE_GAME", "DAY_PHASE")
    parent_graph.add_edge("DAY_PHASE", "DAY_RESOLUTION")
    parent_graph.add_conditional_edges("DAY_RESOLUTION", check_game_end_day)
    parent_graph.add_conditional_edges("WOLF_NIGHT_PHASE", route_after_wolf_night)
    parent_graph.add_conditional_edges("HEALER_NIGHT_PHASE", route_after_healer_night)
    parent_graph.add_conditional_edges("NIGHT_RESOLUTION", check_game_end_night)
    parent_graph.add_edge("INVESTIGATOR_NIGHT_PHASE", "NIGHT_RESOLUTION")
    parent_graph.add_edge("ONE_MORE_DAY", "DAY_PHASE")
    parent_graph.add_edge("END_GAME", END)

    return parent_graph


parent_graph = build_parent_graph()
parent_graph_compiled = parent_graph.compile()


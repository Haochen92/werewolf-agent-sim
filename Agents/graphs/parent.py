from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from Agents.graphs.day import day_graph_compiled
from Agents.graphs.healer import healer_graph_compiled
from Agents.graphs.investigator import investigator_graph_compiled
from Agents.graphs.serial_killer import serial_killer_graph_compiled
from Agents.graphs.vigilante import vigilante_graph_compiled
from Agents.graphs.wolf_night import wolf_night_graph_compiled
from Agents.nodes import (
    check_game_end_day,
    check_game_end_night,
    day_resolution,
    end_game,
    initialize_game,
    night_resolution,
    one_more_day,
    post_game_analysis,
    route_after_healer_night,
    route_after_investigator_night,
    route_after_serial_killer_night,
    route_after_wolf_night,
)
from Agents.state import OrchestratorGraph
from Agents.game_config import game_config_from_runnable
from Agents.memory import store
from Agents.tracing import GraphContext


def _child_config(config: RunnableConfig) -> RunnableConfig:
    child_config = dict(config) if config else {}
    child_config.setdefault("recursion_limit", 100)
    return child_config


def day_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    num_survivors = len(state["surviving_wolves"]) + len(state["surviving_villagers"])
    game_config = game_config_from_runnable(config)
    result = day_graph_compiled.invoke(
        {
            "agent_strategies": state.get("agent_strategies", {}),
            "current_day": state["current_day"],
            "day_channel": state.get("day_channel", []),
            "day_summaries": state.get("day_summaries", []),
            "roles": state["roles"],
            "human_player": state["human_player"],
            "investigator_results": state.get("investigator_results", []),
            "surviving_players": state["surviving_wolves"] + state["surviving_villagers"],
            "surviving_wolves": state["surviving_wolves"],
            "surviving_villagers": state["surviving_villagers"],
            "no_lynch_streak": state.get("no_lynch_streak", 0),
            "current_round": 0,
            "day_votes": [],
        },
        # Bound the SCHEDULE self-loop: derive from the cap so graceful terminate fires first.
        config={**_child_config(config), "recursion_limit": game_config.discussion_recursion_limit(num_survivors)},
        context=runtime.context,
    )

    return {
        "day_channel": result["day_channel"][len(state.get("day_channel", [])):],
        "day_summaries": result.get("day_summaries", [])[len(state.get("day_summaries", [])):],
        "day_votes": result.get("day_votes", []),
        "agent_strategies": result.get("agent_strategies", {}),
        "strategy_adoptions": result.get("strategy_adoptions", []),
    }


def wolf_night_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    result = wolf_night_graph_compiled.invoke(
        {
            "agent_strategies": state.get("agent_strategies", {}),
            "day_channel": state.get("day_channel", []),
            "day_summaries": state.get("day_summaries", []),
            "wolf_channel": state.get("wolf_channel", []),
            "surviving_villagers": state["surviving_villagers"],
            "surviving_wolves": state["surviving_wolves"],
            "human_player": state["human_player"],
            "current_day": state["current_day"],
        },
        config=_child_config(config),
        context=runtime.context,
    )

    return {
        "wolf_channel": result["wolf_channel"][len(state.get("wolf_channel", [])):],
        "wolves_kill_target": result.get("wolves_kill_target"),
        "agent_strategies": result.get("agent_strategies", {}),
    }


def healer_night_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    result = healer_graph_compiled.invoke(
        {
            "previous_strategy": state.get("agent_strategies", {}).get(state["healer_player"], ""),
            "strategy_points": "",
            "day_channel": state.get("day_channel", []),
            "day_summaries": state.get("day_summaries", []),
            "surviving_players": [
                p
                for p in state["surviving_wolves"] + state["surviving_villagers"]
                if p != state["healer_player"]
            ],
            "player_id": state["healer_player"],
            "player_role": "healer",
            "human_player": state["healer_player"] == state["human_player"],
        },
        config=_child_config(config),
        context=runtime.context,
    )
    updates = {"healer_target": result.get("healer_target")}
    if result.get("updated_strategy"):
        updates["agent_strategies"] = {
            state["healer_player"]: result["updated_strategy"]
        }

    return updates


def investigator_night_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    result = investigator_graph_compiled.invoke(
        {
            "previous_strategy": state.get("agent_strategies", {}).get(state["investigator_player"], ""),
            "strategy_points": "",
            "day_channel": state.get("day_channel", []),
            "day_summaries": state.get("day_summaries", []),
            "investigator_results": state.get("investigator_results", []),
            "surviving_players": [
                p
                for p in state["surviving_wolves"] + state["surviving_villagers"]
                if p != state["investigator_player"]
            ],
            "player_id": state["investigator_player"],
            "player_role": "investigator",
            "human_player": state["investigator_player"] == state["human_player"],
        },
        config=_child_config(config),
        context=runtime.context,
    )

    updates = {"investigator_target": result.get("investigator_target")}
    if result.get("updated_strategy"):
        updates["agent_strategies"] = {
            state["investigator_player"]: result["updated_strategy"]
        }

    return updates


def serial_killer_night_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    result = serial_killer_graph_compiled.invoke(
        {
            "previous_strategy": state.get("agent_strategies", {}).get(state["serial_killer_player"], ""),
            "strategy_points": "",
            "day_channel": state.get("day_channel", []),
            "day_summaries": state.get("day_summaries", []),
            "surviving_players": [
                p
                for p in state["surviving_wolves"] + state["surviving_villagers"]
                if p != state["serial_killer_player"]
            ],
            "player_id": state["serial_killer_player"],
            "player_role": "serial_killer",
            "human_player": state["serial_killer_player"] == state["human_player"],
        },
        config=_child_config(config),
        context=runtime.context,
    )

    updates = {"serial_killer_target": result.get("serial_killer_target")}
    if result.get("updated_strategy"):
        updates["agent_strategies"] = {
            state["serial_killer_player"]: result["updated_strategy"]
        }

    return updates


def vigilante_night_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    result = vigilante_graph_compiled.invoke(
        {
            "previous_strategy": state.get("agent_strategies", {}).get(state["vigilante_player"], ""),
            "strategy_points": "",
            "day_channel": state.get("day_channel", []),
            "day_summaries": state.get("day_summaries", []),
            "surviving_players": [
                p
                for p in state["surviving_wolves"] + state["surviving_villagers"]
                if p != state["vigilante_player"]
            ],
            "vigilante_bullets": state.get("vigilante_bullets", 0),
            "player_id": state["vigilante_player"],
            "player_role": "vigilante",
            "human_player": state["vigilante_player"] == state["human_player"],
        },
        config=_child_config(config),
        context=runtime.context,
    )

    target = result.get("vigilante_target")
    # "hold_fire" is the no-shot sentinel — normalize to None so resolution skips it.
    updates = {"vigilante_target": None if target == "hold_fire" else target}
    if result.get("updated_strategy"):
        updates["agent_strategies"] = {
            state["vigilante_player"]: result["updated_strategy"]
        }

    return updates


def build_parent_graph():
    parent_graph = StateGraph(OrchestratorGraph, context_schema=GraphContext)

    parent_graph.add_node("INITIALIZE_GAME", initialize_game)
    parent_graph.add_node("DAY_PHASE", day_phase)
    parent_graph.add_node("DAY_RESOLUTION", day_resolution)
    parent_graph.add_node("WOLF_NIGHT_PHASE", wolf_night_phase)
    parent_graph.add_node("HEALER_NIGHT_PHASE", healer_night_phase)
    parent_graph.add_node("SERIAL_KILLER_NIGHT_PHASE", serial_killer_night_phase)
    parent_graph.add_node("INVESTIGATOR_NIGHT_PHASE", investigator_night_phase)
    parent_graph.add_node("VIGILANTE_NIGHT_PHASE", vigilante_night_phase)
    parent_graph.add_node("NIGHT_RESOLUTION", night_resolution)
    parent_graph.add_node("ONE_MORE_DAY", one_more_day)
    parent_graph.add_node("END_GAME", end_game)
    parent_graph.add_node("POST_GAME_ANALYSIS", post_game_analysis)

    parent_graph.add_edge(START, "INITIALIZE_GAME")
    parent_graph.add_edge("INITIALIZE_GAME", "DAY_PHASE")
    parent_graph.add_edge("DAY_PHASE", "DAY_RESOLUTION")
    parent_graph.add_conditional_edges("DAY_RESOLUTION", check_game_end_day)
    parent_graph.add_conditional_edges("WOLF_NIGHT_PHASE", route_after_wolf_night)
    parent_graph.add_conditional_edges("HEALER_NIGHT_PHASE", route_after_healer_night)
    parent_graph.add_conditional_edges("SERIAL_KILLER_NIGHT_PHASE", route_after_serial_killer_night)
    parent_graph.add_conditional_edges("INVESTIGATOR_NIGHT_PHASE", route_after_investigator_night)
    parent_graph.add_edge("VIGILANTE_NIGHT_PHASE", "NIGHT_RESOLUTION")
    parent_graph.add_conditional_edges("NIGHT_RESOLUTION", check_game_end_night)
    parent_graph.add_edge("ONE_MORE_DAY", "DAY_PHASE")
    parent_graph.add_edge("END_GAME", "POST_GAME_ANALYSIS")
    parent_graph.add_edge("POST_GAME_ANALYSIS", END)

    return parent_graph

parent_graph = build_parent_graph()
parent_graph_compiled = parent_graph.compile(store=store)

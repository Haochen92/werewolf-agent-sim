"""Top-level game orchestration graph: the day<->night cycle that drives a whole game.

Each phase is a *subgraph* compiled elsewhere (day; wolf/healer/investigator/serial-killer/
vigilante night). The ``*_phase`` wrappers here invoke that subgraph with a payload built from
orchestrator state, then fold the subgraph's result back as a state delta. Channel/summary
fields are returned as the *newly appended slice only*: the subgraph receives the running list
and returns the grown list, so we diff against what we sent (``result[...][len(sent):]``) and
let the orchestrator's reducer append once instead of duplicating the whole history.

build_parent_graph wires the phases into the day -> resolution -> night-groups -> resolution ->
(next day | end) loop; the per-night-actor routing and termination live in the ``route_after_*``
and ``check_game_end_*`` functions imported from Agents.nodes.
"""

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from Agents.graphs.day import day_graph_compiled
from Agents.graphs.night.healer import healer_graph_compiled
from Agents.graphs.night.investigator import investigator_graph_compiled
from Agents.graphs.night.serial_killer import serial_killer_graph_compiled
from Agents.graphs.night.vigilante import vigilante_graph_compiled
from Agents.graphs.night.wolf import wolf_night_graph_compiled
from Agents.nodes import (
    check_game_end_day,
    check_game_end_night,
    day_resolution,
    end_game,
    initialize_game,
    night_finalize,
    night_kill_resolution,
    one_more_day,
    post_game_analysis,
    route_after_healer_night,
    route_after_kill_resolution,
    route_after_serial_killer_night,
    route_after_wolf_night,
)
from Agents.state import (
    DayGraphState,
    HealerNightGraph,
    InvestigatorNightGraph,
    OrchestratorGraph,
    SerialKillerNightGraph,
    VigilanteNightGraph,
    WolfNightGraph,
)
from Agents.config import (
    child_runnable_config,
    discussion_recursion_limit,
    game_config_from_runnable,
)
from Agents.memory import store
from Agents.schemas.roles import cast_role_counts
from Agents.tracing import GraphContext


def day_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    """Run the day subgraph (sequential discussion + voting) and fold its delta back.

    Reads rosters / strategies / channels / results from orchestrator state to seed the day
    subgraph, and caps the discussion self-loop via discussion_recursion_limit(survivors) so the
    scheduler's graceful terminate fires before the hard recursion limit. Returns only what the
    day *added* — channel/summary entries sliced past what we sent — plus votes, strategy
    updates, and adoptions.
    """
    num_survivors = len(state["surviving_wolves"]) + len(state["surviving_villagers"]) 
    game_config = game_config_from_runnable(config)
    payload: DayGraphState = {
        "agent_strategies": state.get("agent_strategies", {}),
        "current_day": state["current_day"],
        "day_channel": state.get("day_channel", []),
        "day_summaries": state.get("day_summaries", []),
        "dead_roster": state.get("dead_roster", []),
        "wolf_channel": state.get("wolf_channel", []),
        "roles": state["roles"],
        "human_player": state["human_player"],
        "investigator_results": state.get("investigator_results", []),
        "vigilante_results": state.get("vigilante_results", []),
        "vigilante_bullets": state.get("vigilante_bullets", 0),
        "surviving_villagers": state["surviving_villagers"],
        "surviving_wolves": state["surviving_wolves"],
        "no_lynch_streak": state.get("no_lynch_streak", 0),
        "current_round": 0,
        "day_votes": [],
    }
    result = day_graph_compiled.invoke(
        payload,
        # Bound the SCHEDULE self-loop: derive from the cap so graceful terminate fires first.
        config=child_runnable_config(
            config, recursion_limit=discussion_recursion_limit(game_config, num_survivors)
        ),
        context=runtime.context,
    )

    return {
        "day_channel": result["day_channel"][len(state.get("day_channel", [])):],
        "day_summaries": result.get("day_summaries", [])[len(state.get("day_summaries", [])):],
        "day_votes": result.get("day_votes", []),
        "agent_strategies": result.get("agent_strategies", {}),
    }


def wolf_night_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    """Run the wolf-night subgraph (multi-wolf discussion -> kill vote) and fold its delta back.

    Seeds the subgraph with the wolf channel + both rosters; returns the newly appended
    wolf-channel slice, the agreed wolves_kill_target, and any strategy/adoption delta.
    """
    payload: WolfNightGraph = {
        "agent_strategies": state.get("agent_strategies", {}),
        "day_channel": state.get("day_channel", []),
        "day_summaries": state.get("day_summaries", []),
        "wolf_channel": state.get("wolf_channel", []),
        "surviving_villagers": state["surviving_villagers"],
        "surviving_wolves": state["surviving_wolves"],
        "human_player": state["human_player"],
        "current_day": state["current_day"],
    }
    result = wolf_night_graph_compiled.invoke(
        payload,
        config=child_runnable_config(config),
        context=runtime.context,
    )

    updates = {
        "wolf_channel": result["wolf_channel"][len(state.get("wolf_channel", [])):],
        "wolves_kill_target": result.get("wolves_kill_target"),
        "agent_strategies": result.get("agent_strategies", {}),
    }
    return updates


def healer_night_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    """Run the healer night subgraph: the healer picks one player to protect.

    Single-actor night pattern (shared by healer/investigator/serial_killer/vigilante): read the
    role's player marker (healer_player) + shared night context, offer every *other* survivor as
    a target, invoke the role subgraph, and write the role's target (healer_target) plus any
    strategy/adoption delta.
    """
    healer = state["healer_player"]
    assert healer is not None  # routing only enters this phase while the healer is alive
    payload: HealerNightGraph = {
        "previous_strategy": state.get("agent_strategies", {}).get(healer, ""),
        "strategy_points": "",
        "current_day": state["current_day"],
        "current_round": 0,
        "day_channel": state.get("day_channel", []),
        "day_summaries": state.get("day_summaries", []),
        # Both public: the dead roster is announced, the cast census is counts-only (no identities).
        "dead_roster": state.get("dead_roster", []),
        "cast_role_counts": cast_role_counts(state.get("roles", {})),
        "surviving_players": [
            p
            for p in state["surviving_wolves"] + state["surviving_villagers"]
            if p != healer
        ],
        "player_id": healer,
        "player_role": "healer",
        "human_player": healer == state["human_player"],
    }
    result = healer_graph_compiled.invoke(
        payload,
        config=child_runnable_config(config),
        context=runtime.context,
    )
    updates = {"healer_target": result.get("healer_target")}
    if result.get("updated_strategy"):
        updates["agent_strategies"] = {
            healer: result["updated_strategy"]
        }
    return updates


def investigator_night_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    """Single-actor night phase (see healer_night_phase): the investigator learns one player's
    true role; reads investigator_player + prior results, writes investigator_target."""
    investigator = state["investigator_player"]
    assert investigator is not None  # routing only enters this phase while the investigator is alive
    payload: InvestigatorNightGraph = {
        "previous_strategy": state.get("agent_strategies", {}).get(investigator, ""),
        "strategy_points": "",
        "current_day": state["current_day"],
        "current_round": 0,
        "day_channel": state.get("day_channel", []),
        "day_summaries": state.get("day_summaries", []),
        # Both public: the dead roster is announced, the cast census is counts-only (no identities).
        "dead_roster": state.get("dead_roster", []),
        "cast_role_counts": cast_role_counts(state.get("roles", {})),
        "investigator_results": state.get("investigator_results", []),
        "surviving_players": [
            p
            for p in state["surviving_wolves"] + state["surviving_villagers"]
            if p != investigator
        ],
        "player_id": investigator,
        "player_role": "investigator",
        "human_player": investigator == state["human_player"],
    }
    result = investigator_graph_compiled.invoke(
        payload,
        config=child_runnable_config(config),
        context=runtime.context,
    )

    updates = {"investigator_target": result.get("investigator_target")}
    if result.get("updated_strategy"):
        updates["agent_strategies"] = {
            investigator: result["updated_strategy"]
        }
    return updates


def serial_killer_night_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    """Single-actor night phase (see healer_night_phase): the serial killer picks a kill target;
    reads serial_killer_player, writes serial_killer_target."""
    serial_killer = state["serial_killer_player"]
    assert serial_killer is not None  # routing only enters this phase while the serial killer is alive
    payload: SerialKillerNightGraph = {
        "previous_strategy": state.get("agent_strategies", {}).get(serial_killer, ""),
        "strategy_points": "",
        "current_day": state["current_day"],
        "current_round": 0,
        "day_channel": state.get("day_channel", []),
        "day_summaries": state.get("day_summaries", []),
        # Both public: the dead roster is announced, the cast census is counts-only (no identities).
        "dead_roster": state.get("dead_roster", []),
        "cast_role_counts": cast_role_counts(state.get("roles", {})),
        "surviving_players": [
            p
            for p in state["surviving_wolves"] + state["surviving_villagers"]
            if p != serial_killer
        ],
        "player_id": serial_killer,
        "player_role": "serial_killer",
        "human_player": serial_killer == state["human_player"],
    }
    result = serial_killer_graph_compiled.invoke(
        payload,
        config=child_runnable_config(config),
        context=runtime.context,
    )

    updates = {"serial_killer_target": result.get("serial_killer_target")}
    if result.get("updated_strategy"):
        updates["agent_strategies"] = {
            serial_killer: result["updated_strategy"]
        }
    return updates


def vigilante_night_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    """Single-actor night phase (see healer_night_phase): the vigilante may shoot or hold fire.

    Reads vigilante_player + remaining bullets/results; "hold_fire" is normalized to None on the
    way out (see below) so resolution skips a non-shot. Writes vigilante_target.
    """
    vigilante = state["vigilante_player"]
    assert vigilante is not None  # routing only enters this phase while the vigilante is alive
    payload: VigilanteNightGraph = {
        "previous_strategy": state.get("agent_strategies", {}).get(vigilante, ""),
        "strategy_points": "",
        "current_day": state["current_day"],
        "current_round": 0,
        "day_channel": state.get("day_channel", []),
        "day_summaries": state.get("day_summaries", []),
        # Both public: the dead roster is announced, the cast census is counts-only (no identities).
        "dead_roster": state.get("dead_roster", []),
        "cast_role_counts": cast_role_counts(state.get("roles", {})),
        "surviving_players": [
            p
            for p in state["surviving_wolves"] + state["surviving_villagers"]
            if p != vigilante
        ],
        "vigilante_bullets": state.get("vigilante_bullets", 0),
        "vigilante_results": state.get("vigilante_results", []),
        "player_id": vigilante,
        "player_role": "vigilante",
        "human_player": vigilante == state["human_player"],
    }
    result = vigilante_graph_compiled.invoke(
        payload,
        config=child_runnable_config(config),
        context=runtime.context,
    )

    target = result.get("vigilante_target")
    # "hold_fire" is the no-shot sentinel — normalize to None so resolution skips it.
    updates = {"vigilante_target": None if target == "hold_fire" else target}
    if result.get("updated_strategy"):
        updates["agent_strategies"] = {
            vigilante: result["updated_strategy"]
        }
    return updates


def build_parent_graph():
    """Wire the orchestration topology.

    START -> INITIALIZE_GAME -> DAY_PHASE -> DAY_RESOLUTION -> (check_game_end_day: END_GAME |
    the first present night phase). Night runs as two groups: group 1 (wolves -> healer ->
    serial_killer -> vigilante) routes actor-to-actor via route_after_* down to KILL_RESOLUTION;
    group 2 is the investigator after kills resolve, gated by route_after_kill_resolution, then
    NIGHT_FINALIZE. NIGHT_FINALIZE -> (check_game_end_night: ONE_MORE_DAY -> DAY_PHASE | END_GAME).
    END_GAME -> POST_GAME_ANALYSIS -> END.
    """
    parent_graph = StateGraph(OrchestratorGraph, context_schema=GraphContext)

    parent_graph.add_node("INITIALIZE_GAME", initialize_game)
    parent_graph.add_node("DAY_PHASE", day_phase)
    parent_graph.add_node("DAY_RESOLUTION", day_resolution)
    parent_graph.add_node("WOLF_NIGHT_PHASE", wolf_night_phase)
    parent_graph.add_node("HEALER_NIGHT_PHASE", healer_night_phase)
    parent_graph.add_node("SERIAL_KILLER_NIGHT_PHASE", serial_killer_night_phase)
    parent_graph.add_node("INVESTIGATOR_NIGHT_PHASE", investigator_night_phase)
    parent_graph.add_node("VIGILANTE_NIGHT_PHASE", vigilante_night_phase)
    parent_graph.add_node("KILL_RESOLUTION", night_kill_resolution)
    parent_graph.add_node("NIGHT_FINALIZE", night_finalize)
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
    parent_graph.add_edge("VIGILANTE_NIGHT_PHASE", "KILL_RESOLUTION")
    parent_graph.add_conditional_edges("KILL_RESOLUTION", route_after_kill_resolution)
    parent_graph.add_edge("INVESTIGATOR_NIGHT_PHASE", "NIGHT_FINALIZE")
    parent_graph.add_conditional_edges("NIGHT_FINALIZE", check_game_end_night)
    parent_graph.add_edge("ONE_MORE_DAY", "DAY_PHASE")
    parent_graph.add_edge("END_GAME", "POST_GAME_ANALYSIS")
    parent_graph.add_edge("POST_GAME_ANALYSIS", END)

    return parent_graph

parent_graph = build_parent_graph()
parent_graph_compiled = parent_graph.compile(store=store)

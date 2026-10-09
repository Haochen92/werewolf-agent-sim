"""Top-level game orchestration graph: the day<->night cycle that drives a whole game.

The day and the pack's night are *subgraphs* compiled elsewhere; the ``*_phase`` wrappers here
invoke them with a payload built from orchestrator state, then fold the result back as a state
delta. Channel/summary fields are returned as the *newly appended slice only*: the subgraph
receives the running list and returns the grown list, so we diff against what we sent
(``result[...][len(sent):]``) and let the orchestrator's reducer append once instead of
duplicating the whole history. Each solo role's night is one named node, ``<ROLE>_NIGHT_PHASE``,
sharing one body (Agents.nodes.night.solo).

build_parent_graph wires the phases into the day -> resolution -> night-groups -> resolution ->
(next day | end) loop; the per-night-actor routing and termination live in the ``route_*`` and
``check_game_end_*`` functions imported from Agents.nodes.
"""

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from Agents.graphs.day import day_graph_compiled
from Agents.graphs.night.pack import pack_night_graph_compiled
from Agents.nodes import (
    check_game_end_day,
    check_game_end_night,
    day_resolution,
    end_game,
    initialize_game,
    night_phase_name,
    night_resolution,
    night_start,
    one_more_day,
    route_night_actors,
    post_game_analysis,
    solo_night_phase,
)
from Agents.rules.night import pack_carrier
from Agents.state import DayGraphState, OrchestratorGraph, PackNightGraph
from Agents.config import (
    child_runnable_config,
    discussion_recursion_limit,
    game_config_from_runnable,
)
from Agents.memory import store, checkpointer
from Agents.schemas.roles import ROLE_SPECS, cast_role_counts, roles
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
        "lineup": state.get("lineup", []),
        "human_players": state["human_players"],
        "night_actions": state.get("night_actions", []),
        "uses_left": state.get("uses_left", {}),
        "speculator_pick": state.get("speculator_pick"),
        "fortune_points": state.get("fortune_points", 0),
        "surviving_villagers": state["surviving_villagers"],
        "surviving_wolves": state["surviving_wolves"],
        "no_lynch_streak": state.get("no_lynch_streak", 0),
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


def pack_night_phase(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    """Run the pack's night subgraph: the chat, the carrier's kill, each wolf's skill. Folds
    back the new chat entries, the pack's choices and any strategy notes."""
    sent_channel = state.get("wolf_channel", [])
    payload: PackNightGraph = {
        "day_channel": state.get("day_channel", []),
        "day_summaries": state.get("day_summaries", []),
        "dead_roster": state.get("dead_roster", []),
        "cast_role_counts": cast_role_counts(state.get("roles", {})),
        "lineup": state.get("lineup", []),
        "night_actions": state.get("night_actions", []),
        "wolf_channel": sent_channel,
        "surviving_wolves": state["surviving_wolves"],
        "surviving_villagers": state["surviving_villagers"],
        "roles": state["roles"],
        "uses_left": state.get("uses_left", {}),
        "agent_strategies": state.get("agent_strategies", {}),
        "human_players": state["human_players"],
        "current_day": state["current_day"],
        "current_round": 1,
        "carrier": pack_carrier(state["surviving_wolves"], state["current_day"]) or "",
        "wolves_target": None,
        "night_choices": [],
    }
    result = pack_night_graph_compiled.invoke(
        payload, config=child_runnable_config(config), context=runtime.context,
    )
    return {
        "wolf_channel": result.get("wolf_channel", [])[len(sent_channel):],
        "night_choices": result.get("night_choices", []),
        "agent_strategies": result.get("agent_strategies", {}),
    }


# One named night node per role of the pool that acts on its own at night.
SOLO_NIGHT_PHASES = {
    night_phase_name(role): solo_night_phase(role)
    for role in roles if ROLE_SPECS[role].night_action and not ROLE_SPECS[role].pack
}


def build_parent_graph():
    """Wire the orchestration topology.

    START -> INITIALIZE_GAME -> DAY_PHASE -> DAY_RESOLUTION -> (check_game_end_day: END_GAME |
    NIGHT_START). NIGHT_START is the no-op night anchor -> (route_night_actors: the list of
    present night phases, run in ONE parallel superstep). Every phase edges into
    NIGHT_RESOLUTION, the barrier, which resolves the night and -> (check_game_end_night:
    ONE_MORE_DAY -> DAY_PHASE | END_GAME). END_GAME -> POST_GAME_ANALYSIS -> END.
    """
    parent_graph = StateGraph(OrchestratorGraph, context_schema=GraphContext)

    parent_graph.add_node("INITIALIZE_GAME", initialize_game)
    parent_graph.add_node("DAY_PHASE", day_phase)
    parent_graph.add_node("DAY_RESOLUTION", day_resolution)
    parent_graph.add_node("PACK_NIGHT_PHASE", pack_night_phase)
    for name, phase in SOLO_NIGHT_PHASES.items():
        parent_graph.add_node(name, phase)
    parent_graph.add_node("NIGHT_START", night_start)
    parent_graph.add_node("NIGHT_RESOLUTION", night_resolution)
    parent_graph.add_node("ONE_MORE_DAY", one_more_day)
    parent_graph.add_node("END_GAME", end_game)
    parent_graph.add_node("POST_GAME_ANALYSIS", post_game_analysis)

    parent_graph.add_edge(START, "INITIALIZE_GAME")
    parent_graph.add_edge("INITIALIZE_GAME", "DAY_PHASE")
    parent_graph.add_edge("DAY_PHASE", "DAY_RESOLUTION")
    parent_graph.add_conditional_edges(
        "DAY_RESOLUTION",
        check_game_end_day,
        ["END_GAME", "NIGHT_START"],
    )
    # List-returning router: NIGHT_START fans out every present night actor in one parallel
    # superstep. path_map is explicit because a list return defeats Literal inference.
    night_phases = ["PACK_NIGHT_PHASE", *SOLO_NIGHT_PHASES]
    parent_graph.add_conditional_edges("NIGHT_START", route_night_actors, night_phases)
    # BSP barrier: all fan-out branches complete before the next superstep, so
    # NIGHT_RESOLUTION sees every actor's committed choice (collect_votes precedent).
    for name in night_phases:
        parent_graph.add_edge(name, "NIGHT_RESOLUTION")
    parent_graph.add_conditional_edges("NIGHT_RESOLUTION", check_game_end_night)
    parent_graph.add_edge("ONE_MORE_DAY", "DAY_PHASE")
    parent_graph.add_edge("END_GAME", "POST_GAME_ANALYSIS")
    parent_graph.add_edge("POST_GAME_ANALYSIS", END)

    return parent_graph

parent_graph = build_parent_graph()
parent_graph_compiled = parent_graph.compile(store=store, checkpointer=checkpointer)

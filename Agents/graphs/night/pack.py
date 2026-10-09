"""The pack's night subgraph: a miniature of the day phase (the only multi-agent night).

START -> PREPARE_PACK_NIGHT (scheduler hub, commits the round) -(route_pack_speaker: ONE wolf
per pass during the chat rounds, each looping back through PREPARE)-> PACK_CHAT; chat spent ->
START_CARRIER -(route_carrier)-> CARRIER_KILL -(pack_fan_out_skills: every wolf in parallel)->
PACK_SKILL -> COLLECT_PACK -> END. An extinct pack ends immediately with no kill. Node bodies
live in Agents.nodes.night.pack.
"""

from langgraph.cache.memory import InMemoryCache
from langgraph.graph import END, START, StateGraph
from langgraph.types import CachePolicy

from Agents.config.langgraph import TURN_CACHE_TTL_SECONDS, turn_cache_key
from Agents.memory import store
from Agents.nodes.night.pack import (
    carrier_kill,
    collect_pack,
    pack_chat,
    pack_fan_out_skills,
    pack_skill,
    prepare_pack_night,
    route_carrier,
    route_pack_speaker,
    start_carrier,
)
from Agents.state import PackNightGraph
from Agents.tracing import GraphContext


def build_pack_night_graph():
    graph = StateGraph(PackNightGraph, context_schema=GraphContext)

    graph.add_node("PREPARE_PACK_NIGHT", prepare_pack_night)
    graph.add_node("PACK_CHAT", pack_chat)
    graph.add_node("START_CARRIER", start_carrier)
    # Cached LLM turns + uncached human twins: the skill turns are the pack night's one parallel
    # superstep, so a human-wolf resume re-executes the LLM siblings — the cache replays them
    # instead. interrupt() must never sit inside a cached node (crashes this langgraph version
    # on resume). Same pattern + rationale as the day graph's vote/vote_human.
    cached = CachePolicy(ttl=TURN_CACHE_TTL_SECONDS, key_func=turn_cache_key)
    graph.add_node("CARRIER_KILL", carrier_kill, cache_policy=cached)
    graph.add_node("CARRIER_KILL_HUMAN", carrier_kill)
    graph.add_node("PACK_SKILL", pack_skill, cache_policy=cached)
    graph.add_node("PACK_SKILL_HUMAN", pack_skill)
    graph.add_node("COLLECT_PACK", collect_pack)

    graph.add_edge(START, "PREPARE_PACK_NIGHT")
    graph.add_conditional_edges("PREPARE_PACK_NIGHT", route_pack_speaker, ["PACK_CHAT", "START_CARRIER", END])
    graph.add_edge("PACK_CHAT", "PREPARE_PACK_NIGHT")
    graph.add_conditional_edges("START_CARRIER", route_carrier, ["CARRIER_KILL", "CARRIER_KILL_HUMAN", END])
    graph.add_conditional_edges("CARRIER_KILL", pack_fan_out_skills, ["PACK_SKILL", "PACK_SKILL_HUMAN", "COLLECT_PACK"])
    graph.add_conditional_edges("CARRIER_KILL_HUMAN", pack_fan_out_skills, ["PACK_SKILL", "PACK_SKILL_HUMAN", "COLLECT_PACK"])
    graph.add_edge("PACK_SKILL", "COLLECT_PACK")
    graph.add_edge("PACK_SKILL_HUMAN", "COLLECT_PACK")
    graph.add_edge("COLLECT_PACK", END)
    return graph


pack_night_graph = build_pack_night_graph()
pack_night_graph_compiled = pack_night_graph.compile(store=store, cache=InMemoryCache())

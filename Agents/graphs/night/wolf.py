"""Wolf-night subgraph: a miniature of the day phase (the only multi-agent night).

START -> PREPARE_WOLF_NIGHT (scheduler hub, commits the round) -(route_wolf_speaker: ONE wolf
per pass during the talk rounds, each looping back through PREPARE)-> WOLF_NIGHT_DISCUSS;
talk spent -> START_WOLF_VOTE (marker) -(wolf_fan_out_vote: every wolf in parallel)->
WOLF_NIGHT_VOTE -> COLLECT_WOLF_VOTES (tally) -> END. Extinct pack ends immediately with no
kill target. Node bodies live in Agents.nodes (night/wolf.py).
"""

from langgraph.cache.memory import InMemoryCache
from langgraph.graph import END, START, StateGraph
from langgraph.types import CachePolicy

from Agents.config.langgraph import TURN_CACHE_TTL_SECONDS, turn_cache_key
from Agents.nodes import wolf_night_discuss, wolf_night_vote
from Agents.memory import store
from Agents.nodes import (
    collect_wolf_votes,
    prepare_wolf_night,
    route_wolf_speaker,
    start_wolf_vote,
    wolf_fan_out_vote,
)
from Agents.state import WolfNightGraph
from Agents.tracing import GraphContext


def build_wolf_night_graph():
    wolf_night_graph = StateGraph(WolfNightGraph, context_schema=GraphContext)

    wolf_night_graph.add_node("PREPARE_WOLF_NIGHT", prepare_wolf_night)
    wolf_night_graph.add_node("WOLF_NIGHT_DISCUSS", wolf_night_discuss)
    wolf_night_graph.add_node("START_WOLF_VOTE", start_wolf_vote)
    # Cached LLM vote + uncached human twin: the pack vote is the wolf night's one parallel
    # superstep, so a human-wolf resume re-executes the LLM siblings — the cache replays
    # them instead. interrupt() must never sit inside a cached node (crashes this langgraph
    # version on resume). Same pattern + rationale as the day graph's vote/vote_human.
    wolf_night_graph.add_node("WOLF_NIGHT_VOTE", wolf_night_vote,
                              cache_policy=CachePolicy(ttl=TURN_CACHE_TTL_SECONDS,
                                                       key_func=turn_cache_key))
    wolf_night_graph.add_node("WOLF_NIGHT_VOTE_HUMAN", wolf_night_vote)
    wolf_night_graph.add_node("COLLECT_WOLF_VOTES", collect_wolf_votes)

    wolf_night_graph.add_edge(START, "PREPARE_WOLF_NIGHT")
    wolf_night_graph.add_conditional_edges(
        "PREPARE_WOLF_NIGHT",
        route_wolf_speaker,
        ["WOLF_NIGHT_DISCUSS", "START_WOLF_VOTE", END],
    )
    wolf_night_graph.add_edge("WOLF_NIGHT_DISCUSS", "PREPARE_WOLF_NIGHT")
    wolf_night_graph.add_conditional_edges(
        "START_WOLF_VOTE", wolf_fan_out_vote,
        ["WOLF_NIGHT_VOTE", "WOLF_NIGHT_VOTE_HUMAN"]
    )
    wolf_night_graph.add_edge("WOLF_NIGHT_VOTE", "COLLECT_WOLF_VOTES")
    wolf_night_graph.add_edge("WOLF_NIGHT_VOTE_HUMAN", "COLLECT_WOLF_VOTES")
    wolf_night_graph.add_edge("COLLECT_WOLF_VOTES", END)

    return wolf_night_graph


wolf_night_graph = build_wolf_night_graph()
wolf_night_graph_compiled = wolf_night_graph.compile(store=store, cache=InMemoryCache())

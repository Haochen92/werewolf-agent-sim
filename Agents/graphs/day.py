"""Day subgraph topology: sequential discussion, then concurrent voting.

Discussion is one-speaker-at-a-time: SCHEDULE picks the next speaker (route_speaker) and the
``discuss`` node loops straight back to SCHEDULE, until route_speaker terminates to
SUMMARIZE_DAY_DISCUSSION. Voting is concurrent: START_VOTING fans every survivor out to the
``vote`` node (fan_out_vote, one Send per survivor) and COLLECT_VOTES is the rejoin barrier.
There is ONE generic node per phase — the role rides the Send payload (``player_role``) and
selects the prompt inside the node; role-specific *content* is payload data, not topology.
The node *bodies* live in Agents.nodes (day/actors.py + day/flow.py); this file is wiring only.

Trace of one discussion turn (the call chain spans four files by design — scheduling, the
audited payload boundary, the actor node, and the shared turn engine are deliberately
separate layers):

    SCHEDULE                     no-op loop anchor (flow.day_scheduler)
    -> route_speaker             EDGE: picks speaker or terminates; edges never commit,
       (flow)                    which is why firing_reason must ride the Send to survive
    -> build_speaker_send        builds the role-gated payload -- THE leak boundary
       (flow)                    (tests/leak_test.py check_* target this layer)
    -> discuss                   (actors) generic node; payload["player_role"] selects the prompt
    -> run_memory_informed_action(turn/pipeline.py)  retrieval -> prompt -> LLM -> validate;
       its return value is the DayChannel delta the superstep commits
"""

from langgraph.cache.memory import InMemoryCache
from langgraph.graph import END, START, StateGraph
from langgraph.types import CachePolicy

from Agents.config.langgraph import TURN_CACHE_TTL_SECONDS, turn_cache_key
from Agents.memory import store
from Agents.nodes import (
    discuss,
    vote,
)
from Agents.nodes import (
    collect_votes,
    fan_out_vote,
    day_scheduler,
    route_after_day_summary,
    start_voting,
    summarize_day_discussion,
    route_speaker
)
from Agents.state import DayGraphState
from Agents.tracing import GraphContext


def build_day_graph():
    """Wire the day topology: START -> SCHEDULE -(route_speaker)-> discuss (which loops back
    to SCHEDULE) | SUMMARIZE_DAY_DISCUSSION -(route_after_day_summary)-> START_VOTING | END;
    START_VOTING fans the survivors out to vote -> COLLECT_VOTES -> END."""
    day_graph = StateGraph(DayGraphState, context_schema=GraphContext)

    day_graph.add_node("SCHEDULE", day_scheduler)
    day_graph.add_node("SUMMARIZE_DAY_DISCUSSION", summarize_day_discussion)
    day_graph.add_node("START_VOTING", start_voting)
    day_graph.add_node("COLLECT_VOTES", collect_votes)

    day_graph.add_node("discuss", discuss)
    # The LLM vote node is CACHED: a human-vote resume aborts and re-executes this whole
    # superstep (imperative-invoke geometry), and the cache turns each sibling re-run into
    # a replay of its recorded result — no re-billed calls, no vote flip-flops. Humans vote
    # through the UNCACHED twin (same body): wrapping interrupt() in a cache_policy crashes
    # this langgraph version on resume (empty-writes cache entry). Probes: scratchpad
    # cache_policy_probe.py / cache_split_probe.py, 2026-08-19.
    day_graph.add_node("vote", vote, cache_policy=CachePolicy(
        ttl=TURN_CACHE_TTL_SECONDS, key_func=turn_cache_key))
    day_graph.add_node("vote_human", vote)

    day_graph.add_edge(START, "SCHEDULE")
    day_graph.add_conditional_edges(
        "SCHEDULE",
        route_speaker,
        ["discuss", "SUMMARIZE_DAY_DISCUSSION"],
    )
    # Self-loop to route back to the scheduler after each speech
    day_graph.add_edge("discuss", "SCHEDULE")

    day_graph.add_conditional_edges(
        "SUMMARIZE_DAY_DISCUSSION",
        route_after_day_summary,
        ["START_VOTING", END],
    )
    day_graph.add_conditional_edges("START_VOTING", fan_out_vote, ["vote", "vote_human"])
    day_graph.add_edge("vote", "COLLECT_VOTES")
    day_graph.add_edge("vote_human", "COLLECT_VOTES")
    day_graph.add_edge("COLLECT_VOTES", END)

    return day_graph


day_graph = build_day_graph()
day_graph_compiled = day_graph.compile(store=store, cache=InMemoryCache())

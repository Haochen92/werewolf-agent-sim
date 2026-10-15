"""Day subgraph topology: an opening round, sequential discussion, a closing round, the vote.

The day's four kinds of step (Phase 2, discussion_evidence.md §7):

- ROUNDS are concurrent: START_OPENING / START_CLOSING fan the round's players out to
  ``round_turn`` (fan_out_round, one Send per player) and COLLECT_ROUND is the rejoin barrier
  that orders and numbers their lines into day_channel. Day 1 is the opening alone.
- DISCUSSION is one speaker at a time: SCHEDULE fires the next speaker (route_speaker: whoever
  owes an answer, else the sweep's next player who has not spoken) and the ``discuss`` node
  loops straight back to SCHEDULE, until nobody is owed and the sweeps are done; then
  route_after_discussion picks START_CLOSING (someone has two accusers) or
  SUMMARIZE_DAY_DISCUSSION.
- VOTING is concurrent: START_VOTING fans every survivor out to ``vote`` (fan_out_vote) and
  COLLECT_VOTES is the rejoin barrier.

There is ONE generic node per kind of turn — the role rides the Send payload (``player_role``)
and selects the prompt inside the node; role-specific *content* is payload data, not topology.
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

A round turn takes the same chain from fan_out_round (flow.fan_out_day, the same payload
builder the vote uses) through ``round_turn`` (actors), whose delta is a RoundCandidate for
COLLECT_ROUND rather than a day_channel entry.
"""

from langgraph.cache.memory import InMemoryCache
from langgraph.graph import END, START, StateGraph
from langgraph.types import CachePolicy

from Agents.config.langgraph import TURN_CACHE_TTL_SECONDS, turn_cache_key
from Agents.memory import store
from Agents.nodes import (
    discuss,
    round_turn,
    vote,
)
from Agents.nodes import (
    collect_round,
    collect_votes,
    day_scheduler,
    fan_out_round,
    fan_out_vote,
    route_after_day_summary,
    route_after_round,
    route_speaker,
    start_closing,
    start_opening,
    start_voting,
    summarize_day_discussion,
)
from Agents.state import DayGraphState
from Agents.tracing import GraphContext


def build_day_graph():
    """Wire the day topology:

        START -> START_OPENING -(fan_out_round)-> round_turn | round_turn_human -> COLLECT_ROUND
        COLLECT_ROUND -(route_after_round)-> SCHEDULE (voting day) | SUMMARIZE_DAY_DISCUSSION (day 1)
        SCHEDULE -(route_speaker)-> discuss (loops back) | START_CLOSING | SUMMARIZE
        START_CLOSING -(fan_out_round)-> round_turn | round_turn_human -> COLLECT_ROUND -> SUMMARIZE
        SUMMARIZE_DAY_DISCUSSION -(route_after_day_summary)-> START_VOTING | END
        START_VOTING -(fan_out_vote)-> vote | vote_human -> COLLECT_VOTES -> END
    """
    day_graph = StateGraph(DayGraphState, context_schema=GraphContext)

    day_graph.add_node("START_OPENING", start_opening)
    day_graph.add_node("START_CLOSING", start_closing)
    day_graph.add_node("COLLECT_ROUND", collect_round)
    day_graph.add_node("SCHEDULE", day_scheduler)
    day_graph.add_node("SUMMARIZE_DAY_DISCUSSION", summarize_day_discussion)
    day_graph.add_node("START_VOTING", start_voting)
    day_graph.add_node("COLLECT_VOTES", collect_votes)

    day_graph.add_node("discuss", discuss)
    # The parallel LLM turn nodes (a round's turns, the votes) are CACHED: a human's resume
    # aborts and re-executes the whole superstep (imperative-invoke geometry), and the cache
    # turns each sibling re-run into a replay of its recorded result — no re-billed calls, no
    # lines or votes changing between the runs. Humans go through the UNCACHED twin (same
    # body): wrapping interrupt() in a cache_policy crashes on resume (IndexError in the
    # cached-writes replay). Probed 2026-08-19 on langgraph 1.1.10 and again 2026-10-07 on
    # 1.2.14, the newest release: same crash, and the docs call cache + interrupt in one task
    # unsupported, so the twin is the supported shape.
    turn_cache = CachePolicy(ttl=TURN_CACHE_TTL_SECONDS, key_func=turn_cache_key)
    day_graph.add_node("round_turn", round_turn, cache_policy=turn_cache)
    day_graph.add_node("round_turn_human", round_turn)
    day_graph.add_node("vote", vote, cache_policy=turn_cache)
    day_graph.add_node("vote_human", vote)

    # The opening round, then the discussion (voting days) or the summary (day 1).
    day_graph.add_edge(START, "START_OPENING")
    day_graph.add_conditional_edges("START_OPENING", fan_out_round, ["round_turn", "round_turn_human"])
    day_graph.add_edge("round_turn", "COLLECT_ROUND")
    day_graph.add_edge("round_turn_human", "COLLECT_ROUND")
    day_graph.add_conditional_edges(
        "COLLECT_ROUND",
        route_after_round,
        ["SCHEDULE", "SUMMARIZE_DAY_DISCUSSION"],
    )

    # The discussion: one speaker at a time (the reactive chains, then the sweep), back to
    # SCHEDULE after each, until nobody is owed and the sweeps are done; then the closing
    # (someone has two accusers) or the summary — route_after_discussion decides.
    day_graph.add_conditional_edges(
        "SCHEDULE",
        route_speaker,
        ["discuss", "START_CLOSING", "SUMMARIZE_DAY_DISCUSSION"],
    )
    day_graph.add_edge("discuss", "SCHEDULE")

    # The closing shares the round nodes with the opening; route_after_round sends it to the summary.
    day_graph.add_conditional_edges("START_CLOSING", fan_out_round, ["round_turn", "round_turn_human"])

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

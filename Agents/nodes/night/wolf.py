"""Wolf night: the one multi-agent night action, shaped as a miniature of the day phase.

The structure mirrors day on purpose (one pattern to know, not two):
PREPARE_WOLF_NIGHT is the scheduler hub (day_scheduler analog — except it commits the talk
round, wolf night's one piece of non-derivable bookkeeping); route_wolf_speaker is the
scheduler hop (route_speaker analog: ONE wolf at a time through WOLF_NIGHT_DISCUSS, each
speaker reading everything said before their turn); START_WOLF_VOTE is the phase marker
(START_VOTING analog); wolf_fan_out_vote dispatches every wolf's message-less binding vote in
parallel (fan_out_vote analog); collect_wolf_votes tallies the plurality target with a random
tiebreak (COLLECT_VOTES analog). A lone wolf skips the talk entirely — a solo discussion is
theater. Speaker order is the surviving_wolves list order, recomputed statelessly from the
wolf channel each pass. Each turn still runs through the shared night engine, so it does
flag-gated retrieval and emits an EvalCase.
"""

import random
from collections import Counter
from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.runtime import Runtime
from langgraph.types import Send

from Agents.state import (
    WolfNightGraph,
)



from Agents.tracing import (
    GraphContext,
)

from Agents.turn import run_memory_informed_night_action
from Agents.prompts import WOLF_NIGHT_DISCUSS, WOLF_NIGHT_VOTE
from Agents.schemas import WolfNightDiscussOutput, WolfNightVoteOutput
from Agents.schemas.turn import ResolvedWolfDiscussion, ResolvedWolfVote
from Agents.schemas.game_events import WolfChannel
from Agents.state import WolfNightState


# The commit contract for both wolf night turns (talk and binding vote): one entry
# appended to the wolf channel, plus the strategy-note map when it changed.
class WolfNightDelta(TypedDict, total=False):
    wolf_channel: list[WolfChannel]
    """One entry: the talk message (vote="") or the binding vote (message="")."""
    agent_strategies: dict[str, str]
    """{player_id: updated strategy note} — present only when the strategy changed."""


# Talk rounds before the binding vote; the vote itself is the round after the last talk round.
WOLF_TALK_ROUNDS = 2
WOLF_VOTE_ROUND = WOLF_TALK_ROUNDS + 1


def _spoken_this_round(state: WolfNightGraph) -> set[str]:
    """Wolves who already spoke in the current talk round tonight — recomputed from the
    channel, never tracked as counters, so the loop stays stateless across passes."""
    return {
        msg.wolf
        for msg in state["wolf_channel"]
        if msg.day == state["current_day"] and msg.round == state["current_round"]
    }


def prepare_wolf_night(state: WolfNightGraph):
    """The scheduler hub (day_scheduler analog): every talk turn loops back here. Commits
    this pass's round — advancing when every wolf has spoken in it; a lone surviving wolf
    jumps straight to the binding vote since there is nothing to discuss."""
    if len(state["surviving_wolves"]) == 1:
        return {"current_round": WOLF_VOTE_ROUND}
    current_round = state.get("current_round", 1)
    if (
        current_round < WOLF_VOTE_ROUND
        and state["surviving_wolves"]
        and _spoken_this_round(state) >= set(state["surviving_wolves"])
    ):
        current_round += 1
    return {"current_round": current_round}


def _wolf_payload(state: WolfNightGraph, wolf: str) -> dict:
    """The per-wolf Send payload (wolf channel + both rosters) — identical for talk and
    vote turns; the receiving node decides what the turn asks for."""
    strategies = state.get("agent_strategies", {})
    return {
        "day_channel": state["day_channel"],
        "day_summaries": state.get("day_summaries", []),
        "wolf_channel": state["wolf_channel"],
        "surviving_villagers": state["surviving_villagers"],
        "surviving_wolves": state["surviving_wolves"],
        "player_id": wolf,
        "player_role": "wolf",
        "human_player": wolf in state["human_players"],
        "current_day": state["current_day"],
        "current_round": state["current_round"],
        "previous_strategy": strategies.get(wolf, ""),
        "strategy_points": "",
    }


def route_wolf_speaker(state: WolfNightGraph):
    """The scheduler hop (route_speaker analog): ONE Send to the next unspoken wolf during
    the talk rounds (surviving_wolves order — sequential, so the later speaker reads the
    earlier one); once the talk is spent, hop to the START_WOLF_VOTE marker."""
    # Wolves extinct (SK kill + lynch can wipe the pack while the game continues): end the
    # subgraph with no kill target — the pre-split fan-out no-oped the same way.
    if not state["surviving_wolves"]:
        return END

    if state["current_round"] >= WOLF_VOTE_ROUND:
        return "START_WOLF_VOTE"

    spoken = _spoken_this_round(state)
    next_speaker = next((w for w in state["surviving_wolves"] if w not in spoken), None)
    if next_speaker is None:
        # Prepare advances the round when every wolf spoke, so reaching here means a stale
        # pass; emit no turn rather than crash the night.
        return []
    return [Send("WOLF_NIGHT_DISCUSS", _wolf_payload(state, next_speaker))]


def start_wolf_vote(state: WolfNightGraph):
    """Phase-marker no-op (START_VOTING analog): the talk is spent, the binding vote begins.
    Also the natural anchor if the pack vote ever needs a wire event."""
    return {}


def wolf_fan_out_vote(state: WolfNightGraph):
    """Every wolf to WOLF_NIGHT_VOTE in parallel (fan_out_vote analog): votes are blind to
    each other — the discussion already happened. Human wolves go to the uncached twin
    (same node body): see the day fan-out for the cache/interrupt rationale."""
    return [Send("WOLF_NIGHT_VOTE_HUMAN" if wolf in state["human_players"]
                 else "WOLF_NIGHT_VOTE", _wolf_payload(state, wolf))
            for wolf in state["surviving_wolves"]]


def collect_wolf_votes(state: WolfNightGraph):
    """Barrier after the parallel vote (COLLECT_VOTES analog): tally the binding votes —
    plurality, random tiebreak. No re-vote loop: wolf_night_vote's random-legal fallback
    guarantees a ballot from every wolf that fanned out."""
    final_votes = [
        msg.vote
        for msg in state["wolf_channel"]
        if msg.round == WOLF_VOTE_ROUND and msg.day == state["current_day"] and msg.vote
    ]
    msg_count = Counter(final_votes)
    max_votes = max(msg_count.values(), default=0)
    candidates = [player for player, votes in msg_count.items() if votes == max_votes]
    return {"wolves_kill_target": random.choice(candidates)} if candidates else {}


def wolf_night_discuss(
    payload: WolfNightState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
) -> WolfNightDelta | None:
    """One wolf's sequential talk turn: a memory-informed message into the wolf channel
    (no vote — the binding vote is its own turn).

    Routed through the same night engine as the single-target roles so it does
    flag-gated retrieval and emits an EvalCase (action_phase "night_action").
    """
    turn = run_memory_informed_night_action(
        payload, config, runtime,
        WOLF_NIGHT_DISCUSS, WolfNightDiscussOutput, "wolf_channel",
    )
    if turn is None:
        return None
    if not isinstance(turn, ResolvedWolfDiscussion):
        raise TypeError(f"wolf discussion resolved to unexpected turn: {turn.kind}")

    updates: WolfNightDelta = {"wolf_channel": [turn.entry]}
    if turn.effects.strategy:
        updates["agent_strategies"] = {
            payload["player_id"]: turn.effects.strategy,
        }
    return updates


def wolf_night_vote(
    payload: WolfNightState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
) -> WolfNightDelta | None:
    """One wolf's binding kill vote after the talk rounds: message-less, cast in parallel
    with the pack — this is the decision the wolf-night EvalCase evaluates."""
    turn = run_memory_informed_night_action(
        payload, config, runtime,
        WOLF_NIGHT_VOTE, WolfNightVoteOutput, "wolf_vote",
    )
    if turn is None:
        return None
    if not isinstance(turn, ResolvedWolfVote):
        raise TypeError(f"wolf vote resolved to unexpected turn: {turn.kind}")

    updates: WolfNightDelta = {"wolf_channel": [turn.entry]}
    if turn.effects.strategy:
        updates["agent_strategies"] = {
            payload["player_id"]: turn.effects.strategy,
        }
    return updates

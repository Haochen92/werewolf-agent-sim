"""Wolf night: the one multi-agent night action — a sequential discussion → parallel kill vote.

A round loop: PREPARE_WOLF_NIGHT → one wolf at a time through WOLF_NIGHT_DISCUSS for the talk
rounds (each speaker sees everything said before their turn) → once the talk rounds are spent,
every wolf fans out to WOLF_NIGHT_VOTE in parallel for the message-less binding vote → collect
tallies the plurality target (random tiebreak). A lone wolf skips the talk entirely — a solo
discussion is theater. Speaker order is the surviving_wolves list order, recomputed statelessly
from the wolf channel each pass (the same recompute-from-channel philosophy as the day scheduler).
Each turn still runs through the shared night engine, so it does flag-gated retrieval and emits
an EvalCase.
"""

import random
from collections import Counter
from typing import Literal

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
from Agents.state import WolfNightState

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
    """Set this pass's round; a lone surviving wolf jumps straight to the binding vote
    since there is nothing to discuss."""
    current_round = state.get("current_round", 1)
    if len(state["surviving_wolves"]) == 1:
        current_round = WOLF_VOTE_ROUND
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
        "human_player": wolf == state["human_player"],
        "current_day": state["current_day"],
        "current_round": state["current_round"],
        "previous_strategy": strategies.get(wolf, ""),
        "strategy_points": "",
    }


def wolf_fan_out(state: WolfNightGraph):
    """Route this pass's turns: during the talk rounds, ONE Send to the next unspoken wolf
    (surviving_wolves order — sequential, so the later speaker reads the earlier one); on the
    vote round, every wolf in parallel to WOLF_NIGHT_VOTE (votes are blind to each other,
    the discussion already happened)."""
    # Wolves extinct (SK kill + lynch can wipe the pack while the game continues): no turns,
    # the subgraph ends with no kill target — the pre-split fan-out no-oped the same way.
    if not state["surviving_wolves"]:
        return []

    if state["current_round"] >= WOLF_VOTE_ROUND:
        return [Send("WOLF_NIGHT_VOTE", _wolf_payload(state, wolf))
                for wolf in state["surviving_wolves"]]

    spoken = _spoken_this_round(state)
    next_speaker = next((w for w in state["surviving_wolves"] if w not in spoken), None)
    if next_speaker is None:
        # Every wolf already spoke this round — collect advances the round, so reaching here
        # means a stale pass; emit no turn rather than crash the night.
        return []
    return [Send("WOLF_NIGHT_DISCUSS", _wolf_payload(state, next_speaker))]


def collect_wolf_night_discussion(state: WolfNightGraph):
    """Barrier after each pass: tally the binding votes once the vote round ran (plurality,
    random tiebreak); during the talk rounds, advance the round only when every wolf has
    spoken in it — otherwise loop back for the next sequential speaker."""
    if state["current_round"] >= WOLF_VOTE_ROUND:
        final_votes = [
            msg.vote
            for msg in state["wolf_channel"]
            if msg.round == WOLF_VOTE_ROUND and msg.day == state["current_day"] and msg.vote
        ]
        msg_count = Counter(final_votes)
        max_votes = max(msg_count.values(), default=0)
        candidates = [player for player, votes in msg_count.items() if votes == max_votes]
        return {"wolves_kill_target": random.choice(candidates)} if candidates else {}
    if _spoken_this_round(state) >= set(state["surviving_wolves"]):
        return {"current_round": state["current_round"] + 1}
    return {}


def check_night_end(state: WolfNightGraph) -> Literal["PREPARE_WOLF_NIGHT", "__end__"]:
    """Loop control: end the wolf night once a kill target is set, else run another
    PREPARE_WOLF_NIGHT pass."""
    if state.get("wolves_kill_target") is not None:
        return END
    return "PREPARE_WOLF_NIGHT"




def wolf_night_discuss(
    payload: WolfNightState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    """One wolf's sequential talk turn: a memory-informed message into the wolf channel
    (no vote — the binding vote is its own turn).

    Routed through the same night engine as the single-target roles so it does
    flag-gated retrieval and emits an EvalCase (action_phase "night_action").
    """
    return run_memory_informed_night_action(
        payload, config, runtime,
        WOLF_NIGHT_DISCUSS, WolfNightDiscussOutput, "wolf_channel",
    )


def wolf_night_vote(
    payload: WolfNightState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    """One wolf's binding kill vote after the talk rounds: message-less, cast in parallel
    with the pack — this is the decision the wolf-night EvalCase evaluates."""
    return run_memory_informed_night_action(
        payload, config, runtime,
        WOLF_NIGHT_VOTE, WolfNightVoteOutput, "wolf_vote",
    )

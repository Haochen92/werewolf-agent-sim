"""Wolf night: the one multi-agent night action — a short parallel discussion → kill vote.

A 2-round loop: PREPARE_WOLF_NIGHT → WOLF_NIGHT_DISCUSS (all wolves in parallel) →
collect → check_night_end, repeating until a kill target is set. Round 1 is open
discussion, round 2 is the binding vote; a lone wolf skips straight to round 2. Each
wolf's turn is still a single memory-informed decision, so it runs through the shared
night engine (see wolf_night_discuss).
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

from Agents.turn import _run_memory_informed_night_action
from Agents.prompts import WOLF_NIGHT_DISCUSS
from Agents.schemas import WolfNightDiscussOutput
from Agents.state import WolfNightState


def prepare_wolf_night(state: WolfNightGraph):
    """Set this pass's discussion round; a lone surviving wolf jumps straight to round 2
    (the vote) since there is nothing to discuss."""
    current_round = state.get("current_round", 1)
    if len(state["surviving_wolves"]) == 1:
        current_round = 2
    return {"current_round": current_round}


def wolf_fan_out(state: WolfNightGraph):
    """Fan every surviving wolf out to WOLF_NIGHT_DISCUSS in parallel, each with the
    shared wolf-night payload (wolf channel + both rosters)."""
    concurrent_nodes = []
    strategies = state.get("agent_strategies", {})

    for wolf in state["surviving_wolves"]:
        is_human = wolf == state["human_player"]
        concurrent_nodes.append(
            Send(
                "WOLF_NIGHT_DISCUSS",
                {
                    "day_channel": state["day_channel"],
                    "day_summaries": state.get("day_summaries", []),
                    "wolf_channel": state["wolf_channel"],
                    "surviving_villagers": state["surviving_villagers"],
                    "surviving_wolves": state["surviving_wolves"],
                    "player_id": wolf,
                    "player_role": "wolf",
                    "human_player": is_human,
                    "current_day": state["current_day"],
                    "current_round": state["current_round"],
                    "previous_strategy": strategies.get(wolf, ""),
                    "strategy_points": "",
                },
            )
        )
    return concurrent_nodes


def collect_wolf_night_discussion(state: WolfNightGraph):
    """Barrier after each discussion round: on the final round (>=2) tally the kill votes
    and pick the plurality target (random tiebreak); otherwise advance to the next round."""
    if state["current_round"] >= 2:
        final_votes = [
            msg.vote
            for msg in state["wolf_channel"]
            if msg.round == 2 and msg.day == state["current_day"]
        ]
        msg_count = Counter(final_votes)
        max_votes = max(msg_count.values(), default=0)
        candidates = [player for player, votes in msg_count.items() if votes == max_votes]
        return {"wolves_kill_target": random.choice(candidates)} if candidates else {}
    return {"current_round": state["current_round"] + 1}


def check_night_end(state: WolfNightGraph) -> Literal["PREPARE_WOLF_NIGHT", "__end__"]:
    """Loop control: end the wolf night once a kill target is set, else run another
    PREPARE_WOLF_NIGHT round."""
    if state.get("wolves_kill_target") is not None:
        return END
    return "PREPARE_WOLF_NIGHT"




def wolf_night_discuss(
    payload: WolfNightState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    """One wolf's night turn: a memory-informed kill-vote into the wolf channel.

    Routed through the same night engine as the single-target roles so it does
    flag-gated retrieval and emits an EvalCase (action_phase "night_action") — that
    is what puts wolf-night decisions into the eval/memory sample, even though wolf
    night is the only *multi-agent* night action.
    """
    return _run_memory_informed_night_action(
        payload, config, runtime,
        WOLF_NIGHT_DISCUSS, WolfNightDiscussOutput, "wolf_channel",
    )



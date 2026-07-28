from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.tracing import GraphContext

# Day actor nodes (thin wrappers over the shared runtime engine).
from Agents.turn import run_memory_informed_action
from Agents.prompts import (
    HEALER_DAY_DISCUSS,
    HEALER_DAY_VOTE,
    INVESTIGATOR_DAY_DISCUSS,
    INVESTIGATOR_DAY_VOTE,
    SERIAL_KILLER_DAY_DISCUSS,
    SERIAL_KILLER_DAY_VOTE,
    VIGILANTE_DAY_DISCUSS,
    VIGILANTE_DAY_VOTE,
    VILLAGER_DAY_DISCUSS,
    VILLAGER_DAY_VOTE,
    WOLF_DAY_DISCUSS,
    WOLF_DAY_VOTE,
)
from typing import TypedDict, cast

from Agents.schemas import DayChannel, DayDiscussOutput, DayVote, DayVoteOutput
from Agents.state import HealerDayState, InvestigatorDayState, VillagerDayState, WolfDayState

# The Send-payload shape: one of the role-gated payload TypedDicts built by flow.py's
# builders (documentation-only — Send payloads are not runtime-validated; see state/day.py).
DayActorPayload = VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState


# The commit contracts: exactly what a turn's superstep can fold into graph state (shape
# decided in turn/resolve._attach_agent_reasoning; documented at run_memory_informed_action).
# Together with DayActorPayload these make the node signature the full turn contract:
# payload in, delta out — everything else in the call chain is implementation.
class DiscussDelta(TypedDict, total=False):
    day_channel: list[DayChannel]
    """One entry: the speech, or a pass marker (voluntary or novelty-gated)."""
    agent_strategies: dict[str, str]
    """{player_id: updated strategy note} — present only when the strategy changed."""


class VoteDelta(TypedDict, total=False):
    day_votes: list[DayVote]
    """One vote (random-target fallback if every retry failed)."""
    agent_strategies: dict[str, str]
    """{player_id: updated strategy note} — present only when the strategy changed."""


# Every role's day-discuss / day-vote turn makes the identical call into the shared
# engine — only the prompt differs. So the graph registers ONE generic node per phase
# and the role rides the Send payload (player_role, already attached by the role-gated
# payload builders in flow.py). Role-specific behaviour is data (the prompt tables),
# not code: adding a role = one prompt entry per phase.
DISCUSS_PROMPTS: dict[str, str] = {
    "villager": VILLAGER_DAY_DISCUSS,
    "healer": HEALER_DAY_DISCUSS,
    "wolf": WOLF_DAY_DISCUSS,
    "investigator": INVESTIGATOR_DAY_DISCUSS,
    "serial_killer": SERIAL_KILLER_DAY_DISCUSS,
    "vigilante": VIGILANTE_DAY_DISCUSS,
}

VOTE_PROMPTS: dict[str, str] = {
    "villager": VILLAGER_DAY_VOTE,
    "healer": HEALER_DAY_VOTE,
    "wolf": WOLF_DAY_VOTE,
    "investigator": INVESTIGATOR_DAY_VOTE,
    "serial_killer": SERIAL_KILLER_DAY_VOTE,
    "vigilante": VIGILANTE_DAY_VOTE,
}


# The payload is the explicitly-built dict from build_speaker_send / fan_out_day (role-gated
# there — the leak boundary), not raw graph state.
def discuss(
    payload: DayActorPayload,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
) -> DiscussDelta | None:
    return cast(DiscussDelta | None, run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        DISCUSS_PROMPTS[payload["player_role"]],
        DayDiscussOutput,
        "day_channel",
    ))


def vote(
    payload: DayActorPayload,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
) -> VoteDelta | None:
    return cast(VoteDelta | None, run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        VOTE_PROMPTS[payload["player_role"]],
        DayVoteOutput,
        "day_votes",
    ))

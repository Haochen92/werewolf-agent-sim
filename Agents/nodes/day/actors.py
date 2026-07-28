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
from Agents.schemas import DayDiscussOutput, DayVoteOutput
from Agents.state import HealerDayState, InvestigatorDayState, VillagerDayState, WolfDayState

# The Send-payload shape: one of the role-gated payload TypedDicts built by flow.py's
# builders (documentation-only — Send payloads are not runtime-validated; see state/day.py).
DayActorPayload = VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState


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
):
    return run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        DISCUSS_PROMPTS[payload["player_role"]],
        DayDiscussOutput,
        "day_channel",
    )


def vote(
    payload: DayActorPayload,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        VOTE_PROMPTS[payload["player_role"]],
        DayVoteOutput,
        "day_votes",
    )

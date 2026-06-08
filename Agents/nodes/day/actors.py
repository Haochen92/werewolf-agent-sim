from logging import getLogger as _getLogger
logger = _getLogger(__name__)


from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime




from Agents.tracing import (
    GraphContext,
)

# Day actor nodes (thin wrappers over the shared runtime engine).
from Agents.engine import _run_memory_informed_action
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
def villager_discuss(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        VILLAGER_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def healer_discuss(
    payload: HealerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        HEALER_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def wolf_discuss(
    payload: WolfDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        WOLF_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def investigator_discuss(
    payload: InvestigatorDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        INVESTIGATOR_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def villager_vote(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        VILLAGER_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def healer_vote(
    payload: HealerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        HEALER_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def wolf_vote(
    payload: WolfDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        WOLF_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def investigator_vote(
    payload: InvestigatorDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        INVESTIGATOR_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def serial_killer_discuss(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        SERIAL_KILLER_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def vigilante_discuss(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        VIGILANTE_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def serial_killer_vote(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        SERIAL_KILLER_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def vigilante_vote(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        VIGILANTE_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )



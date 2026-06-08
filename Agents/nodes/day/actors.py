from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.tracing import GraphContext

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


# Every role's day-discuss / day-vote node makes the identical call into the
# shared engine — only the prompt differs (the state-type hint is cosmetic). The
# nodes are reached via Send(f"{role}_discuss", payload) / Send(f"{role}_vote",
# payload) with an explicitly-built payload, so the first-arg annotation is
# documentation, not input filtering. So we build them from one factory per phase
# rather than hand-repeating 12 near-identical bodies. Adding a role = one line.
def _make_discuss_node(prompt: str, state_type=VillagerDayState):
    def discuss(
        payload: state_type,
        config: RunnableConfig,
        runtime: Runtime[GraphContext],
    ):
        return _run_memory_informed_action(
            payload,
            config,
            runtime,
            "day_discussion",
            prompt,
            DayDiscussOutput,
            "day_channel",
        )

    return discuss


def _make_vote_node(prompt: str, state_type=VillagerDayState):
    def vote(
        payload: state_type,
        config: RunnableConfig,
        runtime: Runtime[GraphContext],
    ):
        return _run_memory_informed_action(
            payload,
            config,
            runtime,
            "day_vote",
            prompt,
            DayVoteOutput,
            "day_votes",
        )

    return vote


# Discussion nodes per role.
villager_discuss = _make_discuss_node(VILLAGER_DAY_DISCUSS, VillagerDayState)
healer_discuss = _make_discuss_node(HEALER_DAY_DISCUSS, HealerDayState)
wolf_discuss = _make_discuss_node(WOLF_DAY_DISCUSS, WolfDayState)
investigator_discuss = _make_discuss_node(INVESTIGATOR_DAY_DISCUSS, InvestigatorDayState)
serial_killer_discuss = _make_discuss_node(SERIAL_KILLER_DAY_DISCUSS)  # uses VillagerDayState
vigilante_discuss = _make_discuss_node(VIGILANTE_DAY_DISCUSS)  # uses VillagerDayState

# Vote nodes per role.
villager_vote = _make_vote_node(VILLAGER_DAY_VOTE, VillagerDayState)
healer_vote = _make_vote_node(HEALER_DAY_VOTE, HealerDayState)
wolf_vote = _make_vote_node(WOLF_DAY_VOTE, WolfDayState)
investigator_vote = _make_vote_node(INVESTIGATOR_DAY_VOTE, InvestigatorDayState)
serial_killer_vote = _make_vote_node(SERIAL_KILLER_DAY_VOTE)  # uses VillagerDayState
vigilante_vote = _make_vote_node(VIGILANTE_DAY_VOTE)  # uses VillagerDayState

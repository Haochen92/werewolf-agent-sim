"""Investigator night actor node."""

from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.prompts import INVESTIGATOR_NIGHT
from Agents.schemas import InvestigatorOutput
from Agents.schemas.turn import ResolvedInvestigatorTarget
from Agents.state import InvestigatorNightGraph
from Agents.tracing import GraphContext
from Agents.turn import run_memory_informed_night_action


class InvestigatorDelta(TypedDict, total=False):
    investigator_target: str
    updated_strategy: str


def investigator_act(
    payload: InvestigatorNightGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
) -> InvestigatorDelta | None:
    turn = run_memory_informed_night_action(
        payload,
        config,
        runtime,
        INVESTIGATOR_NIGHT,
        InvestigatorOutput,
        "investigator_target",
    )
    if turn is None:
        return None
    if not isinstance(turn, ResolvedInvestigatorTarget):
        raise TypeError(f"investigator action resolved to unexpected turn: {turn.kind}")

    updates: InvestigatorDelta = {"investigator_target": turn.entry}
    if turn.effects.strategy:
        updates["updated_strategy"] = turn.effects.strategy
    return updates

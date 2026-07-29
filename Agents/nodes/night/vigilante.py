"""Vigilante night actor node."""

from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.prompts import VIGILANTE_NIGHT
from Agents.schemas import VigilanteOutput
from Agents.schemas.turn import ResolvedVigilanteTarget
from Agents.state import VigilanteNightGraph
from Agents.tracing import GraphContext
from Agents.turn import run_memory_informed_night_action


class VigilanteDelta(TypedDict, total=False):
    vigilante_target: str
    updated_strategy: str


def vigilante_act(
    payload: VigilanteNightGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
) -> VigilanteDelta | None:
    turn = run_memory_informed_night_action(
        payload,
        config,
        runtime,
        VIGILANTE_NIGHT,
        VigilanteOutput,
        "vigilante_target",
    )
    if turn is None:
        return None
    if not isinstance(turn, ResolvedVigilanteTarget):
        raise TypeError(f"vigilante action resolved to unexpected turn: {turn.kind}")

    updates: VigilanteDelta = {"vigilante_target": turn.entry}
    if turn.effects.strategy:
        updates["updated_strategy"] = turn.effects.strategy
    return updates

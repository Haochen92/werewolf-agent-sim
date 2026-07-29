"""Serial-killer night actor node."""

from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.prompts import SERIAL_KILLER_NIGHT
from Agents.schemas import SerialKillerOutput
from Agents.schemas.turn import ResolvedSerialKillerTarget
from Agents.state import SerialKillerNightGraph
from Agents.tracing import GraphContext
from Agents.turn import run_memory_informed_night_action


class SerialKillerDelta(TypedDict, total=False):
    serial_killer_target: str
    updated_strategy: str


def serial_killer_act(
    payload: SerialKillerNightGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
) -> SerialKillerDelta | None:
    turn = run_memory_informed_night_action(
        payload,
        config,
        runtime,
        SERIAL_KILLER_NIGHT,
        SerialKillerOutput,
        "serial_killer_target",
    )
    if turn is None:
        return None
    if not isinstance(turn, ResolvedSerialKillerTarget):
        raise TypeError(f"serial-killer action resolved to unexpected turn: {turn.kind}")

    updates: SerialKillerDelta = {"serial_killer_target": turn.entry}
    if turn.effects.strategy:
        updates["updated_strategy"] = turn.effects.strategy
    return updates

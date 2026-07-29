"""Healer night actor node."""

from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.prompts import HEALER_NIGHT
from Agents.schemas import HealerOutput
from Agents.schemas.turn import ResolvedHealerTarget
from Agents.state import HealerNightGraph
from Agents.tracing import GraphContext
from Agents.turn import run_memory_informed_night_action


class HealerDelta(TypedDict, total=False):
    healer_target: str
    updated_strategy: str


def healer_act(
    payload: HealerNightGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
) -> HealerDelta | None:
    turn = run_memory_informed_night_action(
        payload,
        config,
        runtime,
        HEALER_NIGHT,
        HealerOutput,
        "healer_target",
    )
    if turn is None:
        return None
    if not isinstance(turn, ResolvedHealerTarget):
        raise TypeError(f"healer action resolved to unexpected turn: {turn.kind}")

    updates: HealerDelta = {"healer_target": turn.entry}
    if turn.effects.strategy:
        updates["updated_strategy"] = turn.effects.strategy
    return updates

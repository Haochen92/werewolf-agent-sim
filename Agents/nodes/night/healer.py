from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.engine import _run_memory_informed_night_action
from Agents.prompts import HEALER_NIGHT
from Agents.schemas import HealerOutput
from Agents.state import HealerNightGraph
from Agents.tracing import GraphContext


def healer_act(
    payload: HealerNightGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_night_action(
        payload, config, runtime, HEALER_NIGHT, HealerOutput, "healer_target"
    )



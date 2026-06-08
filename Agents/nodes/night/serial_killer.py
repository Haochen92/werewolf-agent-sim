from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.engine import _run_memory_informed_night_action
from Agents.prompts import SERIAL_KILLER_NIGHT
from Agents.schemas import SerialKillerOutput
from Agents.state import SerialKillerNightGraph
from Agents.tracing import GraphContext


def serial_killer_act(
    payload: SerialKillerNightGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_night_action(
        payload, config, runtime,
        SERIAL_KILLER_NIGHT, SerialKillerOutput, "serial_killer_target",
    )



from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.engine import _run_memory_informed_night_action
from Agents.prompts import VIGILANTE_NIGHT
from Agents.schemas import VigilanteOutput
from Agents.state import VigilanteNightGraph
from Agents.tracing import GraphContext


def vigilante_act(
    payload: VigilanteNightGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_night_action(
        payload, config, runtime, VIGILANTE_NIGHT, VigilanteOutput, "vigilante_target"
    )

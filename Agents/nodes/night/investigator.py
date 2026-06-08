from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.nodes.runtime import _run_memory_informed_night_action
from Agents.prompts import INVESTIGATOR_NIGHT
from Agents.schemas import InvestigatorOutput
from Agents.state import InvestigatorNightGraph
from Agents.tracing import GraphContext


def investigator_act(
    payload: InvestigatorNightGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_night_action(
        payload, config, runtime,
        INVESTIGATOR_NIGHT, InvestigatorOutput, "investigator_target",
    )



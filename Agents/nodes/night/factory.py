"""Factory for single-actor night nodes.

Healer / investigator / serial-killer / vigilante night nodes are each the same
call into the shared engine — only the prompt, output schema, output key, and
(cosmetic) state-type hint differ. They keep their own per-role files so a role
whose night logic later diverges (the way wolf already does, with a multi-node
discussion flow) can replace its one-line binding with a real function in place.
This factory removes the repeated wrapper boilerplate from the common case.

Nodes are reached via Send(f"{role}_act", payload) with an explicit payload, so
the first-arg annotation is documentation, not input filtering.
"""

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from pydantic import BaseModel

from Agents.turn import _run_memory_informed_night_action
from Agents.tracing import GraphContext


def make_night_act_node(
    prompt,
    output_schema: type[BaseModel],
    output_key: str,
    state_type,
):
    def act(
        payload: state_type,
        config: RunnableConfig,
        runtime: Runtime[GraphContext],
    ):
        return _run_memory_informed_night_action(
            payload, config, runtime, prompt, output_schema, output_key
        )

    return act

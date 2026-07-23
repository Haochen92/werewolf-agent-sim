import os
from typing import Any

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from Agents.config import RunConfig, build_runnable_config
from Agents.config.run import (  # noqa: F401 — re-exported for backward compat
    DEFAULT_FILTERING_CONFIG,
    DEFAULT_MEMORY_CONFIG,
    DEFAULT_RERANKING_CONFIG,
    DEFAULT_RETRIEVAL_TYPES_CONFIG,
    DEFAULT_SP_EXPLORATION_SLOT,
    DEFAULT_SP_PROVEN_TIERING,
)
from Agents.run_fingerprint import git_revision, runtime_fingerprint
from Agents.schemas.metrics import (  # noqa: F401 — re-exported for backward compat
    DayResolutionMetric,
    GraphContext,
    Metrics,
    NightResolutionMetric,
)


# Stamp every trace with the code version via Langfuse's first-class `release`
# field (filterable in the UI). Must be set before the first get_client() —
# the OTel resource is created once per process. setdefault keeps an explicit
# LANGFUSE_RELEASE override working.
os.environ.setdefault("LANGFUSE_RELEASE", git_revision()["git_commit"])

langfuse = get_client()


def create_langfuse_handler() -> CallbackHandler:
    """The Langfuse LangChain callback that nests a run under the current trace. A factory (not a
    module singleton) so config assembly injects observability rather than importing it."""
    return CallbackHandler()


def build_game_config(
    memory_config: dict | None = None,
    session_id: str | None = None,
    game_config: Any = None,
    memory_persistence_config: Any = None,
    reranking_config: dict | None = None,
    filtering_config: dict | None = None,
    retrieval_types_config: dict | None = None,
    game_id: str | None = None,
    sp_proven_tiering: bool | None = None,
    sp_exploration_slot: bool | None = None,
) -> dict:
    """Backward-compat entry point: compose a RunConfig from loose options and adapt it to a root
    RunnableConfig, attaching the Langfuse handler + runtime fingerprint. New code should build a
    RunConfig and call Agents.config.build_runnable_config directly (injecting these two)."""
    run = RunConfig.from_options(
        memory_config=memory_config,
        session_id=session_id,
        game_config=game_config,
        memory_persistence_config=memory_persistence_config,
        reranking_config=reranking_config,
        filtering_config=filtering_config,
        retrieval_types_config=retrieval_types_config,
        game_id=game_id,
        sp_proven_tiering=sp_proven_tiering,
        sp_exploration_slot=sp_exploration_slot,
    )
    return build_runnable_config(
        run,
        callbacks=[create_langfuse_handler()],
        metadata={"runtime_fingerprint": runtime_fingerprint()},
    )


def flush():
    langfuse.flush()

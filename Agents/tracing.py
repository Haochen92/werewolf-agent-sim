import os

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from Agents.run_fingerprint import git_revision
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
    module singleton) so the entry point injects observability into build_runnable_config rather
    than the config layer importing tracing."""
    return CallbackHandler()


def flush():
    langfuse.flush()

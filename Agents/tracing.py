import os
import threading

from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from Agents.run_fingerprint import git_revision
from Agents.schemas.metrics import (  # noqa: F401 — re-exported for backward compat
    DayResolutionMetric,
    GraphContext,
    Metrics,
    NightResolutionMetric,
)


_client: Langfuse | None = None
_client_lock = threading.Lock()


def init_tracing() -> Langfuse:
    """Build the process's Langfuse client, once. Entry points call this at start-up, after
    their settings are loaded.

    Nothing is built when this module is imported: the client reads its keys once, at creation,
    and one built before the entry point has loaded its settings is disabled without an error.
    The first client built also fixes the release for every later one in the process, so the
    code version is passed here; an explicit LANGFUSE_RELEASE still wins.

    Returns:
        The one client, built on the first call and returned as is on later calls.
    """
    global _client
    with _client_lock:
        if _client is None:
            load_dotenv()  # a script that loaded no .env of its own still gets its keys
            release = os.environ.get("LANGFUSE_RELEASE") or git_revision()["git_commit"]
            _client = Langfuse(release=release)
        return _client


def get_langfuse() -> Langfuse:
    """The process's Langfuse client. Built here on first use when no entry point called
    init_tracing() (one-off scripts, tests)."""
    return _client if _client is not None else init_tracing()


def create_langfuse_handler(*, trace_context: dict | None = None) -> CallbackHandler:
    """The Langfuse LangChain callback that nests a run under the current trace. A factory (not a
    module singleton) so the entry point injects observability into build_runnable_config rather
    than the config layer importing tracing."""
    # The handler looks up the process's client itself and builds a default one if there is none,
    # which would fix the release as empty. So this module's client comes first.
    get_langfuse()
    return CallbackHandler(trace_context=trace_context)


def flush():
    get_langfuse().flush()

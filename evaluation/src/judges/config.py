"""Shared LLM configuration for the evaluation judges.

One home for the default judge model and the factory that builds a judge LLM,
so the model choice isn't copy-pasted across every judge module. A judge that
needs a different model overrides ``DEFAULT_JUDGE_MODEL`` locally (e.g. the
situation-summary judge runs on a stronger model).
"""

from __future__ import annotations

from Agents.llm_factory import create_chat_model

# The standard judge model. Judge modules import this as their default; the few
# that diverge set their own ``DEFAULT_*_JUDGE_MODEL`` to a different literal.
DEFAULT_JUDGE_MODEL = "gemini-2.5-pro"


def get_judge_llm(model: str = DEFAULT_JUDGE_MODEL, **kwargs):
    """Build the LLM a judge runs on — the single chokepoint for judge LLM
    construction. ``**kwargs`` pass through to ``create_chat_model`` (e.g.
    ``thinking_level``)."""
    return create_chat_model(model, **kwargs)

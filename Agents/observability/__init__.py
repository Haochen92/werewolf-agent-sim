"""Observability plumbing shared by the game runtime and the eval read side.

Pure modules only — importing this package must NOT initialize the Langfuse
client (that side effect lives in ``Agents.tracing``), so evaluation code can
import span names and the case sink without touching tracing globals.
"""

from Agents.observability.span_names import (
    ACTION_EVAL_SPAN_PREFIX,
    DAY_SUMMARY_SPAN_PREFIX,
    DEDUP_LLM_RUN_NAMES,
    DEDUP_SPAN_PREFIX,
    EXTRACTION_SPAN_PREFIX,
    action_eval_span_name,
    day_summary_span_name,
    dedup_span_name,
    extraction_role_run_name,
    extraction_span_name,
)

__all__ = [
    "ACTION_EVAL_SPAN_PREFIX",
    "DAY_SUMMARY_SPAN_PREFIX",
    "DEDUP_LLM_RUN_NAMES",
    "DEDUP_SPAN_PREFIX",
    "EXTRACTION_SPAN_PREFIX",
    "action_eval_span_name",
    "day_summary_span_name",
    "dedup_span_name",
    "extraction_role_run_name",
    "extraction_span_name",
]

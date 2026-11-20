"""Observability plumbing shared by the game runtime and the eval read side.

Pure modules only — importing this package must NOT build the Langfuse client
(``Agents.tracing`` builds it, by a call), so evaluation code can import span
names and the case sink without touching tracing globals.
"""

from Agents.observability.case_sink import EvalCaseSink, freeze_case
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
    "EvalCaseSink",
    "freeze_case",
    "action_eval_span_name",
    "day_summary_span_name",
    "dedup_span_name",
    "extraction_role_run_name",
    "extraction_span_name",
]

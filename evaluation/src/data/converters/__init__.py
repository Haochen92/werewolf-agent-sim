"""Span-dict → typed ``*Case`` converters (one per case type; pure, no I/O).

A source (``sources/sidecar.py`` or ``sources/langfuse.py``) produces normalized
span dicts; each function here validates one into its typed case, returning
``None`` for spans that carry no case of that type. Re-exported so callers can
``from evaluation.src.data.converters import eval_case_from_span`` without knowing
which file it lives in.
"""

from evaluation.src.data.converters.agent_decision import eval_case_from_span
from evaluation.src.data.converters.day_summary import day_summary_case_from_span
from evaluation.src.data.converters.dedup import dedup_case_from_span
from evaluation.src.data.converters.extraction import extraction_case_from_span

__all__ = [
    "eval_case_from_span",
    "extraction_case_from_span",
    "dedup_case_from_span",
    "day_summary_case_from_span",
]

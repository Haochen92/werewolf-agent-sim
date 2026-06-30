"""Convert agent-decision spans into the frozen ``EvalCase`` format.

An ``EvalCase`` freezes one agent decision (day message / day vote / night
action) — the richest case type. Live evaluation expects modern spans whose
output carries an ``eval_case`` payload; older span formats remain in
``evaluation/src/archive/legacy_cases.py`` for audit history but are no longer
accepted by the active builder.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from Agents.schemas.evaluation import EvalCase


def eval_case_from_span(span: dict[str, Any]) -> EvalCase | None:
    """Return an ``EvalCase`` from a modern Langfuse span, or ``None``."""
    output = span.get("output") if isinstance(span.get("output"), dict) else {}
    if isinstance(output.get("eval_case"), dict):
        return _case_from_payload(output["eval_case"], span)
    return None


def _case_from_payload(payload: dict[str, Any], span: dict[str, Any]) -> EvalCase | None:
    """Validate an embedded ``eval_case`` payload and fill span IDs if needed."""
    enriched = {
        **payload,
        "trace_id": payload.get("trace_id") or span.get("trace_id") or "",
        "observation_id": payload.get("observation_id") or span.get("id") or "",
        "span_name": payload.get("span_name") or span.get("name") or "",
    }
    try:
        return EvalCase.model_validate(enriched)
    except ValidationError as exc:
        print(f"  Skipping invalid eval_case payload: {exc}")
        return None

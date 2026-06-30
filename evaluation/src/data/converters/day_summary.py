"""Convert Langfuse day-summary spans into frozen ``DaySummaryCase`` records."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from Agents.schemas.evaluation import DaySummaryCase


def day_summary_case_from_span(span: dict[str, Any]) -> DaySummaryCase | None:
    """Return a ``DaySummaryCase`` from a Langfuse span, or ``None``."""
    output = span.get("output") if isinstance(span.get("output"), dict) else {}
    if isinstance(output.get("day_summary_case"), dict):
        return _case_from_payload(output["day_summary_case"], span)
    return None


def _case_from_payload(
    payload: dict[str, Any], span: dict[str, Any]
) -> DaySummaryCase | None:
    enriched = {
        **payload,
        "trace_id": payload.get("trace_id") or span.get("trace_id") or "",
        "observation_id": payload.get("observation_id") or span.get("id") or "",
        "span_name": payload.get("span_name") or span.get("name") or "",
    }
    try:
        return DaySummaryCase.model_validate(enriched)
    except ValidationError as exc:
        print(f"  Skipping invalid day_summary_case payload: {exc}")
        return None

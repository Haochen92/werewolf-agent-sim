"""Convert Langfuse dedup spans into frozen ``DedupCase`` records."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from Agents.schemas.evaluation import DedupCase


def dedup_case_from_span(span: dict[str, Any]) -> DedupCase | None:
    """Return a ``DedupCase`` from a Langfuse span, or ``None``."""
    output = span.get("output") if isinstance(span.get("output"), dict) else {}
    if isinstance(output.get("dedup_case"), dict):
        return _case_from_payload(output["dedup_case"], span)
    return None


def _case_from_payload(
    payload: dict[str, Any], span: dict[str, Any]
) -> DedupCase | None:
    enriched = {
        **payload,
        "trace_id": payload.get("trace_id") or span.get("trace_id") or "",
        "observation_id": payload.get("observation_id") or span.get("id") or "",
        "span_name": payload.get("span_name") or span.get("name") or "",
    }
    try:
        return DedupCase.model_validate(enriched)
    except ValidationError as exc:
        print(f"  Skipping invalid dedup_case payload: {exc}")
        return None

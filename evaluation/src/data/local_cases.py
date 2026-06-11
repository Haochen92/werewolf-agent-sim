"""Local eval-case source: read per-game sidecars written by ``run_batch``.

``run_batch`` persists every game's eval cases to
``batch_results/eval_cases/<session_id>/<game_id>.jsonl`` (pointer in the batch
record's ``eval_cases_path``) as the SAME normalized span dicts the Langfuse
fetch layer produces — so the ``*_case_from_span`` converters apply verbatim and
a frozen-set build needs no Langfuse read at all (no 422s, no truncation, no
span-name collisions). This is the preferred source; the Langfuse fetchers in
``langfuse.py`` remain for games that predate local emission.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from Agents.observability import (
    ACTION_EVAL_SPAN_PREFIX,
    DAY_SUMMARY_SPAN_PREFIX,
    DEDUP_SPAN_PREFIX,
    EXTRACTION_SPAN_PREFIX,
)
from Agents.schemas.evaluation import (
    DaySummaryCase,
    DedupCase,
    EvalCase,
    ExtractionCase,
)
from evaluation.src.core.settings import REPO_ROOT
from evaluation.src.data.cases import eval_case_from_span
from evaluation.src.data.day_summary_cases import day_summary_case_from_span
from evaluation.src.data.dedup_cases import dedup_case_from_span
from evaluation.src.data.extraction_cases import extraction_case_from_span


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number} of {path}: {exc}"
                ) from exc
    return rows


def read_local_spans(batch_results_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Follow each batch record's ``eval_cases_path`` pointer and return the
    span dicts grouped by trace_id (insertion-ordered = batch order).

    Records without a pointer (errored games, or batches predating local
    emission) are skipped with a warning — fall back to the Langfuse source
    for those.
    """
    if not batch_results_path.exists():
        raise FileNotFoundError(f"Batch results file not found: {batch_results_path}")

    by_trace: dict[str, list[dict[str, Any]]] = {}
    skipped = 0
    for record in _read_jsonl(batch_results_path):
        pointer = record.get("eval_cases_path")
        if not pointer:
            if record.get("status") == "success":
                skipped += 1
            continue
        sidecar = REPO_ROOT / pointer
        if not sidecar.exists():
            print(f"WARNING: eval-case sidecar missing, skipping game: {sidecar}")
            skipped += 1
            continue
        spans = _read_jsonl(sidecar)
        trace_id = record.get("trace_id") or (
            spans[0].get("trace_id") if spans else None
        )
        if not trace_id:
            print(f"WARNING: no trace_id for sidecar, skipping: {sidecar}")
            skipped += 1
            continue
        by_trace.setdefault(trace_id, []).extend(spans)

    if skipped:
        print(
            f"WARNING: skipped {skipped} game(s) without a local eval-case "
            "sidecar (predates local emission? use a Langfuse source for those)."
        )
    return by_trace


def _spans_with_prefix(
    spans: list[dict[str, Any]], prefix: str
) -> list[dict[str, Any]]:
    return [s for s in spans if str(s.get("name", "")).startswith(prefix)]


class LocalCaseSource:
    """Per-trace case access over the local sidecars, mirroring the
    ``fetch_*_cases(trace_id)`` contract of the Langfuse fetch layer so the
    builders can swap sources with a one-line branch."""

    def __init__(self, batch_results_path: Path) -> None:
        self._by_trace = read_local_spans(batch_results_path)

    def trace_ids(self) -> list[str]:
        return list(self._by_trace)

    def _cases(self, trace_id: str, prefix: str, converter: Any) -> list[Any]:
        spans = _spans_with_prefix(self._by_trace.get(trace_id, []), prefix)
        return [case for case in map(converter, spans) if case]

    def eval_cases(self, trace_id: str) -> list[EvalCase]:
        return self._cases(trace_id, ACTION_EVAL_SPAN_PREFIX, eval_case_from_span)

    def extraction_cases(self, trace_id: str) -> list[ExtractionCase]:
        return self._cases(trace_id, EXTRACTION_SPAN_PREFIX, extraction_case_from_span)

    def dedup_cases(self, trace_id: str) -> list[DedupCase]:
        return self._cases(trace_id, DEDUP_SPAN_PREFIX, dedup_case_from_span)

    def day_summary_cases(self, trace_id: str) -> list[DaySummaryCase]:
        return self._cases(
            trace_id, DAY_SUMMARY_SPAN_PREFIX, day_summary_case_from_span
        )

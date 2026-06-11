"""Langfuse evaluation pipeline.

This module implements a top-down pipeline for extracting evaluation cases
from Langfuse traces and pushing judge scores back:

    Entry Points (session IDs)
        → Trace Resolution (session → trace IDs)
            → Observation Extraction (trace → eval spans)
                → EvalCase Construction (span → structured case)
                    → Score Push (judge results → Langfuse scores)

Each layer narrows the data: broad session identifiers are resolved into
specific trace IDs, which yield observations, which are filtered to
evaluation spans, which are converted to EvalCase objects for judging.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from evaluation.src.core.settings import load_project_env

load_project_env()

from langfuse import get_client  # noqa: E402

from Agents.observability import (  # noqa: E402
    ACTION_EVAL_SPAN_PREFIX,
    DAY_SUMMARY_SPAN_PREFIX,
    DEDUP_LLM_RUN_NAMES,
    DEDUP_SPAN_PREFIX,
    EXTRACTION_SPAN_PREFIX,
)
from Agents.schemas.evaluation import (  # noqa: E402
    DaySummaryCase,
    DedupCase,
    EvalCase,
    ExtractionCase,
)
from evaluation.src.data.cases import eval_case_from_span  # noqa: E402
from evaluation.src.data.day_summary_cases import day_summary_case_from_span  # noqa: E402
from evaluation.src.data.dedup_cases import dedup_case_from_span  # noqa: E402
from evaluation.src.data.extraction_cases import extraction_case_from_span  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Version tag attached to every score pushed by this module.  Bump this when
# the judge prompt or scoring rubric changes so that old and new scores can
# be distinguished in Langfuse dashboards.
EVAL_VERSION = "retrieval_judge_v2"

# The span-name prefixes that mark evaluation spans are shared with the
# producers via Agents.observability (imported above) — single source of truth.

# The four score dimensions the judge produces for each eval span.
SCORE_NAMES = [
    "summary_quality",
    "retrieval_relevance",
    "strategy_application",
    "grounding",
]

# ---------------------------------------------------------------------------
# Langfuse client
# ---------------------------------------------------------------------------

langfuse = get_client()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _require_langfuse_api() -> Any:
    """Return the low-level Langfuse API client (available in langfuse 3.x).

    Raises RuntimeError with a human-readable message if the client was not
    initialised properly (missing env vars, wrong SDK version, etc.).
    """
    api = getattr(langfuse, "api", None)
    if api is None:
        raise RuntimeError(
            "Langfuse API client is unavailable. Check LANGFUSE_PUBLIC_KEY, "
            "LANGFUSE_SECRET_KEY, and LANGFUSE_HOST in .env."
        )
    return api


def _field(obj: Any, name: str, default: Any = None) -> Any:
    """Read a field from a Fern/Pydantic model *or* a plain dict.

    The Langfuse SDK sometimes returns typed objects and sometimes plain
    dicts depending on the endpoint and SDK version.  This wrapper lets
    the rest of the code stay agnostic.
    """
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    """Remove duplicates from a list while keeping the original order."""
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


# ---------------------------------------------------------------------------
# Layer 1 — Entry points: obtain session IDs
#
# Three ways to seed the pipeline.  Each returns a list of session IDs that
# the next layer will resolve into trace IDs.
# ---------------------------------------------------------------------------


def read_session_ids_from_batch_results(path: Path) -> list[str]:
    """Read session IDs from a ``run_batch`` JSONL output file.

    Each non-empty line in the file must be a valid JSON object.  Objects
    that contain a ``session_id`` key contribute that value to the result.

    Raises:
        FileNotFoundError: if *path* does not exist.
        ValueError: if *path* is not a file or contains invalid JSON.
    """
    if not path.exists():
        raise FileNotFoundError(f"Batch results file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Batch results path is not a file: {path}")

    session_ids: list[str] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number} of {path}: {exc}"
                ) from exc
            session_id = record.get("session_id")
            if session_id:
                session_ids.append(session_id)

    return _dedupe_preserving_order(session_ids)


# ---------------------------------------------------------------------------
# Layer 2 — Trace resolution: session IDs → trace IDs
#
# Given one or more session IDs (from Layer 1), these functions page through
# the Langfuse API to collect every associated trace ID.
# ---------------------------------------------------------------------------


def _trace_ids_from_trace_page(traces: Any) -> list[str]:
    """Extract non-empty trace IDs from a single page of trace list results."""
    return [
        trace_id
        for trace_id in (_field(trace, "id") for trace in _field(traces, "data", []))
        if trace_id
    ]


def fetch_trace_ids_for_session_id(session_id: str) -> list[str]:
    """Fetch all trace IDs belonging to one exact Langfuse session ID."""
    return fetch_trace_ids_for_session_ids([session_id])


def fetch_trace_ids_for_session_ids(session_ids: list[str]) -> list[str]:
    """Fetch all trace IDs belonging to the given Langfuse session IDs.

    Deduplicates both the input session IDs and the collected trace IDs.
    Pages through ``api.trace.list()`` for each session.
    """
    api = _require_langfuse_api()
    trace_ids: list[str] = []

    for session_id in _dedupe_preserving_order(session_ids):
        page = 1
        limit = 50

        while True:
            traces = api.trace.list(page=page, limit=limit, session_id=session_id)
            data = _field(traces, "data", [])
            if not data:
                break

            trace_ids.extend(_trace_ids_from_trace_page(traces))

            # Stop when we've reached the last page.
            meta = _field(traces, "meta")
            total_pages = _field(meta, "total_pages", page)
            if page >= total_pages or len(data) < limit:
                break
            page += 1

    return _dedupe_preserving_order(trace_ids)


def fetch_trace_ids_for_session_prefix(session_prefix: str) -> list[str]:
    """Fetch trace IDs for every session whose ID starts with *session_prefix*.

    This is useful when sessions follow a naming convention like
    ``"experiment_2024-01_..."`` and you want to evaluate an entire batch.

    Implementation: pages through *all* sessions, filters by prefix, then
    delegates to ``fetch_trace_ids_for_session_ids`` for trace resolution.
    """
    api = _require_langfuse_api()
    matching_session_ids: list[str] = []
    page = 1
    limit = 50

    # Scan all sessions and collect those matching the prefix.
    while True:
        sessions = api.sessions.list(page=page, limit=limit)
        data = _field(sessions, "data", [])
        if not data:
            break

        for session in data:
            session_id = _field(session, "id")
            if session_id and session_id.startswith(session_prefix):
                matching_session_ids.append(session_id)

        meta = _field(sessions, "meta")
        total_pages = _field(meta, "total_pages", page)
        if page >= total_pages or len(data) < limit:
            break
        page += 1

    # Resolve matched sessions → trace IDs.
    return fetch_trace_ids_for_session_ids(matching_session_ids)


# ---------------------------------------------------------------------------
#  Layer 3 — Observations: enumerate, fetch full rows scoped by name, convert
#
# Fetching EVERY observation of a trace (paged get_many with only trace_id)
# is a table-query whose cost scales with the trace's span volume — Langfuse's
# query-cost guard 422s on heavy games. The read path therefore splits in two:
#   1. trace.get(trace_id) — cheap full ENUMERATION (ids/names/types), but it
#      TRUNCATES large output fields, so it can never supply case content.
#   2. get_many(trace_id=..., name=<exact>) — full output, tiny result set.
# A batched fast path pushes the prefix filter server-side via the JSON
# `filter` param when many names are wanted; any ApiError falls back to the
# guaranteed per-name loop.
# ---------------------------------------------------------------------------

# Above this many distinct target names, try one batched prefix query before
# falling back to per-name fetches (action-eval spans run 150-300 per game).
_BATCHED_FETCH_THRESHOLD = 10


def enumerate_observations(trace_id: str) -> list[dict[str, Any]]:
    """Enumerate all observations of a trace (id/name/type/parent) — no 422.

    Uses ``trace.get``, which embeds every observation in one response but
    truncates large ``output`` fields — enumeration only, never case content.
    """
    api = _require_langfuse_api()
    trace = api.trace.get(trace_id)
    return [
        {
            "id": _field(obs, "id"),
            "name": _field(obs, "name"),
            "type": _field(obs, "type"),
            "parent_observation_id": _field(obs, "parent_observation_id"),
        }
        for obs in (_field(trace, "observations") or [])
    ]


def _normalize_observation(obs: Any, trace_id: str, kind: str) -> dict[str, Any]:
    """Normalize an API observation to the plain span-dict shape the converters
    (and the local sidecar records) use."""
    return {
        "kind": kind,
        "id": _field(obs, "id"),
        "name": _field(obs, "name"),
        "trace_id": trace_id,
        "parent_observation_id": _field(obs, "parent_observation_id"),
        "metadata": _field(obs, "metadata") or {},
        "input": _field(obs, "input"),
        "output": _field(obs, "output"),
    }


def _fetch_full_observations_by_name(
    trace_id: str, name: str, limit: int = 10
) -> list[Any]:
    """Fetch full observations (un-truncated output) for one exact name.

    ``get_many``'s ``name`` filter is exact-match server-side, so the result is
    1-few rows — cheap enough to never trip the query-cost guard.
    """
    api = _require_langfuse_api()
    rows: list[Any] = []
    page = 1
    while True:
        observations = api.observations.get_many(
            trace_id=trace_id, name=name, page=page, limit=limit
        )
        data = _field(observations, "data", [])
        if not data:
            break
        rows.extend(data)
        if len(data) < limit:
            break
        page += 1
    return rows


def _fetch_full_spans_batched(
    trace_id: str, prefix: str, limit: int = 20
) -> list[Any] | None:
    """One paged query for all SPANs matching a name prefix, or None to signal
    the caller to fall back to per-name fetches.

    Pushes the prefix filter server-side via the JSON ``filter`` param (which
    supersedes query params, so traceId rides inside it too; the plain
    trace_id kwarg stays as a belt-and-braces scope if a server build ignores
    ``filter``). Small pages — rows carry heavy outputs. Server support is
    version-dependent: any ApiError → None → per-name loop.
    """
    api = _require_langfuse_api()
    filter_json = json.dumps(
        [
            {"type": "string", "column": "traceId", "operator": "=", "value": trace_id},
            {"type": "string", "column": "name", "operator": "starts with", "value": prefix},
            {"type": "string", "column": "type", "operator": "=", "value": "SPAN"},
        ]
    )
    rows: list[Any] = []
    page = 1
    try:
        while True:
            observations = api.observations.get_many(
                trace_id=trace_id, filter=filter_json, page=page, limit=limit
            )
            data = _field(observations, "data", [])
            if not data:
                break
            rows.extend(data)
            if len(data) < limit:
                break
            page += 1
    except Exception as exc:  # ApiError, or any transport hiccup → fall back
        print(f"Batched span fetch unavailable ({exc!r}); falling back to per-name.")
        return None
    return rows


def fetch_spans(
    trace_id: str,
    *,
    prefix: str | None = None,
    names: list[str] | None = None,
    exclude_names: frozenset[str] = frozenset(),
    kind: str = "span",
) -> list[dict[str, Any]]:
    """Fetch full span dicts for a trace, scoped by name prefix or exact names.

    The generic retroactive reader: ANY span (eval-case-wrapped or not) can be
    mined from Langfuse by prefix without ever fetch-all-ing a heavy trace.
    Resolution: enumerate (when *names* not given) → drop *exclude_names* →
    batched prefix fetch when many targets, else per-name → normalize, keeping
    only the resolved target names (also guards the batched path client-side).
    """
    if names is None:
        if prefix is None:
            raise ValueError("fetch_spans requires a prefix or explicit names.")
        names = [
            obs["name"]
            for obs in enumerate_observations(trace_id)
            if obs["name"] and obs["name"].startswith(prefix)
        ]
    wanted = [
        name
        for name in _dedupe_preserving_order([n for n in names if n])
        if name not in exclude_names
    ]
    if not wanted:
        return []

    rows: list[Any] | None = None
    if prefix is not None and len(wanted) > _BATCHED_FETCH_THRESHOLD:
        rows = _fetch_full_spans_batched(trace_id, prefix)
    if rows is None:
        rows = []
        for name in wanted:
            rows.extend(_fetch_full_observations_by_name(trace_id, name))

    wanted_set = set(wanted)
    return [
        _normalize_observation(obs, trace_id, kind)
        for obs in rows
        if _field(obs, "name") in wanted_set
    ]


def _cases_from_spans(spans: list[dict[str, Any]], converter: Any) -> list[Any]:
    """Convert span dicts via *converter*, dropping non-case spans (None)."""
    return [case for case in map(converter, spans) if case]


def fetch_eval_cases(trace_id: str) -> list[EvalCase]:
    """Build EvalCase objects from every eval span in a trace."""
    spans = fetch_spans(
        trace_id, prefix=ACTION_EVAL_SPAN_PREFIX, kind="agent_action_eval"
    )
    return _cases_from_spans(spans, eval_case_from_span)


def fetch_extraction_cases(trace_id: str) -> list[ExtractionCase]:
    """Build ExtractionCase objects from extraction spans in a trace.

    The per-role child LLM runs share the parent case-span's name prefix (see
    Agents.observability.span_names), so prefix candidates are narrowed
    STRUCTURALLY: the parent is the candidate whose own parent is not itself a
    candidate. Normally exactly one fetch per trace.
    """
    candidates = [
        obs
        for obs in enumerate_observations(trace_id)
        if obs["name"] and obs["name"].startswith(EXTRACTION_SPAN_PREFIX)
    ]
    candidate_ids = {obs["id"] for obs in candidates}
    parent_names = [
        obs["name"]
        for obs in candidates
        if obs["parent_observation_id"] not in candidate_ids
    ]
    spans = fetch_spans(trace_id, names=parent_names, kind="postgame_extraction")
    return _cases_from_spans(spans, extraction_case_from_span)


def fetch_dedup_cases(trace_id: str) -> list[DedupCase]:
    """Build DedupCase objects from dedup spans in a trace.

    The dedup LLM runs match the prefix but carry no case — excluded by name
    up front so their (potentially many) full rows are never fetched.
    """
    spans = fetch_spans(
        trace_id,
        prefix=DEDUP_SPAN_PREFIX,
        exclude_names=DEDUP_LLM_RUN_NAMES,
        kind="dedup",
    )
    return _cases_from_spans(spans, dedup_case_from_span)


def fetch_day_summary_cases(trace_id: str) -> list[DaySummaryCase]:
    """Build DaySummaryCase objects from day-summary spans in a trace."""
    spans = fetch_spans(
        trace_id, prefix=DAY_SUMMARY_SPAN_PREFIX, kind="day_summary"
    )
    return _cases_from_spans(spans, day_summary_case_from_span)


# ---------------------------------------------------------------------------
# Layer 4 — Score push: judge results → Langfuse scores
#
# After an external judge (LLM or human) produces scores for an EvalCase,
# this layer writes them back to Langfuse so they appear on the trace's
# score panel.  Scores use deterministic UUID-5 IDs so re-running the
# pipeline is idempotent (same input → same score ID → upsert, not dupe).
# ---------------------------------------------------------------------------


def push_judge_scores(
    trace_id: str,
    observation_id: str,
    scores: dict[str, Any],
    model: str,
    model_type: str,
    session_id: str | None = None,
) -> None:
    """Write judge scores for one observation back to Langfuse.

    Args:
        trace_id:       The Langfuse trace this observation belongs to.
        observation_id: The specific observation (eval span) that was judged.
        scores:         Dict with numeric values for each of ``SCORE_NAMES``
                        and an optional ``brief_reasoning`` string.
        model:          The judge model identifier (e.g. ``"gpt-4"``).
        model_type:     Category of the judge (e.g. ``"llm"`` or ``"human"``).
    """
    for name in SCORE_NAMES:
        value = scores.get(name)
        if value is None:
            continue

        # Deterministic ID: same eval version + model + trace + observation +
        # score name always produces the same UUID, making re-runs idempotent.
        score_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{EVAL_VERSION}:{model_type}:{model}:"
                f"{trace_id}:{observation_id}:{name}",
            )
        )

        langfuse.create_score(
            trace_id=trace_id,
            observation_id=observation_id,
            score_id=score_id,
            name=f"judge_{name}",
            value=float(value),
            data_type="NUMERIC",
            comment=scores.get("brief_reasoning", ""),
            metadata={
                "eval_version": EVAL_VERSION,
                "judge_model": model,
                "model_type": model_type,
            },
        )
        if session_id:
            session_score_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{EVAL_VERSION}:{model_type}:{model}:"
                    f"{session_id}:{trace_id}:{observation_id}:{name}",
                )
            )
            langfuse.create_score(
                session_id=session_id,
                score_id=session_score_id,
                name=f"judge_{name}",
                value=float(value),
                data_type="NUMERIC",
                comment=scores.get("brief_reasoning", ""),
                metadata={
                    "eval_version": EVAL_VERSION,
                    "judge_model": model,
                    "model_type": model_type,
                    "trace_id": trace_id,
                    "observation_id": observation_id,
                },
            )


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


def flush_langfuse() -> None:
    """Flush any buffered Langfuse events to the server.

    Call this at the end of a pipeline run to ensure all scores created by
    ``push_judge_scores`` are actually transmitted before the process exits.
    """
    langfuse.flush()

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

from evaluation.settings import load_project_env

load_project_env()

from langfuse import get_client  # noqa: E402

from Agents.schemas.evaluation import EvalCase  # noqa: E402
from evaluation.cases import eval_case_from_span  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Version tag attached to every score pushed by this module.  Bump this when
# the judge prompt or scoring rubric changes so that old and new scores can
# be distinguished in Langfuse dashboards.
EVAL_VERSION = "retrieval_judge_v1"

# Observation names that start with this prefix are treated as evaluation
# spans (i.e. they contain the input/output data a judge should score).
ACTION_EVAL_SPAN_PREFIX = "agent_action_eval_"

# The three score dimensions the judge produces for each eval span.
SCORE_NAMES = ["summary_quality", "retrieval_relevance", "strategy_application"]

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
    """Fetch all trace IDs belonging to one exact Langfuse session ID.

    Pages through ``api.trace.list()`` until all results are collected.
    """
    api = _require_langfuse_api()
    trace_ids: list[str] = []
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

    return trace_ids


def fetch_trace_ids_for_session_ids(session_ids: list[str]) -> list[str]:
    """Fetch trace IDs for multiple exact session IDs.

    Deduplicates both the input session IDs and the collected trace IDs.
    """
    trace_ids: list[str] = []
    for session_id in _dedupe_preserving_order(session_ids):
        trace_ids.extend(fetch_trace_ids_for_session_id(session_id))
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
# Layer 3 — Observation extraction: trace IDs → eval spans
#
# For each trace ID (from Layer 2), fetch its observations and keep only
# those whose name starts with ACTION_EVAL_SPAN_PREFIX.  These spans
# contain the agent input/output that a judge will score.
# ---------------------------------------------------------------------------


def _fetch_observations_page(
    trace_id: str,
    page: int,
    limit: int = 100,
    parent_observation_id: str | None = None,
) -> list[Any]:
    """Fetch a single page of observations for a trace."""
    api = _require_langfuse_api()
    observations = api.observations.get_many(
        trace_id=trace_id,
        page=page,
        limit=limit,
        parent_observation_id=parent_observation_id,
    )
    return _field(observations, "data", [])


def fetch_agent_action_eval_spans(trace_id: str) -> list[dict[str, Any]]:
    """Fetch all ``agent_action_eval_*`` observations for a single trace.

    Returns a list of dicts with a consistent shape regardless of how the
    Langfuse SDK represents the observation internally:

        {
            "kind":                  "agent_action_eval",
            "id":                    "<observation ID>",
            "name":                  "agent_action_eval_<action>",
            "trace_id":              "<parent trace ID>",
            "parent_observation_id": "<optional parent span>",
            "metadata":              { ... },
            "input":                 <the agent's input for this action>,
            "output":                <the agent's output for this action>,
        }
    """
    eval_spans: list[dict[str, Any]] = []
    page = 1
    limit = 100

    while True:
        observations = _fetch_observations_page(
            trace_id=trace_id, page=page, limit=limit
        )
        if not observations:
            break

        for obs in observations:
            name = _field(obs, "name")
            if name and name.startswith(ACTION_EVAL_SPAN_PREFIX):
                eval_spans.append(
                    {
                        "kind": "agent_action_eval",
                        "id": _field(obs, "id"),
                        "name": name,
                        "trace_id": trace_id,
                        "parent_observation_id": _field(obs, "parent_observation_id"),
                        "metadata": _field(obs, "metadata") or {},
                        "input": _field(obs, "input"),
                        "output": _field(obs, "output"),
                    }
                )

        if len(observations) < limit:
            break
        page += 1

    return eval_spans


# ---------------------------------------------------------------------------
# Layer 4 — EvalCase construction: eval spans → structured cases
#
# Converts the raw span dicts from Layer 3 into typed EvalCase objects that
# the judge prompt can consume.  The actual conversion logic lives in
# ``evaluation.cases.eval_case_from_span``; this layer simply wires it up.
# ---------------------------------------------------------------------------


def fetch_eval_cases(trace_id: str) -> list[EvalCase]:
    """Build ``EvalCase`` objects from every eval span in a trace.

    Spans that fail conversion (e.g. missing required fields) are silently
    skipped — ``eval_case_from_span`` returns ``None`` for those.
    """
    cases: list[EvalCase] = []
    for span in fetch_agent_action_eval_spans(trace_id):
        case = eval_case_from_span(span)
        if case:
            cases.append(case)
    return cases


# ---------------------------------------------------------------------------
# Layer 5 — Score push: judge results → Langfuse scores
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


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


def flush_langfuse() -> None:
    """Flush any buffered Langfuse events to the server.

    Call this at the end of a pipeline run to ensure all scores created by
    ``push_judge_scores`` are actually transmitted before the process exits.
    """
    langfuse.flush()
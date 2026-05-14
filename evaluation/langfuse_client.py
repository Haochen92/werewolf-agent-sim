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


EVAL_VERSION = "retrieval_judge_v1"
ACTION_EVAL_SPAN_PREFIX = "agent_action_eval_"

langfuse = get_client()


def _require_langfuse_api() -> Any:
    """Return the generated Langfuse API client available in langfuse 3.x."""
    api = getattr(langfuse, "api", None)
    if api is None:
        raise RuntimeError(
            "Langfuse API client is unavailable. Check LANGFUSE_PUBLIC_KEY, "
            "LANGFUSE_SECRET_KEY, and LANGFUSE_HOST in .env."
        )
    return api


def _field(obj: Any, name: str, default: Any = None) -> Any:
    """Read a field from Fern/Pydantic objects or plain dicts."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _trace_ids_from_trace_page(traces: Any) -> list[str]:
    return [
        trace_id
        for trace_id in (_field(trace, "id") for trace in _field(traces, "data", []))
        if trace_id
    ]


def fetch_trace_ids_for_session_id(session_id: str) -> list[str]:
    """Fetch all trace IDs for one exact Langfuse session ID."""
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
        meta = _field(traces, "meta")
        total_pages = _field(meta, "total_pages", page)
        if page >= total_pages or len(data) < limit:
            break
        page += 1

    return trace_ids


def fetch_trace_ids_for_session_ids(session_ids: list[str]) -> list[str]:
    """Fetch trace IDs for exact session IDs without scanning unrelated traces."""
    trace_ids: list[str] = []
    for session_id in _dedupe_preserving_order(session_ids):
        trace_ids.extend(fetch_trace_ids_for_session_id(session_id))
    return _dedupe_preserving_order(trace_ids)


def fetch_trace_ids_for_session_prefix(session_prefix: str) -> list[str]:
    """Fetch trace IDs whose session_id starts with the given prefix."""
    api = _require_langfuse_api()
    session_ids: list[str] = []
    page = 1
    limit = 50

    while True:
        sessions = api.sessions.list(page=page, limit=limit)
        data = _field(sessions, "data", [])
        if not data:
            break

        for session in data:
            session_id = _field(session, "id")
            if session_id and session_id.startswith(session_prefix):
                session_ids.append(session_id)

        meta = _field(sessions, "meta")
        total_pages = _field(meta, "total_pages", page)
        if page >= total_pages or len(data) < limit:
            break
        page += 1

    return fetch_trace_ids_for_session_ids(session_ids)


def read_session_ids_from_batch_results(path: Path) -> list[str]:
    """Read session IDs from a run_batch JSONL output file."""
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


def _fetch_observations_page(
    trace_id: str,
    page: int,
    limit: int = 100,
    parent_observation_id: str | None = None,
) -> list[Any]:
    api = _require_langfuse_api()
    observations = api.observations.get_many(
        trace_id=trace_id,
        page=page,
        limit=limit,
        parent_observation_id=parent_observation_id,
    )
    return _field(observations, "data", [])


def fetch_agent_action_eval_spans(trace_id: str) -> list[dict[str, Any]]:
    """Fetch structured agent_action_eval observations for a trace."""
    eval_spans: list[dict[str, Any]] = []
    page = 1
    limit = 100

    while True:
        observations = _fetch_observations_page(trace_id=trace_id, page=page, limit=limit)
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


def fetch_eval_cases(trace_id: str) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for span in fetch_agent_action_eval_spans(trace_id):
        case = eval_case_from_span(span)
        if case:
            cases.append(case)
    return cases


def push_judge_scores(
    trace_id: str,
    observation_id: str,
    scores: dict[str, Any],
    model: str,
    model_type: str,
) -> None:
    score_names = ["summary_quality", "retrieval_relevance", "strategy_application"]
    for name in score_names:
        value = scores.get(name)
        if value is not None:
            score_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    (
                        f"{EVAL_VERSION}:{model_type}:{model}:"
                        f"{trace_id}:{observation_id}:{name}"
                    ),
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


def flush_langfuse() -> None:
    langfuse.flush()

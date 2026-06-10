"""Embedding-model factory with transient-error retry.

``create_embeddings`` wraps ``GoogleGenerativeAIEmbeddings`` so the LangGraph
store's runtime retrieval query (the live situation text) survives quota blips
instead of aborting the game — the bare API call had no backoff, so a single 429
killed a whole run. The transient set mirrors memory persistence's; inlined here
to avoid a circular import (memory imports this factory). Backoff is configurable
via EMBED_RETRY_* env vars.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from .backends import _DEFAULT_VERTEX_LOCATION, _use_vertex

logger = logging.getLogger(__name__)

# Canonical embedding config. The vector store index is only valid for the
# embedding model/dims it was built with, so these are part of the runtime
# fingerprint (Agents/run_fingerprint.py) and referenced by consumers instead
# of being re-hardcoded.
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_EMBEDDING_DIMS = 1536

_EMBED_TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_EMBED_TRANSIENT_MARKERS = (
    "429", "resource_exhausted", "rate limit", "quota",
    "500", "502", "503", "504", "deadline", "unavailable",
    "connection reset", "bad gateway", "timeout",
)


def _embed_error_is_transient(exc: BaseException) -> bool:
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if getattr(current, "status_code", None) in _EMBED_TRANSIENT_STATUS_CODES:
            return True
        response = getattr(current, "response", None)
        if getattr(response, "status_code", None) in _EMBED_TRANSIENT_STATUS_CODES:
            return True
        message = str(current).lower()
        if any(marker in message for marker in _EMBED_TRANSIENT_MARKERS):
            return True
        current = current.__cause__ or current.__context__
    return False


def _embed_with_retries(call: Callable[[], Any], *, op: str) -> Any:
    attempts = int(os.getenv("EMBED_RETRY_ATTEMPTS", "5"))
    initial = float(os.getenv("EMBED_RETRY_INITIAL_DELAY", "2.0"))
    max_delay = float(os.getenv("EMBED_RETRY_MAX_DELAY", "30.0"))
    attempts = max(1, attempts)
    for attempt in range(1, attempts + 1):
        try:
            return call()
        except Exception as exc:  # noqa: BLE001 — re-raised below if not transient/last
            if attempt >= attempts or not _embed_error_is_transient(exc):
                raise
            delay = min(max_delay, initial * (2 ** (attempt - 1)))
            logger.warning(
                "Embedding %s hit a transient error; retrying in %.1fs "
                "(attempt %s/%s): %s",
                op, delay, attempt + 1, attempts, exc,
            )
            time.sleep(delay)
    raise RuntimeError(f"Embedding {op} retry loop exited unexpectedly")


class _RetryingGoogleGenerativeAIEmbeddings(GoogleGenerativeAIEmbeddings):
    """GoogleGenerativeAIEmbeddings with exponential backoff on transient errors.

    Wraps both the sync and async embed methods so the LangGraph store's runtime
    retrieval query (and any other consumer) survives quota blips instead of
    aborting the game. Backoff is configurable via EMBED_RETRY_* env vars.
    """

    def embed_documents(self, texts, *args, **kwargs):
        return _embed_with_retries(
            lambda: super(_RetryingGoogleGenerativeAIEmbeddings, self).embed_documents(
                texts, *args, **kwargs
            ),
            op="embed_documents",
        )

    def embed_query(self, text, *args, **kwargs):
        return _embed_with_retries(
            lambda: super(_RetryingGoogleGenerativeAIEmbeddings, self).embed_query(
                text, *args, **kwargs
            ),
            op="embed_query",
        )


def create_embeddings(
    model: str = DEFAULT_EMBEDDING_MODEL,
    *,
    output_dimensionality: int | None = None,
) -> GoogleGenerativeAIEmbeddings:
    """Create an embeddings model (with transient-error retry) for the configured backend."""
    kwargs: dict[str, Any] = {"model": model}
    if output_dimensionality is not None:
        kwargs["output_dimensionality"] = output_dimensionality

    if _use_vertex():
        kwargs["vertexai"] = True
        kwargs["location"] = os.getenv(
            "VERTEX_LOCATION", _DEFAULT_VERTEX_LOCATION
        )

    return _RetryingGoogleGenerativeAIEmbeddings(**kwargs)

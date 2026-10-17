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
from langchain_openai import OpenAIEmbeddings

from .providers.google import _DEFAULT_VERTEX_LOCATION, _use_vertex

logger = logging.getLogger(__name__)

# Canonical embedding config. The vector store index is only valid for the
# embedding model/dims it was built with, so these are part of the runtime
# fingerprint (Agents/run_fingerprint.py) and referenced by consumers instead
# of being re-hardcoded.
# 2026-07-16: -001 → -2. The current Vertex project caps -001 at 5 req/min (trial-inherited,
# console-unmodifiable, increase requests denied) while -2's embedContent bucket is granted 50/min —
# -001 is unrunnable, so the model moves and the absolute cosine thresholds move with it
# (percentile-remapped: retrieval dedup_gate + tell PREFILTER_THRESHOLD; clustering 0.70 binds on
# neither scale). Canary re-pinned same day — the legitimate re-pin case (intentional model change,
# cold-start run so no store rebuild owed).
# A model id with a slash (``qwen/qwen3-embedding-8b``) is served through OpenRouter; anything else
# is a Gemini model. Selected by MEMORY_EMBEDDING_MODEL: a store, its cache and the thresholds below
# all belong to one model.
DEFAULT_EMBEDDING_MODEL = os.getenv("MEMORY_EMBEDDING_MODEL", "qwen/qwen3-embedding-8b")
DEFAULT_EMBEDDING_DIMS = 1536

# OpenRouter routes a model to several hosts, and their vectors for one text differ slightly (Qwen3
# on Nebius vs DeepInfra: cosine ~0.998), so a store's vectors are pinned to these hosts in order and
# never fall back elsewhere (SiliconFlow serves Qwen3 in fp8).
OPENROUTER_EMBEDDING_PROVIDERS = ["Nebius", "DeepInfra"]

# Cosine thresholds by embedding model: each model has its own similarity scale, so a threshold is
# only meaningful for the model it was set on. A new model's values are percentile-remapped from the
# old model's over the same text pairs (evidence/memory_system/v8, embedder migration).
SIMILARITY_THRESHOLDS: dict[str, dict[str, float]] = {
    "gemini-embedding-2": {
        "dedup_candidate": 0.55,        # online dedup: a store hit worth an LLM look (situation)
        "obs_content_keep": 0.935,      # online dedup prefilter: below this, keep without an LLM
        "obs_content_discard": 0.96,    # ... at or above this, discard without an LLM
        "sp_action_keep": 0.81,         # the same pair for strategy-point actions
        "sp_action_discard": 0.93,
        "batch_cluster": 0.70,          # batch dedup clustering (situation)
        "synth_cluster": 0.65,          # synthesis clustering (situation)
        "retrieval_dedup_gate": 0.87,   # near-duplicate filter on retrieved items (situation)
    },
    # 2026-10-12, from gemini-embedding-2 over within-cell pairs of the v8 seed store, and the
    # dedup_v2 golden labels for the prefilter (zero errors; gemini-embedding-2's own values above
    # were set on -001 and make errors on those labels). The candidate and clustering thresholds bind
    # on almost no pair on either model; they keep their distance below each model's lowest pair.
    "qwen/qwen3-embedding-8b": {
        "dedup_candidate": 0.36,
        "obs_content_keep": 0.72,
        "obs_content_discard": 0.94,
        "sp_action_keep": 0.61,
        "sp_action_discard": 0.88,
        "batch_cluster": 0.50,
        "synth_cluster": 0.46,
        "retrieval_dedup_gate": 0.80,   # p68 of within-cell situation pairs, as 0.87 is on Gemini
    },
}


def similarity_threshold(name: str, model: str | None = None) -> float:
    """The cosine threshold `name` on the scale of `model` (the configured embedding model)."""
    return SIMILARITY_THRESHOLDS[model or DEFAULT_EMBEDDING_MODEL][name]

_EMBED_TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_EMBED_TRANSIENT_MARKERS = (
    "429", "resource_exhausted", "rate limit", "quota",
    "500", "502", "503", "504", "deadline", "unavailable",
    "connection reset", "bad gateway", "timeout", "timed out",
)


def _embed_error_is_transient(exc: BaseException) -> bool:
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, TimeoutError) or "timeout" in type(current).__name__.lower():
            return True
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


# The same question for a chat call: is this the provider being slow or full (a timeout, a
# 429 or 5xx, a dropped connection) rather than the request being wrong? A game turn that
# fails this way goes to its rescue model instead of asking the same model again.
is_transient_provider_error = _embed_error_is_transient


_KEY_REJECTED_STATUS_CODES = {401, 403}
_KEY_REJECTED_MARKERS = (
    "invalid x-api-key", "invalid api key", "incorrect api key", "api key not valid",
    "api_key_invalid", "authentication_error", "permission_denied",
    "credit balance is too low",
)


# The words every refusal of a game's key is told in (agent_player); the server knows such a
# death by them, even from an archived game's stored error.
KEY_REFUSED = "refused this game's API key"


def provider_complaint(exc: BaseException) -> str:
    """The provider's own short reason for a failed call, e.g. "401, invalid x-api-key": the
    status and the message from the SDK's error body (Anthropic and OpenAI shape it alike)."""
    status = getattr(exc, "status_code", None)
    body = getattr(exc, "body", None)
    error = body.get("error") if isinstance(body, dict) else None
    message = error.get("message") if isinstance(error, dict) else None
    if not message:
        message = str(getattr(exc, "message", "") or exc)
    message = message.strip()[:200]
    return f"{status}, {message}" if status else message


class ProviderKeyRejected(RuntimeError):
    """The provider refused the game's credential: no later turn on that key can succeed, so the
    game ends with this said rather than playing on in technical passes (owner's BYOK ruling,
    2026-08-12: a dead key is surfaced and the player restarts)."""


def is_key_rejected_error(exc: BaseException) -> bool:
    """Whether a chat call failed because the key itself was refused (wrong provider's key,
    revoked, out of credit), not because of this one request."""
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if getattr(current, "status_code", None) in _KEY_REJECTED_STATUS_CODES:
            return True
        response = getattr(current, "response", None)
        if getattr(response, "status_code", None) in _KEY_REJECTED_STATUS_CODES:
            return True
        message = str(current).lower()
        if any(marker in message for marker in _KEY_REJECTED_MARKERS):
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
        result = _embed_with_retries(
            lambda: super(_RetryingGoogleGenerativeAIEmbeddings, self).embed_documents(
                texts, *args, **kwargs
            ),
            op="embed_documents",
        )
        if len(result) != len(texts):
            # Batch collapse: the installed langchain client posts embedContent-family models
            # (gemini-embedding-2) as ONE content, returning a single vector for the whole batch.
            # A silently misaligned vector list would corrupt every store index downstream, so fall
            # back to per-text calls (embed_documents, not embed_query, to keep the document task
            # type). Costs one request per text — acceptable: batch embeds run in the serial
            # driver ticks, and the run-scale request budget is the embedContent 50/min bucket.
            logger.warning(
                "embed_documents returned %d vectors for %d texts (batch collapse); "
                "re-embedding per text", len(result), len(texts),
            )
            result = [
                _embed_with_retries(
                    lambda t=t: super(
                        _RetryingGoogleGenerativeAIEmbeddings, self
                    ).embed_documents([t], *args, **kwargs)[0],
                    op="embed_documents[single]",
                )
                for t in texts
            ]
        return result

    def embed_query(self, text, *args, **kwargs):
        return _embed_with_retries(
            lambda: super(_RetryingGoogleGenerativeAIEmbeddings, self).embed_query(
                text, *args, **kwargs
            ),
            op="embed_query",
        )


class _RetryingOpenRouterEmbeddings(OpenAIEmbeddings):
    """An OpenRouter-served embedding model (OpenAI-compatible API) with the same transient-error
    backoff as the Gemini one. Accepts and ignores Gemini's ``task_type``."""

    def embed_documents(self, texts, *args, **kwargs):
        kwargs.pop("task_type", None)
        return _embed_with_retries(
            lambda: super(_RetryingOpenRouterEmbeddings, self).embed_documents(texts, *args, **kwargs),
            op="embed_documents",
        )

    def embed_query(self, text, *args, **kwargs):
        kwargs.pop("task_type", None)
        return _embed_with_retries(
            lambda: super(_RetryingOpenRouterEmbeddings, self).embed_query(text, *args, **kwargs),
            op="embed_query",
        )


def _create_openrouter_embeddings(model: str, output_dimensionality: int | None) -> OpenAIEmbeddings:
    return _RetryingOpenRouterEmbeddings(
        model=model, base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"),
        dimensions=output_dimensionality,
        # Not an OpenAI model: send raw text, not tiktoken ids.
        check_embedding_ctx_length=False,
        model_kwargs={"extra_body": {"provider": {"order": OPENROUTER_EMBEDDING_PROVIDERS,
                                                  "allow_fallbacks": False}}},
    )


def create_embeddings(
    model: str = DEFAULT_EMBEDDING_MODEL,
    *,
    output_dimensionality: int | None = None,
) -> GoogleGenerativeAIEmbeddings | OpenAIEmbeddings:
    """Create an embeddings model (with transient-error retry) for the configured backend."""
    if "/" in model:
        return _create_openrouter_embeddings(model, output_dimensionality)
    kwargs: dict[str, Any] = {"model": model}
    if output_dimensionality is not None:
        kwargs["output_dimensionality"] = output_dimensionality

    if _use_vertex():
        kwargs["vertexai"] = True
        kwargs["location"] = os.getenv(
            "VERTEX_LOCATION", _DEFAULT_VERTEX_LOCATION
        )

    return _RetryingGoogleGenerativeAIEmbeddings(**kwargs)

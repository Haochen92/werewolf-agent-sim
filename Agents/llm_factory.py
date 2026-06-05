"""Centralized factory for LLM chat models and embeddings.

All LLM instantiation across the project should go through this module.
Supports four backends:

- **vertex** (default): Uses Vertex AI via Application Default Credentials
  on the ``global`` endpoint.  Active when ``LLM_BACKEND=vertex`` or when
  no ``GOOGLE_API_KEY`` is set.
- **google** (legacy): Uses the Google Generative AI Developer API with an
  API key.  Set by ``LLM_BACKEND=google`` (requires ``GOOGLE_API_KEY``).
- **nim**: Uses NVIDIA NIM via the OpenAI-compatible API.
  Set model prefix ``nim/`` (e.g. ``"nim/deepseek-ai/deepseek-v4-flash"``).
  Requires ``NVIDIA_API_KEY``.
- **mistral**: Uses the Mistral API (OpenAI-compatible).
  Set model prefix ``mistral/`` (e.g. ``"mistral/mistral-small-2506"``).
  Requires ``MISTRAL_API_KEY``.

On Vertex AI, ``thinking_level`` is translated to ``thinking_budget`` (token
count) because the 2.x model series does not support the string-based
``thinking_level`` parameter.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# The factory is the central reader of provider API keys (MISTRAL_API_KEY,
# NVIDIA_API_KEY, …) from the environment, so it loads .env itself rather than
# relying on each caller (e.g. the labeling engine) to have done so first.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Chat-model instances are immutable after construction and safe to reuse across
# threads (the underlying SDK/httpx clients are thread-safe). Building one is
# non-trivial (client + auth setup), so memoize by construction args — callers in
# hot loops (e.g. the multi-model labeling engine) would otherwise rebuild per call.
_MODEL_CACHE: dict[Any, Any] = {}
_MODEL_CACHE_LOCK = threading.Lock()

_DEFAULT_VERTEX_LOCATION = "global"

THINKING_LEVEL_TO_BUDGET: dict[str, int] = {
    "minimal": 128,
    "low": 1024,
    "medium": 4096,
    "high": 8192,
}


_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
_MISTRAL_BASE_URL = "https://api.mistral.ai/v1"


@dataclass
class _OpenAICompatResponse:
    content: str


class NIMChatModel:
    """Thin wrapper around NVIDIA NIM API with LangChain-compatible .invoke()."""

    def __init__(self, model: str, *, temperature: float = 0.0):
        from openai import OpenAI

        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("NVIDIA_API_KEY not set")
        self._client = OpenAI(base_url=_NIM_BASE_URL, api_key=api_key)
        self._model = model
        self._temperature = temperature

    def invoke(self, prompt: str) -> _OpenAICompatResponse:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
        )
        return _OpenAICompatResponse(content=response.choices[0].message.content)


class MistralChatModel:
    """Thin wrapper around Mistral API with LangChain-compatible .invoke()."""

    def __init__(self, model: str, *, temperature: float = 0.0):
        from openai import OpenAI

        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY not set")
        self._client = OpenAI(base_url=_MISTRAL_BASE_URL, api_key=api_key)
        self._model = model
        self._temperature = temperature

    def invoke(self, prompt: str) -> _OpenAICompatResponse:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
        )
        return _OpenAICompatResponse(content=response.choices[0].message.content)


def _use_vertex() -> bool:
    backend = os.getenv("LLM_BACKEND", "").strip().lower()
    if backend == "google":
        return False
    if backend == "vertex":
        return True
    return not bool(os.getenv("GOOGLE_API_KEY"))


def create_chat_model(
    model: str,
    *,
    temperature: float = 0.0,
    thinking_level: str | None = None,
    thinking_budget: int | None = None,
    **kwargs: Any,
) -> ChatGoogleGenerativeAI | NIMChatModel:
    """Create (or reuse) a chat model using the configured backend.

    Instances are memoized by construction args (see ``_MODEL_CACHE``); repeated
    calls with the same args return the same shared, thread-safe instance.

    Parameters
    ----------
    model:
        Model identifier.  Use ``"nim/<org>/<model>"`` for NVIDIA NIM
        (e.g. ``"nim/deepseek-ai/deepseek-v4-flash"``), otherwise a
        Gemini model name (e.g. ``"gemini-2.5-flash"``).
    temperature:
        Sampling temperature.
    thinking_level:
        Symbolic thinking level (``"minimal"``, ``"low"``, ``"medium"``,
        ``"high"``).  Ignored for NIM models.
    thinking_budget:
        Explicit thinking token budget.  Takes precedence over
        ``thinking_level`` when both are provided.  Ignored for NIM models.
    **kwargs:
        Forwarded to ``ChatGoogleGenerativeAI`` (ignored for NIM).
    """
    try:
        cache_key: Any = (
            model, temperature, thinking_level, thinking_budget,
            tuple(sorted(kwargs.items())),
        )
        hash(cache_key)
    except TypeError:
        cache_key = None  # unhashable kwargs -> bypass cache
    if cache_key is not None and (cached := _MODEL_CACHE.get(cache_key)) is not None:
        return cached

    instance = _build_chat_model(
        model, temperature=temperature, thinking_level=thinking_level,
        thinking_budget=thinking_budget, **kwargs,
    )
    if cache_key is None:
        return instance
    with _MODEL_CACHE_LOCK:
        return _MODEL_CACHE.setdefault(cache_key, instance)


def _build_chat_model(
    model: str,
    *,
    temperature: float = 0.0,
    thinking_level: str | None = None,
    thinking_budget: int | None = None,
    **kwargs: Any,
) -> ChatGoogleGenerativeAI | NIMChatModel:
    """Construct a fresh chat model (uncached). See ``create_chat_model``."""
    if model.startswith("nim/"):
        return NIMChatModel(model.removeprefix("nim/"), temperature=temperature)

    if model.startswith("mistral/"):
        return MistralChatModel(model.removeprefix("mistral/"), temperature=temperature)

    build_kwargs: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
    }

    if _use_vertex():
        build_kwargs["vertexai"] = True
        build_kwargs["location"] = os.getenv(
            "VERTEX_LOCATION", _DEFAULT_VERTEX_LOCATION
        )
    else:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            build_kwargs["google_api_key"] = api_key

    if thinking_budget is not None:
        build_kwargs["thinking_budget"] = thinking_budget
    elif thinking_level:
        if _use_vertex():
            budget = THINKING_LEVEL_TO_BUDGET.get(thinking_level)
            if budget is not None:
                build_kwargs["thinking_budget"] = budget
        else:
            build_kwargs["thinking_level"] = thinking_level

    build_kwargs.update(kwargs)
    return ChatGoogleGenerativeAI(**build_kwargs)


# Transient embedding errors worth retrying. Unlike the seed-time loader (which has
# its own retry loop), the *runtime* retrieval query — store.search embedding the live
# situation text — went straight to the API with no backoff, so a single 429 aborted the
# whole game. These mirror memory_persistence's transient set; inlined here to avoid a
# circular import (memory.py imports this factory).
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
    model: str = "gemini-embedding-001",
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

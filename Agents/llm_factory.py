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
from functools import lru_cache
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

# Canonical embedding config. The vector store index is only valid for the
# embedding model/dims it was built with, so these are part of the runtime
# fingerprint (Agents/run_fingerprint.py) and referenced by consumers instead
# of being re-hardcoded.
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_EMBEDDING_DIMS = 1536

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


# ---------------------------------------------------------------------------
# Game model accessors — the cached chat models the game graph runs on, plus the
# env/default resolution they share. Kept here (with create_chat_model) so all
# model instantiation lives in one factory; run_fingerprint imports the constants
# and _thinking_level_from_env to stamp the generation bundle without drift.
# ---------------------------------------------------------------------------

DEFAULT_GAME_MODEL = "gemini-3.1-flash-lite"
DEFAULT_GAME_THINKING_LEVEL = "minimal"
DEFAULT_SUMMARY_THINKING_LEVEL = "medium"
DEFAULT_PRO_MODEL = "gemini-2.5-pro"
# Pinned (was the floating alias "gemini-pro-latest", which Google retargets
# silently — a reproducibility hazard for the extraction pipeline that
# conditions gold labels). gemini-3.5-flash: stable GA, pro-comparable quality,
# and a different model family/quota pool than the primary, so it remains a
# genuine fallback. (3.1-pro-preview rejected: preview tier = no SLA +
# retirement risk.)
DEFAULT_PRO_BACKUP_MODEL = "gemini-3.5-flash"
# Per-item downstream dedup — fixed cheap model (overridable via DEDUP_MODEL env).
DEFAULT_DEDUP_MODEL = "gemini-3.1-flash-lite"
DEFAULT_DEDUP_THINKING_LEVEL = "low"
VALID_THINKING_LEVELS = {"minimal", "low", "medium", "high"}


def _thinking_level_from_env(
    env_var: str,
    default: str | None = None,
) -> str | None:
    value = os.getenv(env_var, default)
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized in {"", "none", "default"}:
        return None
    if normalized not in VALID_THINKING_LEVELS:
        valid = ", ".join(sorted(VALID_THINKING_LEVELS))
        raise ValueError(f"{env_var} must be one of: {valid}")
    return normalized


@lru_cache(maxsize=1)
def get_llm():
    return create_chat_model(
        os.getenv("GOOGLE_GENAI_MODEL", DEFAULT_GAME_MODEL),
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        thinking_level=_thinking_level_from_env(
            "GOOGLE_GENAI_THINKING_LEVEL",
            DEFAULT_GAME_THINKING_LEVEL,
        ),
    )


@lru_cache(maxsize=1)
def get_llm_summary():
    return create_chat_model(
        os.getenv("GOOGLE_GENAI_MODEL", DEFAULT_GAME_MODEL),
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        thinking_level=_thinking_level_from_env(
            "GOOGLE_GENAI_SUMMARY_THINKING_LEVEL",
            DEFAULT_SUMMARY_THINKING_LEVEL,
        ),
    )


@lru_cache(maxsize=1)
def get_llm_judge():
    """Cheap model for binary judgments (e.g. the proactive novelty gate) — minimal thinking."""
    return create_chat_model(
        os.getenv("GOOGLE_GENAI_MODEL", DEFAULT_GAME_MODEL),
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        thinking_level=_thinking_level_from_env(
            "GOOGLE_GENAI_JUDGE_THINKING_LEVEL",
            "minimal",
        ),
    )


@lru_cache(maxsize=1)
def get_llm_pro():
    return create_chat_model(
        os.getenv("GOOGLE_GENAI_PRO_MODEL", DEFAULT_PRO_MODEL),
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
    )


@lru_cache(maxsize=1)
def get_llm_pro_backup():
    return create_chat_model(
        os.getenv("GOOGLE_GENAI_PRO_BACKUP_MODEL", DEFAULT_PRO_BACKUP_MODEL),
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        thinking_level=_thinking_level_from_env(
            "GOOGLE_GENAI_PRO_BACKUP_THINKING_LEVEL",
        ),
    )


def get_llm_dedup():
    """Cheap, deterministic model for the per-item downstream dedup agent."""
    return create_chat_model(
        os.getenv("DEDUP_MODEL", DEFAULT_DEDUP_MODEL),
        temperature=0.0,
        thinking_level=_thinking_level_from_env(
            "DEDUP_THINKING_LEVEL",
            DEFAULT_DEDUP_THINKING_LEVEL,
        ),
    )


def get_llm_batch_dedup(model: str, thinking_level: str | None):
    """Deterministic model for the batch (cluster) dedup agent. Model/thinking are
    per-run choices (single-pass model, or two-pass triage/verify), so the caller
    passes them; the factory owns only the temperature=0 dedup policy."""
    return create_chat_model(
        model,
        temperature=0.0,
        thinking_level=thinking_level,
    )


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

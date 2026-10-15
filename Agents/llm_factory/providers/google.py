"""Gemini (bare ``gemini-*`` ids): on Vertex AI (the default, Application Default Credentials) or the
Developer API with a key (``LLM_BACKEND=google``, or a game's own key), and Vertex's explicit context
cache for a prefix shared by many calls.

On Vertex, ``thinking_level`` is translated to ``thinking_budget`` (a token count): the 2.x models do
not take the string level. Gemini's cache holds the prompt text alone (the schema of a structured
call travels separately), so calls with different schemas share one cache.

The prefix cache is best effort: any failure (a non-Vertex backend, a prefix below the cache minimum,
a region without caching, auth) returns None and the caller sends the full prompt uncached. It lives
in the region the game runs in (``VERTEX_LOCATION``, default ``global``); cache hits were verified
live on ``global`` and ``us-central1`` (cache_read ~97% either way); ``EXTRACTION_CACHE_LOCATION``
stays as an escape hatch.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from logging import getLogger
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

logger = getLogger(__name__)

_DEFAULT_VERTEX_LOCATION = "global"

THINKING_LEVEL_TO_BUDGET: dict[str, int] = {
    "minimal": 128,
    "low": 1024,
    "medium": 4096,
    "high": 8192,
}

DEFAULT_EXTRACTION_CACHE_TTL_SECONDS = 900


def _use_vertex() -> bool:
    backend = os.getenv("LLM_BACKEND", "").strip().lower()
    if backend == "google":
        return False
    if backend == "vertex":
        return True
    return not bool(os.getenv("GOOGLE_API_KEY"))


def build_chat_model(model: str, *, temperature: float, thinking_level: str | None,
                     thinking_budget: int | None, game_key: str, **kwargs: Any) -> ChatGoogleGenerativeAI:
    """The chat model for a Gemini id; ``game_key`` is the game's own Developer-API key, or empty."""
    build_kwargs: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
    }

    # A per-game BYOK key forces the google (API-key) backend regardless of LLM_BACKEND:
    # the player's key is a Developer-API key, and billing the run to it is the point.
    use_vertex = not game_key and _use_vertex()
    if use_vertex:
        build_kwargs["vertexai"] = True
        build_kwargs["location"] = os.getenv(
            "VERTEX_LOCATION", _DEFAULT_VERTEX_LOCATION
        )
    else:
        api_key = game_key or os.getenv("GOOGLE_API_KEY")
        if api_key:
            build_kwargs["google_api_key"] = api_key

    if thinking_budget is not None:
        build_kwargs["thinking_budget"] = thinking_budget
    elif thinking_level:
        if use_vertex:
            budget = THINKING_LEVEL_TO_BUDGET.get(thinking_level)
            if budget is not None:
                build_kwargs["thinking_budget"] = budget
        else:
            build_kwargs["thinking_level"] = thinking_level

    build_kwargs.update(kwargs)
    return ChatGoogleGenerativeAI(**build_kwargs)


# --- Vertex's explicit prefix cache (extraction's role and cell fan-outs) ------------------------

@dataclass
class PrefixCache:
    """A live Vertex context cache + the cached 2.5-pro model bound to it.

    `model` is invoked with ONLY the role tail; Gemini prepends the cached prefix.
    """

    name: str
    model: Any

    def delete(self) -> None:
        """Best-effort delete; the cache TTL is the real backstop if this fails."""
        try:
            self.model.client.caches.delete(name=self.name)
        except Exception as e:
            logger.warning(
                "Prefix cache delete failed for %s: %s (will TTL-expire).",
                self.name,
                e,
            )


def create_prefix_cache(
    prefix: str,
    *,
    model_id: str,
    location: str | None = None,
    ttl_seconds: int | None = None,
) -> PrefixCache | None:
    """Cache `prefix` for `model_id` and return a model bound to it, or None.

    Returns None (caller falls back to the uncached full prompt) when the backend
    is not Vertex or anything in cache creation fails.
    """
    if not _use_vertex():
        logger.info("Extraction prefix caching skipped: backend is not Vertex.")
        return None

    # Same region as the rest of the game by default (verified to cache-hit on
    # global); EXTRACTION_CACHE_LOCATION is an optional pin if ever needed.
    location = (
        location
        or os.getenv("EXTRACTION_CACHE_LOCATION")
        or os.getenv("VERTEX_LOCATION", _DEFAULT_VERTEX_LOCATION)
    )
    ttl_seconds = ttl_seconds or DEFAULT_EXTRACTION_CACHE_TTL_SECONDS
    temperature = float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0"))

    try:
        from langchain_core.messages import HumanMessage
        from langchain_google_genai import ChatGoogleGenerativeAI, create_context_cache

        base = ChatGoogleGenerativeAI(
            model=model_id,
            vertexai=True,
            location=location,
            temperature=temperature,
        )
        name = create_context_cache(
            base,
            messages=[HumanMessage(content=prefix)],
            ttl=f"{ttl_seconds}s",
        )
        cached_model = ChatGoogleGenerativeAI(
            model=model_id,
            vertexai=True,
            location=location,
            temperature=temperature,
            cached_content=name,
        )
        logger.info(
            "Created extraction prefix cache %s (model=%s, location=%s, ttl=%ss).",
            name,
            model_id,
            location,
            ttl_seconds,
        )
        return PrefixCache(name=name, model=cached_model)
    except Exception as e:
        logger.warning(
            "Extraction prefix cache creation failed (%s); "
            "falling back to uncached extraction.",
            e,
        )
        return None

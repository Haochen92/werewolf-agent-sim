"""Best-effort Vertex context cache for the shared per-role extraction prefix.

The six role fan-out calls share one byte-identical prefix (~14k chars + the full
transcript). Caching it once lets the 2.5-pro calls reuse it instead of each
re-sending the whole thing — the real cost lever for per-role extraction.

Vertex-specific and ENTIRELY best-effort: any failure (non-vertex backend, below
the cache token minimum, a region that doesn't support caching, auth) returns
None / no-ops, and the caller falls back to the full uncached prompt. Caching must
never break extraction.

Region: the cache lives in the SAME location the game runs in (``VERTEX_LOCATION``,
default ``global``) so the cached 2.5-pro call routes like every other call.
Context caching + cache hits were verified live on both ``global`` and
``us-central1`` (cache_read ~97% either way), so no region pin is needed; an
optional ``EXTRACTION_CACHE_LOCATION`` override stays as an escape hatch if a
future region quirk ever needs one.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from logging import getLogger
from typing import Any

from Agents.llm_factory.backends import _DEFAULT_VERTEX_LOCATION, _use_vertex

logger = getLogger(__name__)

DEFAULT_EXTRACTION_CACHE_TTL_SECONDS = 900


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

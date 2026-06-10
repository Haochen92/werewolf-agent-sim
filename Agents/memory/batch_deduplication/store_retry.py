"""Retrying wrappers around the memory store's put/search operations (batch-only).

Both delegate to persistence's ``_memory_store_call_with_retries`` with this package's retry
constants. Embedding calls already self-retry inside the embeddings object (llm_factory's
``_RetryingGoogleGenerativeAIEmbeddings``), so this outer wrapper is a *batch-completion*
safety seam: an offline sweep does thousands of store calls and is expensive to restart, so a
transient that escapes the inner retry shouldn't abort the whole run. The per-game path skips
this layer on purpose — it fails open (store raw) rather than risk stalling a live game.
"""

from __future__ import annotations

from typing import Any

from langgraph.store.base import BaseStore

from Agents.memory.persistence import _memory_store_call_with_retries

from .config import (
    DEFAULT_MEMORY_STORE_RETRY_ATTEMPTS,
    DEFAULT_MEMORY_STORE_RETRY_INITIAL_DELAY,
    DEFAULT_MEMORY_STORE_RETRY_MAX_DELAY,
)


def _put_memory_with_retries(
    target_store: BaseStore,
    namespace: tuple[str, str, str],
    key: str,
    value: dict[str, Any],
) -> None:
    _memory_store_call_with_retries(
        lambda: target_store.put(namespace, key, value),
        operation_name="put",
        retry_attempts=DEFAULT_MEMORY_STORE_RETRY_ATTEMPTS,
        retry_initial_delay=DEFAULT_MEMORY_STORE_RETRY_INITIAL_DELAY,
        retry_max_delay=DEFAULT_MEMORY_STORE_RETRY_MAX_DELAY,
    )


def _search_memory_with_retries(
    target_store: BaseStore,
    namespace: tuple[str, str, str],
    *,
    query: str | None,
    limit: int,
    offset: int = 0,
) -> list[Any]:
    return _memory_store_call_with_retries(
        lambda: target_store.search(
            namespace,
            query=query,
            limit=limit,
            offset=offset,
        ),
        operation_name="search",
        retry_attempts=DEFAULT_MEMORY_STORE_RETRY_ATTEMPTS,
        retry_initial_delay=DEFAULT_MEMORY_STORE_RETRY_INITIAL_DELAY,
        retry_max_delay=DEFAULT_MEMORY_STORE_RETRY_MAX_DELAY,
    )

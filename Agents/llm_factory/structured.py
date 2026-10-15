"""Offline structured calls, provider-neutral: one call (``structured_call``) and many at once
(``batch_structured``), for jobs that run outside a game (extraction, de-halo, judges, synthesis).

A Claude model (``claude-*``) goes through the Anthropic SDK (providers/anthropic.py): cache marks,
an in-prompt schema when calls share a prefix under different schemas, and Message Batches at half
price. Any other model goes through its live chat model (chat.py), with its provider's own automatic
caching, and a "batch" is concurrent direct calls: no other provider's batch API is wired (Gemini's
batch mode is not built; DeepSeek and OpenRouter have none).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from typing import Any

from pydantic import BaseModel

from .providers import anthropic

logger = getLogger(__name__)


def is_claude(model: str) -> bool:
    return model.startswith("claude")


def structured_call(prompt: str, schema: type[BaseModel], model: str, *, thinking_level: str | None = None,
                    temperature: float = 1.0, cache_prefix: str | None = None, cache_ttl: str | None = None,
                    schema_in_prompt: bool = False) -> tuple[BaseModel | None, dict]:
    """The reply as ``schema`` and the call's token usage. Cache marks and the in-prompt schema apply
    to Claude only; ``temperature`` to the other providers (Claude takes none while it thinks)."""
    if is_claude(model):
        return anthropic.parse_with_claude(prompt, schema, model, thinking_level, cache_prefix=cache_prefix,
                                           cache_ttl=cache_ttl, schema_in_prompt=schema_in_prompt)
    from langchain_core.callbacks import get_usage_metadata_callback

    from .chat import create_chat_model

    llm = create_chat_model(model, temperature=temperature, thinking_level=thinking_level)
    with get_usage_metadata_callback() as cb:
        result = llm.with_structured_output(schema).invoke(prompt)
    if isinstance(result, dict):
        result = schema.model_validate(result)
    return result, dict(cb.usage_metadata)


def batch_structured(requests: dict[str, tuple], model: str, *, thinking_level: str | None = None,
                     cache_prefix: str | None = None, cache_ttl: str | None = None,
                     schema_in_prompt: bool = False, workers: int = 8) -> dict[str, BaseModel | None]:
    """Each request's reply by id ({id: (prompt, schema)} or (prompt, schema, prefix)); None where it
    failed, for the caller to retry. One Message Batch on Claude; concurrent direct calls elsewhere."""
    if is_claude(model):
        return anthropic.batch_parse(requests, model, thinking_level, cache_prefix=cache_prefix,
                                     cache_ttl=cache_ttl, schema_in_prompt=schema_in_prompt)

    def one(item: tuple[str, tuple]) -> tuple[str, BaseModel | None]:
        key, (prompt, schema, *_) = item
        try:
            return key, structured_call(prompt, schema, model, thinking_level=thinking_level)[0]
        except Exception as e:  # noqa: BLE001 — a failed request maps to None, as in a batch
            logger.warning("Structured call %s on %s failed: %s", key, model, e)
            return key, None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return dict(pool.map(one, requests.items()))

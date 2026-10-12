"""Structured-output calls to a Claude model, for the memory pipeline's Claude stages.

The de-halo pass and (when configured) strategy synthesis call Claude directly through the
Anthropic SDK rather than the game's model factory. The key is CLAUDE_API_KEY (or
ANTHROPIC_API_KEY). These calls are not traced in Langfuse, so every call's tokens are added to
``usage_totals`` for the caller to report.

Two ways to call: ``parse_with_claude`` (one call, now) and ``batch_parse`` (many calls as one
Message Batch, at half price, back within the hour as a rule; for offline runs only). Both can mark
a shared prompt prefix for caching: the text the model reads is the same, split into two blocks.
"""

from __future__ import annotations

import os
import threading
import time
from logging import getLogger
from typing import Any

from pydantic import BaseModel, TypeAdapter

logger = getLogger(__name__)

_THINKING_OFF = {"minimal", "off", "none"}
# Claude models think by default and thinking counts against max_tokens (a 46-lesson de-halo used
# about 12k), so the cap is 32k; above about 21k the SDK requires streaming unless the call sets its
# own timeout.
_MAX_TOKENS = 32000

usage_totals: dict[str, int] = {"calls": 0, "batched_calls": 0, "input_tokens": 0, "output_tokens": 0,
                                "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
# The same tokens by (model, batched), so they can be priced: a batched call bills at the batch rate.
usage_by_model: dict[tuple[str, bool], dict[str, int]] = {}
_lock = threading.Lock()


def claude_api_key() -> str | None:
    return os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")


def _client():
    import anthropic

    api_key = claude_api_key()
    if not api_key:
        raise RuntimeError("no CLAUDE_API_KEY")
    return anthropic.Anthropic(api_key=api_key)


def _thinking(thinking_level: str | None) -> dict[str, Any]:
    level = (thinking_level or "").lower()
    if level in _THINKING_OFF:
        return {"thinking": {"type": "disabled"}}
    if level:
        return {"thinking": {"type": "adaptive"}, "output_config": {"effort": level}}
    return {}


def _content(prompt: str, cache_prefix: str | None) -> str | list[dict]:
    """The prompt as one block, or as a cached prefix block and the rest when it starts with it."""
    if not cache_prefix or not prompt.startswith(cache_prefix) or len(prompt) == len(cache_prefix):
        return prompt
    return [{"type": "text", "text": cache_prefix, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": prompt[len(cache_prefix):]}]


def _count(usage, batched: bool = False, model: str = "") -> dict:
    row = {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
           "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
           "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0}
    with _lock:
        usage_totals["batched_calls" if batched else "calls"] += 1
        for k, v in row.items():
            usage_totals[k] += v
        by_model = usage_by_model.setdefault((model, batched), dict.fromkeys(row, 0))
        for k, v in row.items():
            by_model[k] += v
    return row


def usage_cost_usd() -> float | None:
    """What this process's Claude calls cost, at the catalogue's prices for today, batched calls at
    the batch rate; None if any model has no price. Anthropic's input_tokens excludes the cache read
    and the cache write, so both are added back as input (a write is priced as plain input, a quarter
    short of its 1.25x)."""
    from datetime import datetime, timezone

    from Agents.llm_factory.pricing import cost_usd

    total = 0.0
    with _lock:
        rows = list(usage_by_model.items())
    for (model, batched), u in rows:
        cached = u["cache_read_input_tokens"]
        cost = cost_usd(model, datetime.now(timezone.utc), batch=batched, cached=cached,
                        input=u["input_tokens"] + cached + u["cache_creation_input_tokens"],
                        output=u["output_tokens"])
        if cost is None:
            return None
        total += cost
    return total


def parse_with_claude(prompt: str, schema: type[BaseModel], model: str, thinking_level: str | None = None,
                      cache_prefix: str | None = None) -> tuple[BaseModel | None, dict]:
    """The parsed output and token usage of one call. Raises when there is no key."""
    response = _client().messages.parse(
        model=model, max_tokens=_MAX_TOKENS, timeout=600, output_format=schema,
        messages=[{"role": "user", "content": _content(prompt, cache_prefix)}], **_thinking(thinking_level))
    return response.parsed_output, _count(response.usage, model=model)


def batch_parse(requests: dict[str, tuple[str, type[BaseModel]]], model: str, thinking_level: str | None = None,
                cache_prefix: str | None = None, poll_seconds: int = 30) -> dict[str, BaseModel | None]:
    """Each request's parsed output, by id, from one Message Batch ({id: (prompt, schema)}). Blocks
    until the batch ends; a request that errored, expired or did not parse maps to None, for the
    caller to retry directly."""
    from anthropic.lib._parse._transform import transform_schema  # the schema transform parse() applies

    client = _client()
    thinking = _thinking(thinking_level)
    batch_requests = []
    for custom_id, (prompt, schema) in requests.items():
        output_format = {"type": "json_schema", "schema": transform_schema(TypeAdapter(schema).json_schema())}
        params: dict[str, Any] = {"model": model, "max_tokens": _MAX_TOKENS,
                                  "messages": [{"role": "user", "content": _content(prompt, cache_prefix)}],
                                  **thinking}
        params["output_config"] = {**params.get("output_config", {}), "format": output_format}
        batch_requests.append({"custom_id": custom_id, "params": params})
    batch = client.messages.batches.create(requests=batch_requests)
    logger.info("Message batch %s: %d requests on %s", batch.id, len(batch_requests), model)
    while batch.processing_status != "ended":
        time.sleep(poll_seconds)
        batch = client.messages.batches.retrieve(batch.id)
    out: dict[str, BaseModel | None] = dict.fromkeys(requests)
    for result in client.messages.batches.results(batch.id):
        if result.result.type != "succeeded":
            logger.warning("Batch %s request %s: %s", batch.id, result.custom_id, result.result.type)
            continue
        message = result.result.message
        _count(message.usage, batched=True, model=model)
        text = next((b.text for b in message.content if b.type == "text"), "")
        try:
            out[result.custom_id] = requests[result.custom_id][1].model_validate_json(text)
        except Exception as e:  # noqa: BLE001 — a reply that does not parse is retried by the caller
            logger.warning("Batch %s request %s did not parse (%s): %s", batch.id, result.custom_id,
                           message.stop_reason, e)
    return out

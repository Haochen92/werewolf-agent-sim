"""Structured-output calls to a Claude model, for the memory pipeline's Claude stages.

The de-halo pass and (when configured) strategy synthesis call Claude directly through the
Anthropic SDK rather than the game's model factory. The key is CLAUDE_API_KEY (or
ANTHROPIC_API_KEY). These calls bypass LangChain, so each one is recorded in Langfuse here (``_trace``,
with its cost, a batched call at the batch rate), and its tokens are added to ``usage_totals``.

Two ways to call: ``parse_with_claude`` (one call, now) and ``batch_parse`` (many calls as one
Message Batch, at half price, back within the hour as a rule; for offline runs only). Both can mark
a shared prompt prefix for caching: the text the model reads is the same, split into two blocks. A
batch runs its requests in no set order, so a prefix shared within it is cached only once a request
has written it; a caller can write it first with a direct call and the 1-hour cache (``cache_ttl``).

The enforced output schema is part of Claude's cache key: calls that share a prefix under different
schemas never read each other's cache (measured 2026-10-12, evidence/memory_system/v8/experiment_log.md).
A fan-out with a schema per call passes ``schema_in_prompt``: the schema goes as text after the cached
part, the reply is parsed and validated here, and a reply that does not validate is retried once with
the schema enforced.
"""

from __future__ import annotations

import json
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

usage_totals: dict[str, int] = {"calls": 0, "batched_calls": 0, "unvalidated_replies": 0,
                                "input_tokens": 0, "output_tokens": 0,
                                "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                                "cache_creation_1h_input_tokens": 0}
# A cache write bills above the input rate: 1.25x for the 5-minute cache, 2x for the 1-hour one.
_WRITE_FACTOR_5M, _WRITE_FACTOR_1H = 1.25, 2.0
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


def _thinking(thinking_level: str | None, model: str = "") -> dict[str, Any]:
    from Agents.llm_factory.backends import _CLAUDE_THINKING_OFF

    level = (thinking_level or "").lower()
    if level in _THINKING_OFF:
        # Sonnet 5.5 refuses "disabled"; its off is "between_tools" (backends). No temperature here.
        off = _CLAUDE_THINKING_OFF.get(model, {"thinking": {"type": "disabled"}})
        return {"thinking": off["thinking"]}
    if level:
        return {"thinking": {"type": "adaptive"}, "output_config": {"effort": level}}
    return {}


def _content(prompt: str, cache_prefix: str | None, cache_ttl: str | None = None) -> str | list[dict]:
    """The prompt as one block, or as a cached prefix block and the rest when it starts with it.
    ``cache_ttl`` "1h" keeps the prefix an hour (written at twice the input rate, not 1.25x)."""
    if not cache_prefix or not prompt.startswith(cache_prefix) or len(prompt) == len(cache_prefix):
        return prompt
    control = {"type": "ephemeral", **({"ttl": cache_ttl} if cache_ttl else {})}
    return [{"type": "text", "text": cache_prefix, "cache_control": control},
            {"type": "text", "text": prompt[len(cache_prefix):]}]


_SCHEMA_INSTRUCTION = ("\n\nReply with only one JSON object that matches this JSON schema, with no other "
                       "text before or after it:\n{schema}")


def _with_schema(prompt: str, schema: type[BaseModel]) -> str:
    """The prompt with the schema written after it, so it sits after any cached prefix."""
    return prompt + _SCHEMA_INSTRUCTION.format(
        schema=json.dumps(TypeAdapter(schema).json_schema(), separators=(",", ":")))


def _validated(text: str, schema: type[BaseModel]) -> BaseModel | None:
    """The reply as ``schema``, or None (and counted) when it is not one JSON object that validates.
    A fenced block or text around the object is tolerated."""
    start, end = text.find("{"), text.rfind("}")
    try:
        return schema.model_validate_json(text[start:end + 1])
    except Exception:  # noqa: BLE001 — the caller retries with the schema enforced
        with _lock:
            usage_totals["unvalidated_replies"] += 1
        return None


def _count(usage, batched: bool = False, model: str = "") -> dict:
    split = getattr(usage, "cache_creation", None)
    row = {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
           "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
           "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
           "cache_creation_1h_input_tokens": getattr(split, "ephemeral_1h_input_tokens", 0) or 0}
    with _lock:
        usage_totals["batched_calls" if batched else "calls"] += 1
        for k, v in row.items():
            usage_totals[k] += v
        by_model = usage_by_model.setdefault((model, batched), dict.fromkeys(row, 0))
        for k, v in row.items():
            by_model[k] += v
    _trace(row, batched, model)
    return row


def _trace(row: dict, batched: bool, model: str) -> None:
    """Record the call in Langfuse as a generation (under the active trace, if any), with its tokens by
    type and the cost worked out here, a batched call at the batch rate. These calls bypass LangChain,
    so nothing else traces them. Never raises: tracing must not fail a call."""
    try:
        from datetime import datetime, timezone

        from Agents.llm_factory.pricing import cost_usd
        from Agents.tracing import langfuse

        cached, written = row["cache_read_input_tokens"], row["cache_creation_input_tokens"]
        usd = _cost(model, datetime.now(timezone.utc), batched, row)
        generation = langfuse.start_observation(
            as_type="generation", name="claude_batch_call" if batched else "claude_call", model=model,
            metadata={"batched": batched},
            usage_details={"input": row["input_tokens"], "input_cache_read": cached,
                           "input_cache_creation": written, "output": row["output_tokens"]},
            cost_details={"total": usd} if usd is not None else None)
        generation.end()
    except Exception:  # noqa: BLE001
        logger.debug("Langfuse trace of a Claude call failed", exc_info=True)


def _cost(model: str, at, batched: bool, u: dict) -> float | None:
    """What one usage row cost. Anthropic's input_tokens excludes the cache read and the cache write,
    so both are added back as input; a write's premium over the input rate (a quarter for the
    5-minute cache, as much again for the 1-hour one) is added on top."""
    from Agents.llm_factory.pricing import cost_usd

    cached, written = u["cache_read_input_tokens"], u["cache_creation_input_tokens"]
    written_1h = u.get("cache_creation_1h_input_tokens", 0)
    base = cost_usd(model, at, batch=batched, cached=cached, input=u["input_tokens"] + cached + written,
                    output=u["output_tokens"])
    premium = cost_usd(model, at, batch=batched, cached=0, output=0,
                       input=round((written - written_1h) * (_WRITE_FACTOR_5M - 1) + written_1h * (_WRITE_FACTOR_1H - 1)))
    return None if base is None or premium is None else base + premium


def usage_cost_usd() -> float | None:
    """What this process's Claude calls cost, at the catalogue's prices for today, batched calls at
    the batch rate, cache writes at their premium; None if any model has no price."""
    from datetime import datetime, timezone

    total = 0.0
    with _lock:
        rows = list(usage_by_model.items())
    for (model, batched), u in rows:
        cost = _cost(model, datetime.now(timezone.utc), batched, u)
        if cost is None:
            return None
        total += cost
    return total


def parse_with_claude(prompt: str, schema: type[BaseModel], model: str, thinking_level: str | None = None,
                      cache_prefix: str | None = None, cache_ttl: str | None = None,
                      schema_in_prompt: bool = False) -> tuple[BaseModel | None, dict]:
    """The parsed output and token usage of one call. Raises when there is no key. With
    ``schema_in_prompt``, a reply that does not validate is asked for again with the schema enforced
    (the usage returned is the last call's)."""
    if schema_in_prompt:
        response = _client().messages.create(
            model=model, max_tokens=_MAX_TOKENS, timeout=600,
            messages=[{"role": "user", "content": _content(_with_schema(prompt, schema), cache_prefix, cache_ttl)}],
            **_thinking(thinking_level, model))
        usage = _count(response.usage, model=model)
        parsed = _validated(next((b.text for b in response.content if b.type == "text"), ""), schema)
        if parsed is not None:
            return parsed, usage
    response = _client().messages.parse(
        model=model, max_tokens=_MAX_TOKENS, timeout=600, output_format=schema,
        messages=[{"role": "user", "content": _content(prompt, cache_prefix, cache_ttl)}],
        **_thinking(thinking_level, model))
    return response.parsed_output, _count(response.usage, model=model)


def batch_parse(requests: dict[str, tuple], model: str, thinking_level: str | None = None,
                cache_prefix: str | None = None, poll_seconds: int = 30,
                cache_ttl: str | None = None, schema_in_prompt: bool = False) -> dict[str, BaseModel | None]:
    """Each request's parsed output, by id, from one Message Batch ({id: (prompt, schema)}, or
    (prompt, schema, prefix) to mark that request's own cached prefix instead of ``cache_prefix``).
    Blocks until the batch ends; a request that errored, expired or did not parse maps to None, for
    the caller to retry directly (with ``schema_in_prompt``, best with the schema enforced)."""
    from anthropic.lib._parse._transform import transform_schema  # the schema transform parse() applies

    client = _client()
    thinking = _thinking(thinking_level, model)
    batch_requests = []
    for custom_id, (prompt, schema, *own_prefix) in requests.items():
        prefix = own_prefix[0] if own_prefix else cache_prefix
        text = _with_schema(prompt, schema) if schema_in_prompt else prompt
        params: dict[str, Any] = {"model": model, "max_tokens": _MAX_TOKENS,
                                  "messages": [{"role": "user", "content": _content(text, prefix, cache_ttl)}],
                                  **thinking}
        if not schema_in_prompt:
            output_format = {"type": "json_schema", "schema": transform_schema(TypeAdapter(schema).json_schema())}
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
        schema = requests[result.custom_id][1]
        if schema_in_prompt:
            out[result.custom_id] = _validated(text, schema)
            continue
        try:
            out[result.custom_id] = schema.model_validate_json(text)
        except Exception as e:  # noqa: BLE001 — a reply that does not parse is retried by the caller
            logger.warning("Batch %s request %s did not parse (%s): %s", batch.id, result.custom_id,
                           message.stop_reason, e)
    return out

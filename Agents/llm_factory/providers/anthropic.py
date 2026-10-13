"""Claude (``anthropic/`` models in the game factory; ``claude-*`` ids in direct calls).

Two halves. **Seats** (LangChain, live): ``ClaudeChat`` and ``build_chat_model``. **Direct calls**
(the Anthropic SDK, offline): ``parse_with_claude`` (one call, now) and ``batch_parse`` (many calls as
one Message Batch, at half price, back within the hour as a rule), with cache marks, in-prompt
schemas, usage totals and cost. The key is CLAUDE_API_KEY (or ANTHROPIC_API_KEY for direct calls).

Seats. Two things differ from the OpenAI-protocol rows. Structured output: a forced tool call cannot
be combined with thinking, so a thinking seat answers through Claude's own JSON-schema output.
Caching: Claude caches only where a request marks a cache point, and a later request reuses a cached
prefix only when that prefix ends on a piece boundary of its own prompt, at most 20 pieces back from
its mark. A turn's prompt is a fixed system message and one message holding the transcript, which
grows from turn to turn, then the turn's brief. So the system message is marked, and the message is
sent one line per piece with a mark on the transcript's last line: the seat's next turn, its
transcript a few lines longer, finds the previous turn's mark among its pieces.

Direct calls bypass LangChain, so each one is recorded in Langfuse here (``_trace``, with its cost, a
batched call at the batch rate), and its tokens are added to ``usage_totals``. Both ways of calling
can mark a shared prompt prefix for caching: the text the model reads is the same, split into two
blocks. A batch runs its requests in no set order, so a prefix shared within it is cached only once a
request has written it; a caller can write it first with a direct call and the 1-hour cache
(``cache_ttl``). The enforced output schema is part of Claude's cache key: calls that share a prefix
under different schemas never read each other's cache (measured 2026-10-12,
evidence/memory_system/v8/experiment_log.md). A fan-out with a schema per call passes
``schema_in_prompt``: the schema goes as text after the cached part and the reply is validated
here; ``parse_with_claude`` then asks again with the schema enforced, and a batch's caller retries.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, TypeAdapter

from .common import _first_tool_call, _parse_json_reply, _schema_instruction

logger = logging.getLogger(__name__)


# --- Seats (LangChain) -------------------------------------------------------------------------

_MARK = {"type": "ephemeral"}
# The rule under every prompt's transcript (day_discuss, day_vote, night).
_TRANSCRIPT_RULE = re.compile(r"^={20,}$", re.MULTILINE)


def _line_pieces(text: str) -> list[dict[str, Any]]:
    """The text one line per piece; a blank line rides with the line before it (the API refuses a
    piece of whitespace). The same text is always cut the same way, so a longer transcript keeps
    the pieces of the shorter one."""
    pieces: list[str] = []
    for line in text.splitlines(keepends=True):
        if pieces and not line.strip():
            pieces[-1] += line
        else:
            pieces.append(line)
    return [{"type": "text", "text": p} for p in pieces]


def _marked_message(text: str) -> list[dict[str, Any]] | None:
    """The message as line pieces, marked on the transcript's last line; None with no transcript."""
    rules = list(_TRANSCRIPT_RULE.finditer(text))
    if not rules:
        return None
    head, tail = text[: rules[-1].start()], text[rules[-1].start():]
    if not head.strip():
        return None
    pieces = _line_pieces(head)
    pieces[-1]["cache_control"] = _MARK
    return [*pieces, {"type": "text", "text": tail}]


class ClaudeChat(ChatAnthropic):
    """ChatAnthropic with the cache marks above and ``structured_mode`` (common.STRUCTURED_MODES):
    forced_tool, json_schema, auto_tool, and json_mode, which on Claude is the schema as text with
    no output switch (Claude has no JSON mode)."""

    structured_mode: str = "forced_tool"

    def _get_request_payload(self, input_: Any, *, stop: list[str] | None = None, **kwargs: Any) -> dict:
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        system = payload.get("system")
        if isinstance(system, str) and system:
            payload["system"] = [{"type": "text", "text": system, "cache_control": _MARK}]
        elif isinstance(system, list) and system:
            system[-1]["cache_control"] = _MARK
        last = payload["messages"][-1] if payload.get("messages") else None
        if last and last["role"] == "user" and isinstance(last["content"], str):
            if (marked := _marked_message(last["content"])) is not None:
                last["content"] = marked
        return payload

    def _format_output(self, data: Any, **kwargs: Any) -> Any:
        # Langfuse's LangChain handler reads Anthropic's raw usage first, whose input_tokens leaves out
        # the cache reads and writes, so a cached turn traced as ~1,000 input tokens of ~10,000. With
        # the raw block kept under another key it reads the message's usage_metadata, which counts
        # them, and records the reads and writes as their own token types.
        result = super()._format_output(data, **kwargs)
        if result.llm_output and "usage" in result.llm_output:
            result.llm_output["anthropic_usage"] = result.llm_output.pop("usage")
        return result

    def with_structured_output(self, schema: Any = None, **kwargs: Any) -> Any:
        if "method" in kwargs or not isinstance(schema, type):
            return super().with_structured_output(schema, **kwargs)
        if self.structured_mode == "json_schema":
            return super().with_structured_output(schema, method="json_schema", **kwargs)
        if self.structured_mode == "auto_tool":
            bound = self.bind_tools([schema], tool_choice="auto")
            return bound | RunnableLambda(lambda m: _first_tool_call(schema, m))
        if self.structured_mode == "json_mode":
            # An enforced schema is part of Claude's cache key, so one that differs per seat or per call
            # type stops calls sharing a prefix. Here the schema rides as text at the end of the last user
            # message, after the cache marks (a separate message would be merged into it and lose the
            # transcript's mark), and the reply is validated in code against the same schema.
            instruction = _schema_instruction(schema)

            def with_instruction(prompt: Any) -> list:
                messages = list(self._convert_input(prompt).to_messages())
                last = messages[-1] if messages else None
                if isinstance(last, HumanMessage) and isinstance(last.content, str):
                    messages[-1] = HumanMessage(last.content + "\n\n" + instruction)
                else:
                    messages.append(HumanMessage(instruction))
                return messages

            return RunnableLambda(with_instruction) | self | RunnableLambda(lambda m: _parse_json_reply(schema, m))
        return super().with_structured_output(schema, method="function_calling", **kwargs)


# A Claude model with thinking off, where the default request is refused (2026-10-12, Sonnet 5.5 as
# the golden judge): it answers "thinking disabled" with a 400 asking for "between_tools", and takes no
# temperature (and no forced tool call: its catalogue row's structured_mode).
_CLAUDE_THINKING_OFF: dict[str, dict[str, Any]] = {
    "claude-sonnet-5-5": {"thinking": {"type": "between_tools"}},
    # Haiku 5.5 takes "disabled" but answers a temperature with a 400 (2026-10-12, a judge's call).
    "claude-haiku-5-5": {"thinking": {"type": "disabled"}},
}


def build_chat_model(model: str, *, temperature: float, thinking_level: str | None, mode: str,
                     game_key: str) -> ClaudeChat:
    """A Claude seat. Thinking is adaptive, steered by the effort level; "minimal" or none turns it
    off. A forced tool call cannot be combined with thinking, so in forced_tool mode thinking stays
    off, as on DeepSeek. Claude takes no temperature while thinking. ``game_key`` is the game's own
    key, or empty."""
    api_key = game_key or os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not set")
    thinking = thinking_level not in (None, "minimal") and mode != "forced_tool"
    if thinking_level not in (None, "minimal") and not thinking:
        logger.info("Claude: thinking_level=%s ignored (forced tool calling is incompatible "
                    "with thinking).", thinking_level)
    extra: dict[str, Any] = (
        {"thinking": {"type": "adaptive"}, "effort": thinking_level} if thinking
        else _CLAUDE_THINKING_OFF.get(model) or {"thinking": {"type": "disabled"}, "temperature": temperature})
    return ClaudeChat(model=model, api_key=api_key, max_tokens=16_000, structured_mode=mode, **extra)


# --- Direct calls (the Anthropic SDK) ----------------------------------------------------------

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
    level = (thinking_level or "").lower()
    if level in _THINKING_OFF:
        # Sonnet 5.5 refuses "disabled"; its off is "between_tools" (above). No temperature here.
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
    except Exception as e:  # noqa: BLE001 — the caller retries
        with _lock:
            usage_totals["unvalidated_replies"] += 1
        logger.warning("Reply did not validate as %s: %s", schema.__name__, str(e).replace("\n", " ")[:300])
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

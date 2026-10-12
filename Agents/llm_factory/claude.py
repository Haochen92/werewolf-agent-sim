"""Claude seats (Anthropic's API), the factory's ``anthropic/`` models.

Two things differ from the OpenAI-protocol rows. Structured output: a forced tool call cannot be
combined with thinking, so a thinking seat answers through Claude's own JSON-schema output.
Caching: Claude caches only where a request marks a cache point, and a later request reuses a
cached prefix only when that prefix ends on a piece boundary of its own prompt, at most 20 pieces
back from its mark. A turn's prompt is a fixed system message and one message holding the
transcript, which grows from turn to turn, then the turn's brief. So the system message is marked,
and the message is sent one line per piece with a mark on the transcript's last line: the seat's
next turn, its transcript a few lines longer, finds the previous turn's mark among its pieces.
"""

from __future__ import annotations

import re
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.runnables import RunnableLambda

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
    """ChatAnthropic with the cache marks above and ``structured_mode`` (backends.STRUCTURED_MODES):
    forced_tool, json_schema and auto_tool; Claude has no JSON mode."""

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
            from .backends import _first_tool_call

            bound = self.bind_tools([schema], tool_choice="auto")
            return bound | RunnableLambda(lambda m: _first_tool_call(schema, m))
        if self.structured_mode == "json_mode":
            raise ValueError("Claude has no JSON mode: use json_schema")
        return super().with_structured_output(schema, method="function_calling", **kwargs)

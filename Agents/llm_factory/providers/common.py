"""Structured output shared by more than one provider: the modes a model can be asked for a
schema-shaped answer in, and the parsers of a JSON reply and of a tool call."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.exceptions import OutputParserException

# How an OpenAI-protocol (or Claude) model is asked for a schema-shaped answer (Gemini always uses its
# own constrained output). Every caller just calls ``with_structured_output(schema)``; the mode
# decides what that sends:
#   forced_tool  the schema as a tool the model must call. Reliable, but DeepSeek's thinking
#                mode rejects any forced tool_choice (HTTP 400), so it means thinking off there.
#   json_schema  the provider's native structured output (response_format json_schema, strict):
#                its decoder cannot produce an invalid reply, and it works with reasoning where
#                the provider supports it (OpenAI, Alibaba; DeepSeek 400s it).
#   auto_tool    the schema as a tool the model may call. Works with thinking on; a reply
#                that answers in prose instead is a parse failure, which the seat retries.
#   json_mode    no tool: a trailing instruction carries the JSON schema, the provider's JSON
#                output mode is on, and the reply is validated here. Also works with thinking.
# Probed on DeepSeek V4 Flash 2026-10-04 (one call each): thinking + forced or "required"
# tool_choice → 400; thinking + auto → tool called; thinking + JSON mode → valid JSON.
STRUCTURED_MODES = ("forced_tool", "json_schema", "auto_tool", "json_mode")
# A model's mode is its catalogue row's structured_mode (catalog.py), chosen by the model admission
# run (eval-model-admission); a model with none uses forced_tool, which is what every
# OpenAI-protocol row played on first.


def _schema_instruction(schema: type) -> str:
    return ("Answer with only a JSON object, no prose and no code fence, that matches this JSON "
            "schema:\n" + json.dumps(schema.model_json_schema(), separators=(",", ":")))


def _parse_json_reply(schema: type, message: Any) -> Any:
    """The reply's JSON validated against the schema; a parse failure raises, so the seat retries."""
    text = (message.content if isinstance(message.content, str) else str(message.content)).strip()
    if text.startswith("```"):  # tolerated even though asked against: it carries no ambiguity
        text = text.strip("`").removeprefix("json").strip()
    try:
        return schema.model_validate_json(text)
    except ValueError as e:
        raise OutputParserException(f"reply is not a valid {schema.__name__}: {e}", llm_output=text) from e


def _first_tool_call(schema: type, message: Any) -> Any:
    """The tool call's arguments validated against the schema; no tool call raises."""
    for call in getattr(message, "tool_calls", None) or []:
        if call.get("name") == schema.__name__:
            return schema.model_validate(call.get("args") or {})
    raise OutputParserException(f"the model answered without calling {schema.__name__}",
                                llm_output=str(message.content)[:500])

"""The OpenAI protocol: NVIDIA NIM (``nim/``), DeepSeek (``deepseek/``), OpenAI (``openai/``),
OpenRouter (``openrouter/``) and xAI (``xai/``), all through LangChain's ChatOpenAI.

Structured output follows the model's ``structured_mode`` (common.STRUCTURED_MODES). Caching is the
provider's own and automatic on a repeated prefix (DeepSeek's is best effort, on disk; OpenRouter
passes Claude-style cache marks on and keeps a cached request's follow-ups on the same host). None
of these has a batch API wired here (DeepSeek has none; its off-peak hours are half price).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI

from .common import _first_tool_call, _parse_json_reply, _schema_instruction, split_at_transcript

logger = logging.getLogger(__name__)

_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
_OPENAI_BASE_URL = "https://api.openai.com/v1"
_XAI_BASE_URL = "https://api.x.ai/v1"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# OpenRouter serves most open-weight models from many hosts at different prices, precisions and
# cache behaviour, and a fallback to another host loses the warm cache. So each model family is
# pinned to its maker's own servers (OpenRouter's provider slugs, read 2026-10-04); a family with
# no entry here is refused rather than left to OpenRouter's routing.
OPENROUTER_PROVIDER = {
    "qwen/": "alibaba",
    "z-ai/": "z-ai",
    "minimax/": "minimax",
    "openai/": "openai",
}
# Families where an effort level caps thinking instead of setting it, and reasoning cannot be
# turned off: GLM-5.3 Flash on Z.AI reasoned 8–26 tokens at effort low/medium/high, 1,100–1,700
# with {"enabled": true}, and refused {"enabled": false} (probe 2026-10-04). So "minimal" and
# "low" get effort low (its lightest, ~8 tokens) and "medium"/"high" get the plain switch.
OPENROUTER_REASONING_SWITCH_ONLY = ("z-ai/",)

PREFIXES = ("nim/", "deepseek/", "openai/", "openrouter/", "xai/")

# OpenAI models that take explicit cache breakpoints (GPT-5.6 on; prompt-caching guide, read
# 2026-10-13). In the shared-prefix prompt layout they get prompt_cache_options mode "explicit" and a
# breakpoint on the system message and on each line of the public record: a later turn, or another
# seat, then reads the record up to the earlier turn's last line (probe 2026-10-13: a seat's next
# turn read 2,561 of 2,678 tokens, another seat 2,648 of 2,674), and the changing private part is
# never written at the 1.25x write rate, as the implicit breakpoint writes it.
EXPLICIT_CACHE_MODELS = ("gpt-6",)
# OpenAI matches against the latest 80 breakpoints of a request and writes the latest four.
_MAX_BREAKPOINTS = 80
_BREAKPOINT = {"mode": "explicit"}


def mark_explicit_breakpoints(payload: dict[str, Any]) -> None:
    """Breakpoints on the system message and on the lines of the user message's public record (the
    text before its transcript rule); the request switched to explicit-only caching. In place."""
    for message in payload.get("messages") or []:
        if message.get("role") == "system" and isinstance(message.get("content"), str):
            message["content"] = [{"type": "text", "text": message["content"],
                                   "prompt_cache_breakpoint": dict(_BREAKPOINT)}]
            break
    for message in reversed(payload.get("messages") or []):
        content = message.get("content")
        if message.get("role") != "user" or not isinstance(content, str):
            continue
        split = split_at_transcript(content)
        if split is None:
            continue
        pieces, tail = split
        for piece in pieces[-_MAX_BREAKPOINTS:]:
            piece["prompt_cache_breakpoint"] = dict(_BREAKPOINT)
        message["content"] = [*pieces, {"type": "text", "text": tail}]
        break
    extra = dict(payload.get("extra_body") or {})
    extra["prompt_cache_options"] = {"mode": "explicit"}
    payload["extra_body"] = extra


class _ToolCallStructuredChatOpenAI(ChatOpenAI):
    """ChatOpenAI whose ``with_structured_output`` follows ``structured_mode`` (common.py).

    LangChain's default method is ``json_schema`` (the OpenAI ``response_format``),
    which OpenAI-compatible providers don't reliably serve — DeepSeek 400s it
    outright — so the default here is forced tool calling. Callers that pass an
    explicit ``method=`` still win.
    """

    structured_mode: str = "forced_tool"

    def _get_request_payload(self, input_: Any, *, stop: list[str] | None = None, **kwargs: Any) -> dict:
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        from Agents.prompts.layout import shared_prefix

        if shared_prefix() and self.model_name.startswith(EXPLICIT_CACHE_MODELS):
            mark_explicit_breakpoints(payload)
        return payload

    def with_structured_output(self, schema=None, **kwargs):
        if "method" in kwargs or self.structured_mode == "forced_tool" or not isinstance(schema, type):
            kwargs.setdefault("method", "function_calling")
            return super().with_structured_output(schema, **kwargs)
        if self.structured_mode == "json_schema":
            return super().with_structured_output(schema, method="json_schema", strict=True, **kwargs)
        if self.structured_mode == "auto_tool":
            bound = self.bind_tools([schema], tool_choice="auto")
            return bound | RunnableLambda(lambda m: _first_tool_call(schema, m))
        instruction = _schema_instruction(schema)

        def with_instruction(prompt: Any) -> list:
            # Appended last, so the cached prefix of the prompt is unchanged.
            return [*self._convert_input(prompt).to_messages(), HumanMessage(instruction)]

        bound = self.bind(response_format={"type": "json_object"})
        return RunnableLambda(with_instruction) | bound | RunnableLambda(lambda m: _parse_json_reply(schema, m))


def _build_openai_compat_chat_model(
    model: str, base_url: str, key_env: str, *, temperature: float = 0.0,
    api_key_override: str = "", **kwargs: Any
) -> ChatOpenAI:
    """OpenAI-protocol providers (NVIDIA NIM, DeepSeek) via LangChain's ChatOpenAI.

    A real ChatModel — not the thin ``.invoke()``-only wrapper Mistral still uses —
    because game seats bind Pydantic schemas via ``with_structured_output``, which
    rides the provider's tool-calling support.
    """
    api_key = api_key_override or os.getenv(key_env)
    if not api_key:
        raise ValueError(f"{key_env} not set")
    return _ToolCallStructuredChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        **kwargs,
    )


def build_chat_model(model: str, *, temperature: float, thinking_level: str | None, mode: str,
                     game_key: str) -> ChatOpenAI:
    """The chat model for an OpenAI-protocol id (one of ``PREFIXES``); ``game_key`` is the game's own
    key for this provider, or empty."""
    if model.startswith("nim/"):
        return _build_openai_compat_chat_model(
            model.removeprefix("nim/"), _NIM_BASE_URL, "NVIDIA_API_KEY",
            temperature=temperature, structured_mode=mode, api_key_override=game_key,
        )

    if model.startswith("deepseek/"):
        # V4's thinking mode rejects the forced tool_choice of forced_tool mode (a thinking seat
        # 400s on its first turn; seen live with the summary agent's "medium" level). So thinking
        # is on only when asked for AND the model's mode doesn't force the tool call.
        thinking = thinking_level not in (None, "minimal") and mode != "forced_tool"
        if thinking_level not in (None, "minimal") and not thinking:
            logger.info(
                "DeepSeek: thinking_level=%s ignored (forced tool calling is incompatible "
                "with thinking mode).", thinking_level,
            )
        return _build_openai_compat_chat_model(
            model.removeprefix("deepseek/"), _DEEPSEEK_BASE_URL, "DEEPSEEK_API_KEY",
            temperature=temperature, structured_mode=mode, api_key_override=game_key,
            extra_body={"thinking": {"type": "enabled" if thinking else "disabled"}},
        )

    # OpenAI and xAI (Grok) speak the OpenAI protocol; structured output rides tool calling, as
    # for DeepSeek. Wired for offline evaluation (the hallucination bench's arms), not game seats.
    if model.startswith("openai/"):
        # Reasoning models take an effort level; "minimal" means off, as elsewhere (GPT-6 Luna
        # takes none / low / medium / high / xhigh and rejects "minimal").
        effort = ({"reasoning_effort": "none" if thinking_level == "minimal" else thinking_level}
                  if thinking_level else {})
        return _build_openai_compat_chat_model(
            model.removeprefix("openai/"), _OPENAI_BASE_URL, "OPENAI_API_KEY",
            temperature=temperature, structured_mode=mode, api_key_override=game_key, **effort)

    if model.startswith("openrouter/"):
        routed = model.removeprefix("openrouter/")
        provider = next((v for k, v in OPENROUTER_PROVIDER.items() if routed.startswith(k)), None)
        if provider is None:
            raise ValueError(f"{model}: no pinned OpenRouter provider for this model family")
        extra: dict[str, Any] = {"provider": {"order": [provider], "allow_fallbacks": False}}
        if thinking_level:
            # OpenRouter's one reasoning switch across providers; "minimal" means off, as on DeepSeek.
            if routed.startswith(OPENROUTER_REASONING_SWITCH_ONLY):
                extra["reasoning"] = ({"effort": "low"} if thinking_level in ("minimal", "low")
                                      else {"enabled": True})
            else:
                extra["reasoning"] = ({"enabled": False} if thinking_level == "minimal"
                                      else {"effort": thinking_level})
        return _build_openai_compat_chat_model(
            routed, _OPENROUTER_BASE_URL, "OPENROUTER_API_KEY",
            temperature=temperature, structured_mode=mode, extra_body=extra, api_key_override=game_key)

    if model.startswith("xai/"):
        return _build_openai_compat_chat_model(
            model.removeprefix("xai/"), _XAI_BASE_URL, "XAI_API_KEY",
            temperature=temperature, structured_mode=mode, api_key_override=game_key)

    raise ValueError(f"{model} is not an OpenAI-protocol model ({', '.join(PREFIXES)})")

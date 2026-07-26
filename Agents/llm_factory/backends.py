"""Chat-model construction across the five supported backends.

vertex (default) / google (API-key) / nim / deepseek / mistral — selected by ``LLM_BACKEND``
and the model prefix. Instances are memoised by construction args (building one is
non-trivial: client + auth setup), so callers in hot loops reuse a shared,
thread-safe instance. See the package docstring for backend selection rules.
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

# Chat-model instances are immutable after construction and safe to reuse across
# threads (the underlying SDK/httpx clients are thread-safe). Memoize by
# construction args — callers in hot loops would otherwise rebuild per call.
_MODEL_CACHE: dict[Any, Any] = {}
_MODEL_CACHE_LOCK = threading.Lock()

_DEFAULT_VERTEX_LOCATION = "global"

THINKING_LEVEL_TO_BUDGET: dict[str, int] = {
    "minimal": 128,
    "low": 1024,
    "medium": 4096,
    "high": 8192,
}


_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
_MISTRAL_BASE_URL = "https://api.mistral.ai/v1"


@dataclass
class _OpenAICompatResponse:
    content: str


class _ToolCallStructuredChatOpenAI(ChatOpenAI):
    """ChatOpenAI whose ``with_structured_output`` defaults to tool calling.

    LangChain's default method is ``json_schema`` (the OpenAI ``response_format``),
    which OpenAI-compatible providers don't reliably serve — DeepSeek 400s it
    outright — while their tool-calling path is solid. Callers that pass an
    explicit ``method=`` still win.
    """

    def with_structured_output(self, schema=None, **kwargs):
        kwargs.setdefault("method", "function_calling")
        return super().with_structured_output(schema, **kwargs)


def _build_openai_compat_chat_model(
    model: str, base_url: str, key_env: str, *, temperature: float = 0.0, **kwargs: Any
) -> ChatOpenAI:
    """OpenAI-protocol providers (NVIDIA NIM, DeepSeek) via LangChain's ChatOpenAI.

    A real ChatModel — not the thin ``.invoke()``-only wrapper Mistral still uses —
    because game seats bind Pydantic schemas via ``with_structured_output``, which
    rides the provider's tool-calling support.
    """
    api_key = os.getenv(key_env)
    if not api_key:
        raise ValueError(f"{key_env} not set")
    return _ToolCallStructuredChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        **kwargs,
    )


class MistralChatModel:
    """Thin wrapper around Mistral API with LangChain-compatible .invoke()."""

    def __init__(self, model: str, *, temperature: float = 0.0):
        from openai import OpenAI

        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY not set")
        self._client = OpenAI(base_url=_MISTRAL_BASE_URL, api_key=api_key)
        self._model = model
        self._temperature = temperature

    def invoke(self, prompt: str) -> _OpenAICompatResponse:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
        )
        return _OpenAICompatResponse(content=response.choices[0].message.content)


def _use_vertex() -> bool:
    backend = os.getenv("LLM_BACKEND", "").strip().lower()
    if backend == "google":
        return False
    if backend == "vertex":
        return True
    return not bool(os.getenv("GOOGLE_API_KEY"))


def create_chat_model(
    model: str,
    *,
    temperature: float = 0.0,
    thinking_level: str | None = None,
    thinking_budget: int | None = None,
    **kwargs: Any,
) -> ChatGoogleGenerativeAI | ChatOpenAI:
    """Create (or reuse) a chat model using the configured backend.

    Instances are memoized by construction args (see ``_MODEL_CACHE``); repeated
    calls with the same args return the same shared, thread-safe instance.

    Parameters
    ----------
    model:
        Model identifier.  Use ``"nim/<org>/<model>"`` for NVIDIA NIM
        (e.g. ``"nim/deepseek-ai/deepseek-v4-flash"``), otherwise a
        Gemini model name (e.g. ``"gemini-2.5-flash"``).
    temperature:
        Sampling temperature.
    thinking_level:
        Symbolic thinking level (``"minimal"``, ``"low"``, ``"medium"``,
        ``"high"``).  Ignored for NIM/DeepSeek models.
    thinking_budget:
        Explicit thinking token budget.  Takes precedence over
        ``thinking_level`` when both are provided.  Ignored for NIM/DeepSeek models.
    **kwargs:
        Forwarded to ``ChatGoogleGenerativeAI`` (ignored for NIM/DeepSeek).
    """
    try:
        cache_key: Any = (
            model, temperature, thinking_level, thinking_budget,
            tuple(sorted(kwargs.items())),
        )
        hash(cache_key)
    except TypeError:
        cache_key = None  # unhashable kwargs -> bypass cache
    if cache_key is not None and (cached := _MODEL_CACHE.get(cache_key)) is not None:
        return cached

    instance = _build_chat_model(
        model, temperature=temperature, thinking_level=thinking_level,
        thinking_budget=thinking_budget, **kwargs,
    )
    if cache_key is None:
        return instance
    with _MODEL_CACHE_LOCK:
        return _MODEL_CACHE.setdefault(cache_key, instance)


def _build_chat_model(
    model: str,
    *,
    temperature: float = 0.0,
    thinking_level: str | None = None,
    thinking_budget: int | None = None,
    **kwargs: Any,
) -> ChatGoogleGenerativeAI | ChatOpenAI:
    """Construct a fresh chat model (uncached). See ``create_chat_model``."""
    if model.startswith("nim/"):
        return _build_openai_compat_chat_model(
            model.removeprefix("nim/"), _NIM_BASE_URL, "NVIDIA_API_KEY",
            temperature=temperature,
        )

    if model.startswith("deepseek/"):
        # Thinking is ALWAYS disabled: V4's thinking mode rejects the forced
        # tool_choice that with_structured_output sends, and every game call is
        # structured — a thinking DeepSeek seat 400s on its first turn (seen live
        # with the summary agent's default "medium" level).
        if thinking_level not in (None, "minimal"):
            logger.info(
                "DeepSeek: thinking_level=%s ignored (thinking mode is incompatible "
                "with structured output on this endpoint).", thinking_level,
            )
        return _build_openai_compat_chat_model(
            model.removeprefix("deepseek/"), _DEEPSEEK_BASE_URL, "DEEPSEEK_API_KEY",
            temperature=temperature,
            extra_body={"thinking": {"type": "disabled"}},
        )

    if model.startswith("mistral/"):
        return MistralChatModel(model.removeprefix("mistral/"), temperature=temperature)

    build_kwargs: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
    }

    if _use_vertex():
        build_kwargs["vertexai"] = True
        build_kwargs["location"] = os.getenv(
            "VERTEX_LOCATION", _DEFAULT_VERTEX_LOCATION
        )
    else:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            build_kwargs["google_api_key"] = api_key

    if thinking_budget is not None:
        build_kwargs["thinking_budget"] = thinking_budget
    elif thinking_level:
        if _use_vertex():
            budget = THINKING_LEVEL_TO_BUDGET.get(thinking_level)
            if budget is not None:
                build_kwargs["thinking_budget"] = budget
        else:
            build_kwargs["thinking_level"] = thinking_level

    build_kwargs.update(kwargs)
    return ChatGoogleGenerativeAI(**build_kwargs)

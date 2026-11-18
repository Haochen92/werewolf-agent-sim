"""Live chat models: the one entry, ``create_chat_model``, for every LangChain call in a game.

The model id picks the provider (``providers/``): a ``nim/``, ``deepseek/``, ``openai/``,
``openrouter/`` or ``xai/`` prefix the OpenAI protocol, ``anthropic/`` Claude, ``mistral/`` Mistral,
and a bare id Gemini (Vertex unless ``LLM_BACKEND=google``). Instances are memoised by construction
args (building one is non-trivial: client and auth setup), so callers in hot loops reuse a shared,
thread-safe instance. A served game's own model and key are held by its ``GameModels``
(game_models.py), which builds the clients on a player's key itself and keeps them with the game.
"""

from __future__ import annotations

import os
import threading
from typing import Any

from . import catalog
from .health import ModelHealth
from .providers import anthropic, google, openai_compat
from .providers.common import STRUCTURED_MODES
from .providers.mistral import MistralChatModel


def provider_family(model: str) -> str:
    """The credential pool a model id draws from: its prefix, or google for bare Gemini ids."""
    return model.split("/", 1)[0] if "/" in model else "google"


_PROVIDER_NAMES = {"anthropic": "Anthropic", "openai": "OpenAI", "deepseek": "DeepSeek",
                   "google": "Google"}


def provider_name(model: str) -> str:
    """The company a model id's key belongs to, as a player knows it (Anthropic, OpenAI…)."""
    if not model:
        return "The model provider"
    family = provider_family(model)
    return _PROVIDER_NAMES.get(family, family)


# Chat-model instances are immutable after construction and safe to reuse across
# threads (the underlying SDK/httpx clients are thread-safe). Memoize by
# construction args — callers in hot loops would otherwise rebuild per call.
_MODEL_CACHE: dict[Any, Any] = {}
_MODEL_CACHE_LOCK = threading.Lock()


def create_chat_model(
    model: str,
    *,
    temperature: float = 0.0,
    thinking_level: str | None = None,
    thinking_budget: int | None = None,
    **kwargs: Any,
) -> Any:
    """Create (or reuse) a chat model using the configured backend.

    Instances are memoized by construction args (see ``_MODEL_CACHE``); repeated calls with the
    same args return the same shared, thread-safe instance. Every client here is on the server's
    own credentials: a client on a player's key is built and kept by that game's ``GameModels``.

    Parameters
    ----------
    model:
        Model identifier: a provider prefix (``nim/``, ``deepseek/``, ``openai/``, ``openrouter/``,
        ``xai/``, ``anthropic/``, ``mistral/``) or a bare Gemini name (e.g. ``"gemini-2.5-flash"``).
    temperature:
        Sampling temperature.
    thinking_level:
        Symbolic thinking level (``"minimal"``, ``"low"``, ``"medium"``,
        ``"high"``).  Ignored for NIM; on DeepSeek anything above ``"minimal"``
        turns thinking on, unless the model's structured mode is forced_tool.
    thinking_budget:
        Explicit thinking token budget.  Takes precedence over
        ``thinking_level`` when both are provided.  Ignored for NIM/DeepSeek models.
    **kwargs:
        Forwarded to ``ChatGoogleGenerativeAI``, except ``structured_mode``: one of
        ``STRUCTURED_MODES``, overriding the catalogue row's mode for an OpenAI-protocol or
        Claude model. An OpenAI-protocol or Claude model takes only the request budget
        (``timeout``, ``max_retries``) from them.
    """
    return cached_chat_model(
        _MODEL_CACHE, model, temperature=temperature, thinking_level=thinking_level,
        thinking_budget=thinking_budget, **kwargs,
    )


def cached_chat_model(cache: dict[Any, Any], model: str, *, game_key: str = "", **args: Any) -> Any:
    """The chat model for these args from ``cache``, built and kept there on first use.
    ``game_key`` is a player's key for this model's provider, or empty for the server's own
    credentials. A cache holds one or the other: the process-wide cache never takes a key
    (``create_chat_model``), and a game's cache belongs to that game (``GameModels``), so a game
    is never handed another game's client and a key does not outlive its game."""
    try:
        cache_key: Any = (
            model, args.get("temperature", 0.0), args.get("thinking_level"),
            args.get("thinking_budget"),
            tuple(sorted((k, v) for k, v in args.items()
                         if k not in ("temperature", "thinking_level", "thinking_budget"))),
        )
        hash(cache_key)
    except TypeError:
        cache_key = None  # unhashable kwargs -> bypass cache
    if cache_key is not None and (cached := cache.get(cache_key)) is not None:
        return cached

    instance = _build_chat_model(model, game_key=game_key, **args)
    if cache_key is None:
        return instance
    with _MODEL_CACHE_LOCK:
        return cache.setdefault(cache_key, instance)


def _request_limits(kwargs: dict[str, Any]) -> dict[str, Any]:
    """The accessors' request budget for an OpenAI or Anthropic client. Their SDKs count
    ``max_retries`` as the tries after the first, where the budget counts every attempt (as
    Gemini's SDK does). Without it they waited 600 s a try, three tries: a stalled DeepSeek seat
    held its game for up to half an hour before the rescue was asked (2026-10-21)."""
    limits: dict[str, Any] = {}
    if "timeout" in kwargs:
        limits["timeout"] = kwargs["timeout"]
    if "max_retries" in kwargs:
        limits["max_retries"] = max(0, kwargs["max_retries"] - 1)
    return limits


def _build_chat_model(
    model: str,
    *,
    temperature: float = 0.0,
    thinking_level: str | None = None,
    thinking_budget: int | None = None,
    game_key: str = "",
    **kwargs: Any,
) -> Any:
    """Construct a fresh chat model (uncached). See ``create_chat_model``. ``game_key`` is the
    caller's key for this model's provider; empty means the server's own credentials."""
    # ``structured_mode`` overrides the model's catalogue mode (the admission run tries each);
    # LLM_STRUCTURED_MODE does the same for a whole process (a bench arm), and Gemini ignores it.
    mode = kwargs.pop("structured_mode", None)
    if mode is not None and provider_family(model) in ("google", "mistral"):
        raise ValueError(f"{model} has no structured_mode: it uses its own structured output")
    if mode is None and provider_family(model) not in ("google", "mistral"):
        mode = os.getenv("LLM_STRUCTURED_MODE") or None
    if mode is not None and mode not in STRUCTURED_MODES:
        raise ValueError(f"structured_mode must be one of {STRUCTURED_MODES}, not {mode!r}")
    mode = mode or (row.structured_mode if (row := catalog.entry(model)) else None) or "forced_tool"

    if model.startswith(openai_compat.PREFIXES):
        return openai_compat.build_chat_model(model, temperature=temperature, thinking_level=thinking_level,
                                              mode=mode, game_key=game_key,
                                              **_request_limits(kwargs))
    if model.startswith("mistral/"):
        return MistralChatModel(model.removeprefix("mistral/"), temperature=temperature)
    if model.startswith("anthropic/"):
        return anthropic.build_chat_model(model.removeprefix("anthropic/"), temperature=temperature,
                                          thinking_level=thinking_level, mode=mode,
                                          game_key=game_key, **_request_limits(kwargs))
    return google.build_chat_model(model, temperature=temperature, thinking_level=thinking_level,
                                   thinking_budget=thinking_budget, game_key=game_key, **kwargs)

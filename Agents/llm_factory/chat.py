"""Live chat models: the one entry, ``create_chat_model``, for every LangChain call in a game.

The model id picks the provider (``providers/``): a ``nim/``, ``deepseek/``, ``openai/``,
``openrouter/`` or ``xai/`` prefix the OpenAI protocol, ``anthropic/`` Claude, ``mistral/`` Mistral,
and a bare id Gemini (Vertex unless ``LLM_BACKEND=google``). Instances are memoised by construction
args (building one is non-trivial: client and auth setup), so callers in hot loops reuse a shared,
thread-safe instance. A served game's own model and key ride ``GAME_LLM``.
"""

from __future__ import annotations

import os
import threading
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from . import catalog
from .health import ModelHealth
from .providers import anthropic, google, openai_compat
from .providers.common import STRUCTURED_MODES
from .providers.mistral import MistralChatModel


@dataclass(frozen=True)
class GameLLM:
    """A served game's model selection and optional player credential.

    An empty key with a non-empty model is a house-funded selection and uses the configured
    server backend. ``rescue_model=None`` disables rescue; the typed technical-pass path
    still keeps the game moving. Empty model/key = the environment decides (CLI/batch/eval).
    """

    api_key: str = ""
    model: str = ""
    rescue_model: str | None = None
    # Mutable, shared by reference across the game's threads: the stall count that sends a
    # turn straight to the rescue model (health.py). Not part of equality or the cache key.
    health: ModelHealth = field(default_factory=ModelHealth, compare=False, repr=False)


# Per-game model selection, optionally BYOK (pattern 2, ephemeral pass-through). The server's
# GameSession sets it inside the game's asyncio task; LangGraph copies the task
# context into its worker threads, so every node's factory call sees its own game's
# selection — no argument threading through the call chain. The default empty GameLLM
# (every non-server entry point) = use the environment. A ContextVar, NOT config: keys
# must never reach RunConfig, which gets fingerprint-stamped into run records. The key is
# applied ONLY to the provider family of the selected game model, so an off-family call
# (e.g. a Gemini extraction model during a DeepSeek game) falls back to env credentials
# instead of sending the player's key to the wrong provider.
GAME_LLM: ContextVar[GameLLM] = ContextVar("GAME_LLM", default=GameLLM())


def _provider_family(model: str) -> str:
    """The credential pool a model id draws from: its prefix, or google for bare Gemini ids."""
    return model.split("/", 1)[0] if "/" in model else "google"


def _game_key_for(family: str) -> str:
    """The BYOK key, iff the game's selected model belongs to this provider family."""
    override = GAME_LLM.get()
    if override.api_key and _provider_family(override.model) == family:
        return override.api_key
    return ""

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

    Instances are memoized by construction args (see ``_MODEL_CACHE``); repeated
    calls with the same args return the same shared, thread-safe instance.

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
        Forwarded to ``ChatGoogleGenerativeAI`` (ignored for NIM/DeepSeek), except
        ``structured_mode``: one of ``STRUCTURED_MODES``, overriding
        the catalogue row's mode for an OpenAI-protocol or Claude model.
    """
    try:
        # The BYOK key in the cache key: a game must never be handed a client built with
        # another game's (or the server's) credentials.
        cache_key: Any = (
            model, temperature, thinking_level, thinking_budget,
            _game_key_for(_provider_family(model)), tuple(sorted(kwargs.items())),
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
) -> Any:
    """Construct a fresh chat model (uncached). See ``create_chat_model``."""
    # ``structured_mode`` overrides the model's catalogue mode (the admission run tries each);
    # LLM_STRUCTURED_MODE does the same for a whole process (a bench arm), and Gemini ignores it.
    mode = kwargs.pop("structured_mode", None)
    if mode is not None and _provider_family(model) in ("google", "mistral"):
        raise ValueError(f"{model} has no structured_mode: it uses its own structured output")
    if mode is None and _provider_family(model) not in ("google", "mistral"):
        mode = os.getenv("LLM_STRUCTURED_MODE") or None
    if mode is not None and mode not in STRUCTURED_MODES:
        raise ValueError(f"structured_mode must be one of {STRUCTURED_MODES}, not {mode!r}")
    mode = mode or (row.structured_mode if (row := catalog.entry(model)) else None) or "forced_tool"

    if model.startswith(openai_compat.PREFIXES):
        return openai_compat.build_chat_model(model, temperature=temperature, thinking_level=thinking_level,
                                              mode=mode, game_key=_game_key_for(_provider_family(model)))
    if model.startswith("mistral/"):
        return MistralChatModel(model.removeprefix("mistral/"), temperature=temperature)
    if model.startswith("anthropic/"):
        return anthropic.build_chat_model(model.removeprefix("anthropic/"), temperature=temperature,
                                          thinking_level=thinking_level, mode=mode,
                                          game_key=_game_key_for("anthropic"))
    return google.build_chat_model(model, temperature=temperature, thinking_level=thinking_level,
                                   thinking_budget=thinking_budget, game_key=_game_key_for("google"), **kwargs)

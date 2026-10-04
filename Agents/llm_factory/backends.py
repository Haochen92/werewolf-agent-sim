"""Chat-model construction across the five supported backends.

vertex (default) / google (API-key) / nim / deepseek / mistral / openai / xai / openrouter — selected by ``LLM_BACKEND``
and the model prefix. Instances are memoised by construction args (building one is
non-trivial: client + auth setup), so callers in hot loops reuse a shared,
thread-safe instance. See the package docstring for backend selection rules.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from .health import ModelHealth

logger = logging.getLogger(__name__)

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


@dataclass
class _OpenAICompatResponse:
    content: str


# How an OpenAI-protocol model is asked for a schema-shaped answer (Gemini always uses its own
# constrained output). Every caller just calls ``with_structured_output(schema)``; the mode
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
# Per-model mode, chosen by the model admission run (eval-model-admission). Unlisted models
# use forced_tool, which is what every OpenAI-protocol row has played on so far.
STRUCTURED_MODE_BY_MODEL: dict[str, str] = {}


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


class _ToolCallStructuredChatOpenAI(ChatOpenAI):
    """ChatOpenAI whose ``with_structured_output`` follows ``structured_mode`` (see above).

    LangChain's default method is ``json_schema`` (the OpenAI ``response_format``),
    which OpenAI-compatible providers don't reliably serve — DeepSeek 400s it
    outright — so the default here is forced tool calling. Callers that pass an
    explicit ``method=`` still win.
    """

    structured_mode: str = "forced_tool"

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
        ``"high"``).  Ignored for NIM; on DeepSeek anything above ``"minimal"``
        turns thinking on, unless the model's structured mode is forced_tool.
    thinking_budget:
        Explicit thinking token budget.  Takes precedence over
        ``thinking_level`` when both are provided.  Ignored for NIM/DeepSeek models.
    **kwargs:
        Forwarded to ``ChatGoogleGenerativeAI`` (ignored for NIM/DeepSeek), except
        ``structured_mode``: one of ``STRUCTURED_MODES``, overriding
        ``STRUCTURED_MODE_BY_MODEL`` for an OpenAI-protocol model.
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
) -> ChatGoogleGenerativeAI | ChatOpenAI:
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
    mode = mode or STRUCTURED_MODE_BY_MODEL.get(model, "forced_tool")

    if model.startswith("nim/"):
        return _build_openai_compat_chat_model(
            model.removeprefix("nim/"), _NIM_BASE_URL, "NVIDIA_API_KEY",
            temperature=temperature, structured_mode=mode,
            api_key_override=_game_key_for("nim"),
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
            temperature=temperature, structured_mode=mode,
            api_key_override=_game_key_for("deepseek"),
            extra_body={"thinking": {"type": "enabled" if thinking else "disabled"}},
        )

    if model.startswith("mistral/"):
        return MistralChatModel(model.removeprefix("mistral/"), temperature=temperature)

    # OpenAI and xAI (Grok) speak the OpenAI protocol; structured output rides tool calling, as
    # for DeepSeek. Wired for offline evaluation (the hallucination bench's arms), not game seats.
    if model.startswith("openai/"):
        # Reasoning models take an effort level; "minimal" means off, as elsewhere (GPT-6 Luna
        # takes none / low / medium / high / xhigh and rejects "minimal").
        effort = ({"reasoning_effort": "none" if thinking_level == "minimal" else thinking_level}
                  if thinking_level else {})
        return _build_openai_compat_chat_model(
            model.removeprefix("openai/"), _OPENAI_BASE_URL, "OPENAI_API_KEY",
            temperature=temperature, structured_mode=mode,
            api_key_override=_game_key_for("openai"), **effort)
    if model.startswith("openrouter/"):
        routed = model.removeprefix("openrouter/")
        provider = next((v for k, v in OPENROUTER_PROVIDER.items() if routed.startswith(k)), None)
        if provider is None:
            raise ValueError(f"{model}: no pinned OpenRouter provider for this model family")
        extra: dict[str, Any] = {"provider": {"order": [provider], "allow_fallbacks": False}}
        if thinking_level:
            # OpenRouter's one reasoning switch across providers; "minimal" means off, as on DeepSeek.
            extra["reasoning"] = ({"enabled": False} if thinking_level == "minimal"
                                  else {"effort": thinking_level})
        return _build_openai_compat_chat_model(
            routed, _OPENROUTER_BASE_URL, "OPENROUTER_API_KEY",
            temperature=temperature, structured_mode=mode, extra_body=extra,
            api_key_override=_game_key_for("openrouter"))
    if model.startswith("xai/"):
        return _build_openai_compat_chat_model(
            model.removeprefix("xai/"), _XAI_BASE_URL, "XAI_API_KEY",
            temperature=temperature, structured_mode=mode,
            api_key_override=_game_key_for("xai"))

    build_kwargs: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
    }

    # A per-game BYOK key forces the google (API-key) backend regardless of LLM_BACKEND:
    # the player's key is a Developer-API key, and billing the run to it is the point.
    game_key = _game_key_for("google")
    use_vertex = not game_key and _use_vertex()
    if use_vertex:
        build_kwargs["vertexai"] = True
        build_kwargs["location"] = os.getenv(
            "VERTEX_LOCATION", _DEFAULT_VERTEX_LOCATION
        )
    else:
        api_key = game_key or os.getenv("GOOGLE_API_KEY")
        if api_key:
            build_kwargs["google_api_key"] = api_key

    if thinking_budget is not None:
        build_kwargs["thinking_budget"] = thinking_budget
    elif thinking_level:
        if use_vertex:
            budget = THINKING_LEVEL_TO_BUDGET.get(thinking_level)
            if budget is not None:
                build_kwargs["thinking_budget"] = budget
        else:
            build_kwargs["thinking_level"] = thinking_level

    build_kwargs.update(kwargs)
    return ChatGoogleGenerativeAI(**build_kwargs)

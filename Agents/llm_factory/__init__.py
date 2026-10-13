"""Centralized factory for LLM chat models, offline structured calls and embeddings.

All LLM instantiation across the project goes through this package, in two layers:

- **Live** (``chat``): ``create_chat_model`` builds the LangChain chat model for a model id, every
  game call's one entry. ``accessors`` names which model does which job (``get_llm`` for a seat,
  ``get_llm_judge``, ``get_llm_extractor``...).
- **Offline** (``structured``): ``structured_call`` and ``batch_structured`` for jobs outside a game,
  provider-neutral; a Claude model goes through the Anthropic SDK (cache marks, Message Batches).

Each provider family has one module under ``providers/``, holding both its LangChain build and its
direct calls where it has them: ``google`` (Gemini on Vertex, the default, or the Developer API with
``LLM_BACKEND=google``; Vertex's explicit prefix cache), ``anthropic`` (``anthropic/`` seats and
``claude-*`` direct calls), ``openai_compat`` (``nim/``, ``deepseek/``, ``openai/``, ``openrouter/``,
``xai/``), ``mistral`` (``mistral/``); ``common`` holds the structured-output modes they share.
``catalog`` and ``pricing`` hold the model catalogue and its prices; ``embeddings`` the embedders.
The live layer's surface is re-exported here, so ``from Agents.llm_factory import X`` keeps resolving.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# The factory is the central reader of provider API keys (MISTRAL_API_KEY,
# NVIDIA_API_KEY, …) from the environment, so it loads .env itself rather than
# relying on each caller (e.g. the labeling engine) to have done so first.
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from .chat import GAME_LLM, GameLLM, create_chat_model  # noqa: E402
from .providers.common import STRUCTURED_MODES  # noqa: E402
from .providers.google import (  # noqa: E402
    THINKING_LEVEL_TO_BUDGET,
    _use_vertex as _use_vertex,  # private but imported externally; re-export
)
from .providers.mistral import MistralChatModel  # noqa: E402
from .accessors import (  # noqa: E402
    DEFAULT_DEDUP_MODEL,
    DEFAULT_DEDUP_THINKING_LEVEL,
    DEFAULT_GAME_MODEL,
    DEFAULT_GAME_THINKING_LEVEL,
    game_thinking_level,
    DEFAULT_PRO_BACKUP_MODEL,
    DEFAULT_PRO_MODEL,
    DEFAULT_SUMMARY_THINKING_LEVEL,
    VALID_THINKING_LEVELS,
    _thinking_level_from_env as _thinking_level_from_env,  # private; re-export
    get_llm,
    get_llm_batch_dedup,
    get_llm_dedup,
    get_llm_extractor,
    get_llm_game_fallback,
    get_llm_judge,
    get_llm_pro,
    get_llm_pro_backup,
    get_llm_summary,
)
from .embeddings import (  # noqa: E402
    DEFAULT_EMBEDDING_DIMS,
    DEFAULT_EMBEDDING_MODEL,
    create_embeddings,
    similarity_threshold,
)

__all__ = [
    # chat and providers
    "GAME_LLM",
    "GameLLM",
    "MistralChatModel",
    "STRUCTURED_MODES",
    "THINKING_LEVEL_TO_BUDGET",
    "create_chat_model",
    # accessors
    "DEFAULT_DEDUP_MODEL",
    "DEFAULT_DEDUP_THINKING_LEVEL",
    "DEFAULT_GAME_MODEL",
    "DEFAULT_GAME_THINKING_LEVEL",
    "game_thinking_level",
    "DEFAULT_PRO_BACKUP_MODEL",
    "DEFAULT_PRO_MODEL",
    "DEFAULT_SUMMARY_THINKING_LEVEL",
    "VALID_THINKING_LEVELS",
    "get_llm",
    "get_llm_batch_dedup",
    "get_llm_dedup",
    "get_llm_extractor",
    "get_llm_game_fallback",
    "get_llm_judge",
    "get_llm_pro",
    "get_llm_pro_backup",
    "get_llm_summary",
    # embeddings
    "DEFAULT_EMBEDDING_DIMS",
    "DEFAULT_EMBEDDING_MODEL",
    "create_embeddings",
    "similarity_threshold",
]

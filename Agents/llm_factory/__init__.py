"""Centralized factory for LLM chat models and embeddings.

All LLM instantiation across the project should go through this package.
Supports five backends:

- **vertex** (default): Uses Vertex AI via Application Default Credentials
  on the ``global`` endpoint.  Active when ``LLM_BACKEND=vertex`` or when
  no ``GOOGLE_API_KEY`` is set.
- **google** (legacy): Uses the Google Generative AI Developer API with an
  API key.  Set by ``LLM_BACKEND=google`` (requires ``GOOGLE_API_KEY``).
- **nim**: Uses NVIDIA NIM via the OpenAI-compatible API.
  Set model prefix ``nim/`` (e.g. ``"nim/deepseek-ai/deepseek-v4-flash"``).
  Requires ``NVIDIA_API_KEY``.
- **deepseek**: Uses the official DeepSeek API (OpenAI-compatible).
  Set model prefix ``deepseek/`` (e.g. ``"deepseek/deepseek-v4-flash"``).
  Requires ``DEEPSEEK_API_KEY``.
- **mistral**: Uses the Mistral API (OpenAI-compatible).
  Set model prefix ``mistral/`` (e.g. ``"mistral/mistral-small-2506"``).
  Requires ``MISTRAL_API_KEY``.

On Vertex AI, ``thinking_level`` is translated to ``thinking_budget`` (token
count) because the 2.x model series does not support the string-based
``thinking_level`` parameter.

Split into three modules — ``backends`` (chat-model construction across the four
backends), ``accessors`` (the ``get_llm*`` family + model-config constants), and
``embeddings`` (the embedding factory + transient retry). Their full surface is
re-exported here, so ``from Agents.llm_factory import X`` keeps resolving.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# The factory is the central reader of provider API keys (MISTRAL_API_KEY,
# NVIDIA_API_KEY, …) from the environment, so it loads .env itself rather than
# relying on each caller (e.g. the labeling engine) to have done so first.
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from .backends import (  # noqa: E402
    GAME_LLM,
    GameLLM,
    MistralChatModel,
    THINKING_LEVEL_TO_BUDGET,
    _use_vertex as _use_vertex,  # private but imported externally; re-export
    create_chat_model,
)
from .accessors import (  # noqa: E402
    DEFAULT_DEDUP_MODEL,
    DEFAULT_DEDUP_THINKING_LEVEL,
    DEFAULT_GAME_MODEL,
    DEFAULT_GAME_THINKING_LEVEL,
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
)

__all__ = [
    # backends
    "GAME_LLM",
    "GameLLM",
    "MistralChatModel",
    "THINKING_LEVEL_TO_BUDGET",
    "create_chat_model",
    # accessors
    "DEFAULT_DEDUP_MODEL",
    "DEFAULT_DEDUP_THINKING_LEVEL",
    "DEFAULT_GAME_MODEL",
    "DEFAULT_GAME_THINKING_LEVEL",
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
]

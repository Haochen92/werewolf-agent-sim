import uuid
from typing import Any

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from Agents.game_config import game_config_dict
from Agents.memory_persistence import normalize_memory_persistence_config
from Agents.schemas.metrics import (  # noqa: F401 — re-exported for backward compat
    DayResolutionMetric,
    GraphContext,
    Metrics,
    NightResolutionMetric,
)


langfuse = get_client()

DEFAULT_MEMORY_CONFIG = {
    "wolf": False,
    "villager": False,
    "healer": False,
    "investigator": False,
}

DEFAULT_RERANKING_CONFIG = {
    "observations": {
        "wolf": False,
        "villager": False,
        "healer": False,
        "investigator": False,
    },
    "strategy_points": {
        "wolf": False,
        "villager": False,
        "healer": False,
        "investigator": False,
    },
}

DEFAULT_FILTERING_CONFIG = {
    "wolf": False,
    "villager": False,
    "healer": False,
    "investigator": False,
}

DEFAULT_RETRIEVAL_TYPES_CONFIG = {
    "observations": True,
    "strategy_points": True,
}


def build_game_config(
    memory_config: dict | None = None,
    session_id: str | None = None,
    game_config: Any = None,
    memory_persistence_config: Any = None,
    reranking_config: dict | None = None,
    filtering_config: dict | None = None,
    retrieval_types_config: dict | None = None,
) -> dict:
    memory_config = memory_config or DEFAULT_MEMORY_CONFIG
    reranking_config = reranking_config or DEFAULT_RERANKING_CONFIG
    filtering_config = filtering_config or DEFAULT_FILTERING_CONFIG
    retrieval_types_config = retrieval_types_config or DEFAULT_RETRIEVAL_TYPES_CONFIG
    normalized_game_config = game_config_dict(game_config)
    normalized_memory_persistence_config = normalize_memory_persistence_config(
        memory_persistence_config
    ).model_dump(mode="json")
    game_id = str(uuid.uuid4())

    handler = CallbackHandler()

    return {
        "callbacks": [handler],
        "recursion_limit": 100,
        "configurable": {
            "game_id": game_id,
            "memory_config": memory_config,
            "reranking_config": reranking_config,
            "filtering_config": filtering_config,
            "retrieval_types_config": retrieval_types_config,
            "game_config": normalized_game_config,
            "memory_persistence_config": normalized_memory_persistence_config,
            "session_id": session_id,
        },
    }


def flush():
    langfuse.flush()

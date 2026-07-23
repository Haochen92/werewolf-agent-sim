"""Configuration package — the supported public import surface.

Four layers, one responsibility each:
  - game.py       : werewolf rules + scheduler knobs (GameConfig)
  - run.py        : complete application settings for one run (RunConfig) + pipeline arm defaults
  - langgraph.py  : conversion to / propagation of RunnableConfig + settings read-back

Callers import from `Agents.config` and need not know which internal module owns each helper.
Observability (the Langfuse handler) is composed at the entry point and injected into
build_runnable_config — this package never imports tracing.
"""
from Agents.config.game import (
    DEFAULT_GAME_CONFIG,
    GameConfig,
    game_config_dict,
    normalize_game_config,
)
from Agents.config.langgraph import (
    DEFAULT_RECURSION_LIMIT,
    build_runnable_config,
    child_runnable_config,
    discussion_recursion_limit,
    game_config_from_runnable,
)
from Agents.config.run import (
    DEFAULT_FILTERING_CONFIG,
    DEFAULT_MEMORY_CONFIG,
    DEFAULT_RERANKING_CONFIG,
    DEFAULT_RETRIEVAL_TYPES_CONFIG,
    DEFAULT_SP_EXPLORATION_SLOT,
    DEFAULT_SP_PROVEN_TIERING,
    RunConfig,
)

__all__ = [
    "GameConfig",
    "DEFAULT_GAME_CONFIG",
    "normalize_game_config",
    "game_config_dict",
    "RunConfig",
    "DEFAULT_MEMORY_CONFIG",
    "DEFAULT_RERANKING_CONFIG",
    "DEFAULT_FILTERING_CONFIG",
    "DEFAULT_RETRIEVAL_TYPES_CONFIG",
    "DEFAULT_SP_PROVEN_TIERING",
    "DEFAULT_SP_EXPLORATION_SLOT",
    "build_runnable_config",
    "child_runnable_config",
    "game_config_from_runnable",
    "discussion_recursion_limit",
    "DEFAULT_RECURSION_LIMIT",
]

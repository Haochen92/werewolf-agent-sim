"""Backward-compat shim. The config layers moved to the `Agents.config` package (game rules ->
config.game; RunnableConfig adaptation -> config.langgraph). This module re-exports the old names so
existing `from Agents.game_config import ...` call sites keep working; migrate them to
`from Agents.config import ...` and drop this shim once no imports remain.
"""
from __future__ import annotations

from Agents.config.game import (
    DEFAULT_GAME_CONFIG,
    GameConfig,
    game_config_dict,
    normalize_game_config,
)
from Agents.config.langgraph import game_config_from_runnable

__all__ = [
    "GameConfig",
    "DEFAULT_GAME_CONFIG",
    "normalize_game_config",
    "game_config_dict",
    "game_config_from_runnable",
]

"""The models a game's turn asks for, as an object a caller passes in."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import accessors


class GameModels:
    """The models one game's turns run on, handed to the turn code as an argument.

    It exists so that a caller, and a test, can supply the models: a test passes its own
    ``GameModels`` (through the graph context or an argument) instead of patching the
    module-level accessors. Each method returns what its accessor returns. It holds no state
    and no key: the player's key, the stall record and the game's client cache stay on
    ``GAME_LLM`` (chat.py), so nothing secret travels in the graph context.
    """

    def seat(self) -> Any:
        return accessors.get_llm()

    def seat_rescue(self) -> Any:
        return accessors.get_llm_game_fallback()

    def summary(self) -> Any:
        return accessors.get_llm_summary()

    def summary_rescue(self) -> Any:
        return accessors.get_llm_summary_fallback()

    def judge(self, default_thinking_level: str = "minimal") -> Any:
        return accessors.get_llm_judge(default_thinking_level)

    def extractor(self) -> Any:
        return accessors.get_llm_extractor()


def game_models(context: Mapping[str, Any] | None) -> GameModels:
    """The models in a graph context, or the accessors' own when the context has none: the
    server session, the batch runner and older tests build contexts without them, and a test
    runtime may have no context at all."""
    return (context or {}).get("models") or GameModels()

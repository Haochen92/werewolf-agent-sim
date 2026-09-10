"""The served-game model policy as code (product policy, not runtime mechanics).

Only models that have carried real games are selectable — a model enters by surviving
live games, not by having a factory branch. The first row is both the house default and
the default for a bare BYOK key. GET /models serves this table; the routes' BYOK gate and
GameSession's model override read it. Kept apart from the runtime so the HTTP layer can
import a dict without dragging the graph machinery along.
"""

from __future__ import annotations

from typing import NamedTuple


class GameModel(NamedTuple):
    """One catalogue row.

    ``rescue_model`` — the backup for a turn whose primary model exhausted its retries.
    It must sit on the SAME credential path as the primary (house stays on the server
    backend, BYOK stays on the player's key); ``None`` = no game-tested sibling exists,
    so the typed technical-pass path absorbs the failure instead.
    ``display_name`` — what the frontend's model menu shows (GET /models).
    ``house_funded`` — may run without a player key, on the server's own backend
    (Vertex in production): the house pays. Everything else requires BYOK.
    """

    rescue_model: str | None
    display_name: str
    house_funded: bool = False


SUPPORTED_GAME_MODELS: dict[str, GameModel] = {
    "gemini-3.1-flash-lite": GameModel("gemini-3.5-flash-lite",
                                       "Gemini 3.1 Flash-Lite (default)", True),
    "gemini-3.5-flash-lite": GameModel(
        "gemini-3.1-flash-lite", "Gemini 3.5 Flash-Lite", True),
    "gemini-3.6-flash": GameModel(
        "gemini-3.5-flash-lite", "Gemini 3.6 Flash", True),
    "gemini-2.5-pro": GameModel("gemini-3.5-flash-lite", "Gemini 2.5 Pro"),
    # DeepSeek official endpoint (CLI games incl. the HITL driver ran on it). No second
    # DeepSeek model is game-tested, so no same-credential rescue exists.
    "deepseek/deepseek-v4-pro": GameModel(None, "DeepSeek V4 Pro"),
}

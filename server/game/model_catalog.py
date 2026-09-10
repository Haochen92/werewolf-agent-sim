"""Which models a served game may be played on, and who pays for each of them.

A model is listed here only once it has carried real games, so this is a record of what
has actually worked rather than of everything the code could call. The first row is the
default, both for games the server pays for and for a player who brings a key without
naming a model. GET /models serves this table, routes/_shared.py checks a requested model
against it, and game/runtime.py reads it to find a backup model. It is deliberately a
plain table with no engine imports, so the HTTP layer can read it without loading the
game machinery.
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

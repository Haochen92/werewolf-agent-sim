"""Which models a served game may be played on, and who pays for each of them.

A model is listed here only once it has carried real games, so this is a record of what
has actually worked rather than of everything the code could call. Which row is the
default is not fixed here: it is a live setting owned by server/house.py, falling back to
the first house-funded row. GET /models serves this table, house.py decides who pays for a
choice from it, and game/game_session.py reads it to find a backup model. It is
deliberately a plain table with no engine imports, so the HTTP layer can read it without
loading the game machinery.
"""

from __future__ import annotations

from typing import NamedTuple


class GameModel(NamedTuple):
    """One row: a model, the model to fall back on, and how it is paid for.

    ``rescue_model`` is what a turn switches to when the chosen model has failed too many
    times in a row. It has to be reachable with the same credentials as the first one, so
    a server-funded game stays on the server's own backend and a player-funded game stays
    on that player's key. ``None`` means no tested alternative exists, and the turn is
    passed instead. ``display_name`` is what the model menu shows. ``house_funded`` means
    the server pays for it; any other model needs the player to bring their own key.
    """

    rescue_model: str | None
    display_name: str
    house_funded: bool = False


SUPPORTED_GAME_MODELS: dict[str, GameModel] = {
    # 3.5 Flash-Lite is the fallback default: the first house-funded row (owner preference
    # 2026-09-10; the live default is a setting, see server/house.py). Note that
    # 3.5 thinks by default and bills those reasoning tokens as output; 3.1 does not.
    "gemini-3.5-flash-lite": GameModel(
        "gemini-3.1-flash-lite", "Gemini 3.5 Flash-Lite", True),
    "gemini-3.1-flash-lite": GameModel(
        "gemini-3.5-flash-lite", "Gemini 3.1 Flash-Lite", True),
    "gemini-3.6-flash": GameModel(
        "gemini-3.5-flash-lite", "Gemini 3.6 Flash", True),
    "gemini-2.5-pro": GameModel("gemini-3.5-flash-lite", "Gemini 2.5 Pro"),
    "deepseek/deepseek-v4-pro": GameModel("deepseek/deepseek-v4-flash", "DeepSeek V4 Pro"),
    "deepseek/deepseek-v4-flash": GameModel("deepseek/deepseek-v4-pro", "DeepSeek V4 Flash"),
    # Probed 2026-09-10 (tests/live): drops required fields on roughly one wolf vote in three;
    # the seat's retry plus this rescue absorb it. The other rows had no failures.
    "deepseek/deepseek-flash": GameModel("deepseek/deepseek-v4-flash", "DeepSeek V4.1 Flash"),
}

"""Which models a served game may be played on, and who pays for each of them.

The menu is the listed rows of the model catalogue, which lives in the database (tables
``models`` and ``model_prices``) so a model can be added, listed, re-priced or retuned without a
deploy: ``scripts/model_catalog.py`` edits it, and the server re-reads it every few seconds
(``server/housekeeping/catalog_refresh.py``). A model is listed only once it has carried real
games, so the menu is a record of what has actually worked rather than of everything the code
could call. Which row is the default is not fixed here: it is a live setting owned by
server/house.py, falling back to the first house-funded row. GET /models serves the menu,
house.py decides who pays for a choice from it, and game/game_session.py reads it to find a
backup model.

Each row (``Agents.schemas.model_catalog.CatalogModel``) carries the model to fall back on and
how it is paid for. ``rescue_model`` is what a turn switches to when the chosen model has failed
too many times in a row. It has to be reachable with the same credentials as the first one, so a
server-funded game stays on the server's own backend and a player-funded game stays on that
player's key. ``None`` means no tested alternative exists, and the turn is passed instead.
``display_name`` is what the model menu shows. ``house_funded`` means the server pays for it; any
other model needs the player to bring their own key.
"""

from __future__ import annotations

from Agents.llm_factory import catalog
from Agents.schemas.model_catalog import CatalogModel


def menu_models() -> tuple[CatalogModel, ...]:
    """The menu, in its order."""
    return catalog.current().menu()


def game_model(model: str) -> CatalogModel | None:
    """The menu row for ``model``; None when it is not on the menu."""
    row = catalog.entry(model)
    return row if row is not None and row.listed else None


# The model a player's backup key runs as the game's rescue, by the key's company: that company's
# steadiest listed row for a turn (owner, 2026-10-21). A backup lets a game whose own company stalls
# or goes down go on through another company, on the player's own key for it.
BACKUP_MODELS = {
    "anthropic": "anthropic/claude-haiku-5-5",
    "openai": "openai/gpt-6-luna",
    "google": "gemini-3.6-flash",
    "deepseek": "deepseek/deepseek-v4-flash",
}


def backup_models() -> dict[str, str]:
    """The backup model of each company whose backup is on the menu right now."""
    return {company: model for company, model in BACKUP_MODELS.items() if game_model(model)}


def backup_model(company: str, model: str) -> str:
    """The rescue model a backup key of ``company`` runs in a game on ``model``. ValueError when
    it is the game model's own company (its key is the game's key already) or has no backup."""
    family = model.split("/", 1)[0] if "/" in model else "google"
    if company == family:
        raise ValueError(f"the backup key must be another company's than the game model's ({company})")
    backup = backup_models().get(company)
    if backup is None:
        raise ValueError(f"no backup model for a {company} key")
    return backup


def house_models() -> list[str]:
    """The house-funded rows of the menu, in its order."""
    return [row.model for row in menu_models() if row.house_funded]

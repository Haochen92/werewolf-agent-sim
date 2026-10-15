"""The model catalogue's shapes: what is known about each model a game can be played on, and what
each costs. The live values are rows in the database (``models``, ``model_prices``), read by
``Agents/llm_factory/catalog.py``; these are the shapes those rows are read into."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Price:
    """USD per million tokens, in force from ``since`` until the model's next entry. ``peak``:
    DeepSeek's peak hours bill at twice these (off-peak) rates."""

    since: date
    input: float
    cached: float
    output: float  # reasoning tokens are billed as output
    peak: bool = False


@dataclass(frozen=True)
class CatalogModel:
    """One model the factory can build, as the catalogue knows it."""

    model: str
    """The factory's model id, prefix included (``anthropic/claude-haiku-5-5``)."""
    display_name: str
    """What the model menu shows."""
    listed: bool = False
    """On the menu (GET /models). A listed model needs a price; an unlisted one can still be
    played offline (benches, captures) with its settings below."""
    menu_order: int = 0
    """Ascending; ties keep the model id's order."""
    house_funded: bool = False
    """The server pays for it; any other model needs the player to bring their own key."""
    rescue_model: str | None = None
    """What a turn switches to after the model has failed too many times in a row; reachable
    with the same credentials. None: no rescue, and a turn that still fails is passed."""
    turn_thinking: str | None = None
    """A game turn's thinking level; None = the factory's default (minimal)."""
    summary_thinking: str | None = None
    """The day summary's thinking level; None = the summary's default (medium)."""
    structured_mode: str | None = None
    """How an OpenAI-protocol or Claude model is asked for a schema (backends.STRUCTURED_MODES);
    None = forced_tool. Gemini ignores it."""
    notes: str = ""
    """Why the row is what it is: its admission and bench results, its caveats."""


@dataclass(frozen=True)
class Catalog:
    """Every known model in menu order, and every price by the name the provider bills under."""

    models: tuple[CatalogModel, ...] = ()
    prices: dict[str, tuple[Price, ...]] = field(default_factory=dict)
    """Oldest entry first."""
    source: str = "seed"
    """Where it was read from: "seed" (the code's starting rows) or "database"."""

    def model(self, model: str) -> CatalogModel | None:
        return next((m for m in self.models if m.model == model), None)

    def menu(self) -> tuple[CatalogModel, ...]:
        return tuple(m for m in self.models if m.listed)

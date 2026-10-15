"""The model catalogue: every model a game can be played on, its settings and its prices, as the
database holds them (tables ``models`` and ``model_prices``).

The catalogue lives in the database so a model can be added, listed, re-priced or retuned without
a deploy (``scripts/model_catalog.py`` edits it). The engine reads it from memory, never from the
database mid-game: the server installs it at startup and re-reads it every few seconds
(``server/housekeeping/catalog_refresh.py``); any other process (a bench, a capture, the CLI)
reads it from the database the first time it is needed. The seed below is the catalogue as it
stood when it moved to the database (2026-10-12): the migration's starting rows, and what a
process without a database uses. Tests pin it with WW_MODEL_CATALOG=seed.

A model the factory has no branch for (a new provider) still needs code once; after that, its
models are rows.
"""

from __future__ import annotations

import logging
import os
import threading
from collections import defaultdict

from Agents.schemas.model_catalog import Catalog, CatalogModel, Price

from .pricing import PRICES

logger = logging.getLogger(__name__)

# The menu as it stood in server/game/model_catalog.py, with the per-model levels and modes that
# stood in accessors.py and backends.py. The notes are those tables' comments.
SEED_MODELS: tuple[CatalogModel, ...] = (
    CatalogModel(
        "gemini-3.5-flash-lite", "Gemini 3.5 Flash-Lite", listed=True, menu_order=1,
        house_funded=True, rescue_model="gemini-3.1-flash-lite", turn_thinking="medium",
        notes="The fallback default, the first house-funded row (owner preference 2026-09-10). "
              "With structured output it reasons 0 tokens at minimal and low; at medium the "
              "hallucination bench's bad samples fell from 31% to 10% (discussion_evidence.md §6.7)."),
    CatalogModel(
        "gemini-3.1-flash-lite", "Gemini 3.1 Flash-Lite", listed=True, menu_order=2,
        house_funded=True, rescue_model="gemini-3.5-flash-lite", turn_thinking="low",
        notes="Reasons at low; bench bad samples 15% (discussion_evidence.md §6.7)."),
    CatalogModel(
        "gemini-3.6-flash", "Gemini 3.6 Flash", listed=True, menu_order=3, house_funded=True,
        rescue_model="gemini-3.5-flash-lite"),
    CatalogModel(
        "gemini-2.5-pro", "Gemini 2.5 Pro", listed=True, menu_order=4,
        rescue_model="gemini-3.5-flash-lite"),
    CatalogModel(
        "deepseek/deepseek-v4-pro", "DeepSeek V4 Pro", listed=True, menu_order=5,
        rescue_model="deepseek/deepseek-v4-flash"),
    CatalogModel(
        "deepseek/deepseek-v4-flash", "DeepSeek V4 Flash", listed=True, menu_order=6,
        rescue_model="deepseek/deepseek-v4-pro"),
    CatalogModel(
        "deepseek/deepseek-flash", "DeepSeek V4.1 Flash", listed=True, menu_order=7,
        rescue_model="deepseek/deepseek-v4-flash",
        notes="Probed 2026-09-10 (tests/live): drops required fields on roughly one wolf vote in "
              "three; the seat's retry plus the rescue absorb it."),
    CatalogModel(
        "openai/gpt-6-luna", "GPT-6 Luna", listed=True, menu_order=8, turn_thinking="low",
        structured_mode="json_schema",
        notes="Admitted 2026-10-04 (eval-model-admission + the hallucination bench). Both refuse a "
              "forced tool call with reasoning on, so json_schema. 2026-10-11 Phase 3 bench "
              "(phase3_luna_haiku): low 7% bad against medium's 4%, a tie case by case, ~390 "
              "reasoning tokens against ~1,260 and 8 s a turn against 16. An OpenAI key; no rescue."),
    CatalogModel(
        "anthropic/claude-haiku-5-5", "Claude Haiku 5.5", listed=True, menu_order=9,
        house_funded=True, turn_thinking="low", structured_mode="json_schema",
        notes="Admitted 2026-10-11 (eval-model-admission; the Phase 3 hallucination bench): effort "
              "low, 10-16% bad samples against 3.5 flash-lite's 34-39%, ~9.5 s a turn. A forced "
              "tool call turns its thinking off; json_schema kept it (51/51 against 45/51). Paid "
              "from the owner's Anthropic credits. No rescue (owner 2026-10-12)."),
    CatalogModel(
        "openrouter/z-ai/glm-5.3-flash", "GLM-5.3 Flash", listed=True, menu_order=10,
        turn_thinking="minimal", summary_thinking="minimal", structured_mode="json_mode",
        notes="Without thinking (its endpoint cannot turn reasoning fully off; effort low), "
              "json_mode: 32% bad samples, a cheap option rather than a recommended one. With "
              "thinking it took 34-55 s a call, against the summary's 90 s budget. An OpenRouter "
              "key, pinned to Z.AI's servers; no rescue."),
    # Not on the menu: the memory pipeline's synthesis model and the bench's golden judge.
    CatalogModel(
        "anthropic/claude-sonnet-5-5", "Claude Sonnet 5.5", menu_order=100,
        structured_mode="json_schema",
        notes="Refuses tool_choice \"tool\" and \"any\" (2026-10-12); with thinking off it needs "
              "\"between_tools\" and takes no temperature (backends._CLAUDE_THINKING_OFF)."),
)

# The factory's model prefixes whose provider bills the bare name. OpenRouter bills the routed
# name without its own prefix ("z-ai/glm-5.3-flash"); a bare Gemini id is billed as it is.
_BILLED_WITHOUT = ("anthropic/", "openai/", "deepseek/", "openrouter/", "xai/", "nim/", "mistral/")

_lock = threading.Lock()
_installed: Catalog | None = None


def seed() -> Catalog:
    """The catalogue as it stood in code; see the module docstring."""
    return Catalog(models=SEED_MODELS, prices={k: tuple(v) for k, v in PRICES.items()}, source="seed")


def billed_name(model: str) -> str:
    """The name a model's usage is recorded and priced under: the factory's id less its prefix."""
    for prefix in _BILLED_WITHOUT:
        if model.startswith(prefix):
            return model.removeprefix(prefix)
    return model


def _sync_dsn(dsn: str) -> str:
    """The server's DSN may name an async driver; psycopg takes the plain form."""
    for driver in ("postgresql+psycopg://", "postgresql+asyncpg://", "postgres://"):
        if dsn.startswith(driver):
            return "postgresql://" + dsn.removeprefix(driver)
    return dsn


def load_from_database(dsn: str) -> Catalog:
    """Read the catalogue from the ``models`` and ``model_prices`` tables. Raises on a database
    error: the caller decides whether a stale catalogue is better than none."""
    import psycopg

    with psycopg.connect(_sync_dsn(dsn), connect_timeout=5) as conn:
        model_rows = conn.execute(
            "SELECT model, display_name, listed, menu_order, house_funded, rescue_model, "
            "turn_thinking, summary_thinking, structured_mode, notes "
            "FROM models ORDER BY menu_order, model").fetchall()
        price_rows = conn.execute(
            "SELECT model, since, input, cached, output, peak FROM model_prices "
            "ORDER BY model, since").fetchall()
    prices: dict[str, list[Price]] = defaultdict(list)
    for model, since, input_, cached, output, peak in price_rows:
        prices[model].append(Price(since, float(input_), float(cached), float(output), bool(peak)))
    return Catalog(models=tuple(CatalogModel(*row) for row in model_rows),
                   prices={k: tuple(v) for k, v in prices.items()}, source="database")


def install(catalog: Catalog) -> None:
    """Make ``catalog`` the one every lookup in this process reads."""
    global _installed
    with _lock:
        _installed = catalog


def installed() -> Catalog | None:
    """The installed catalogue, or None before anything is installed (no lazy load)."""
    return _installed


def current() -> Catalog:
    """The installed catalogue; on first use with none installed, the database's when
    WW_POSTGRES_DSN is set (the seed if it cannot be read, with a warning), else the seed."""
    global _installed
    if _installed is not None:
        return _installed
    with _lock:
        if _installed is None:
            dsn = os.getenv("WW_POSTGRES_DSN", "")
            if os.getenv("WW_MODEL_CATALOG", "").lower() == "seed" or not dsn:
                _installed = seed()
            else:
                try:
                    _installed = load_from_database(dsn)
                except Exception as e:  # noqa: BLE001 - a bench should still run on the seed
                    logger.warning("model catalogue: database unreadable (%s); using the seed", e)
                    _installed = seed()
        return _installed


def entry(model: str) -> CatalogModel | None:
    """The catalogue's row for ``model``, listed or not."""
    return current().model(model)


def prices_for(billed: str) -> tuple[Price, ...]:
    """Every price for a billed model name, oldest first; empty when it has none."""
    return current().prices.get(billed, ())

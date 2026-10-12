"""The model catalogue (Agents/llm_factory/catalog.py): the seed in code agrees with the migration
that wrote it to the database and holds together on its own; every reader goes through the
installed catalogue, so a database edit reaches the menu, the levels, the modes and the prices;
and an unreadable database never leaves a process without one."""

import asyncio
import importlib.util
import logging
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from Agents.llm_factory import accessors, catalog
from Agents.llm_factory.backends import STRUCTURED_MODES, _build_chat_model
from Agents.llm_factory.pricing import PRICES, price_at
from Agents.schemas.model_catalog import Catalog, Price

HAIKU = "anthropic/claude-haiku-5-5"


def _migration():
    path = Path(__file__).resolve().parents[2] / "alembic/versions/0011_model_catalog.py"
    spec = importlib.util.spec_from_file_location("migration_0011", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def installed(monkeypatch):
    """Install a catalogue for one test; the seed is back afterwards."""
    def install(cat: Catalog) -> None:
        monkeypatch.setattr(catalog, "_installed", cat)
    return install


def test_the_migration_writes_exactly_the_seed():
    m = _migration()
    assert [tuple(row) for row in m.MODELS] == [
        (r.model, r.display_name, r.listed, r.menu_order, r.house_funded, r.rescue_model,
         r.turn_thinking, r.summary_thinking, r.structured_mode, r.notes) for r in catalog.SEED_MODELS]
    assert sorted((row[0], row[1], row[2], row[3], row[4], row[5]) for row in m.PRICES) == sorted(
        (name, p.since.isoformat(), p.input, p.cached, p.output, p.peak)
        for name, rows in PRICES.items() for p in rows)
    assert all(row[6] for row in m.PRICES), "every seeded price says where it came from"


def test_the_seed_holds_together():
    cat = catalog.seed()
    names = {m.model for m in cat.models}
    levels = {"minimal", "low", "medium", "high"}
    for m in cat.models:
        assert m.rescue_model is None or m.rescue_model in names, m.model
        assert m.turn_thinking in levels | {None} and m.summary_thinking in levels | {None}, m.model
        assert m.structured_mode in set(STRUCTURED_MODES) | {None}, m.model
    assert [m.model for m in cat.menu()][0] == "gemini-3.5-flash-lite"  # the fallback default
    assert "anthropic/claude-sonnet-5-5" not in {m.model for m in cat.menu()}


def test_billed_names_drop_the_factory_prefix_only():
    assert catalog.billed_name(HAIKU) == "claude-haiku-5-5"
    assert catalog.billed_name("openrouter/z-ai/glm-5.3-flash") == "z-ai/glm-5.3-flash"
    assert catalog.billed_name("gemini-3.5-flash-lite") == "gemini-3.5-flash-lite"


def test_the_test_suite_runs_on_the_seed():
    assert catalog.current().source == "seed"


def test_a_database_edit_reaches_every_reader(installed, monkeypatch):
    from server.game.model_catalog import game_model, house_models, menu_models

    cat = catalog.seed()
    rows = tuple(replace(m, turn_thinking="high", structured_mode="auto_tool", house_funded=False)
                 if m.model == HAIKU else
                 replace(m, listed=False) if m.model == "gemini-3.6-flash" else m
                 for m in cat.models)
    prices = {**cat.prices, "claude-haiku-5-5": (Price(datetime(2026, 1, 1).date(), 9.0, 0.9, 9.0),)}
    installed(Catalog(models=rows, prices=prices, source="database"))
    monkeypatch.delenv("GOOGLE_GENAI_THINKING_LEVEL", raising=False)
    monkeypatch.setenv("CLAUDE_API_KEY", "k")

    assert accessors.game_thinking_level(HAIKU) == "high"
    assert _build_chat_model(HAIKU).structured_mode == "auto_tool"
    assert price_at("claude-haiku-5-5", datetime(2026, 10, 12, tzinfo=timezone.utc))[0].input == 9.0
    assert "gemini-3.6-flash" not in [m.model for m in menu_models()]
    assert game_model("gemini-3.6-flash") is None and game_model(HAIKU) is not None
    assert HAIKU not in house_models()


def test_an_unreadable_database_falls_back_to_the_seed(monkeypatch, caplog):
    def broken(dsn):
        raise OSError("connection refused")

    monkeypatch.setattr(catalog, "_installed", None)
    monkeypatch.setattr(catalog, "load_from_database", broken)
    monkeypatch.setenv("WW_MODEL_CATALOG", "")
    monkeypatch.setenv("WW_POSTGRES_DSN", "postgresql://nowhere/db")
    with caplog.at_level(logging.WARNING):
        assert catalog.current().source == "seed"
    assert "using the seed" in caplog.text


def test_the_servers_refresh_installs_a_change_and_survives_an_outage(monkeypatch, installed):
    from server.housekeeping.catalog_refresh import catalog_dsn, refresh_catalog

    seed = catalog.seed()
    fresh = replace(seed, source="database")
    installed(seed)
    monkeypatch.setattr(catalog, "load_from_database", lambda dsn: fresh)
    assert asyncio.run(refresh_catalog("postgresql://db")) is True
    assert catalog.current() is fresh

    def broken(dsn):
        raise OSError("down")

    monkeypatch.setattr(catalog, "load_from_database", broken)
    assert asyncio.run(refresh_catalog("postgresql://db")) is False
    assert catalog.current() is fresh  # the last good catalogue stays
    assert catalog_dsn("postgresql://db") == ""  # the suite is pinned to the seed


def test_a_game_on_an_unpriced_model_is_reported(caplog):
    from server.game.usage import UsageMeter

    meter = UsageMeter()
    with caplog.at_level(logging.WARNING):
        meter._add("some-new-model", 1.0, {"input_tokens": 10, "output_tokens": 5}, failed=False)
        meter._add("claude-haiku-5-5", 1.0, {"input_tokens": 10, "output_tokens": 5}, failed=False)
    assert "some-new-model has no price" in caplog.text
    assert "claude-haiku-5-5" not in caplog.text

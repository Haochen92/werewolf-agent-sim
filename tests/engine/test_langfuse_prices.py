"""Langfuse's model definitions from the catalogue (Agents/observability/langfuse_prices.py): one per
dated price, every name a token count is recorded under priced at its rate, and a Claude model's cache
writes at 1.25x input."""
from datetime import date

import pytest

from Agents.observability.langfuse_prices import USAGE_TYPES, definitions
from Agents.schemas.model_catalog import Price


def test_one_definition_per_dated_price_with_every_usage_name_priced():
    prices = {"gemini-3.5-flash-lite": (Price(date(2026, 7, 21), 0.30, 0.03, 2.50),
                                        Price(date(2026, 11, 1), 0.40, 0.04, 3.00))}
    first, second = definitions(prices)
    assert (first.model_name, second.model_name) == (
        "gemini-3.5-flash-lite@2026-07-21", "gemini-3.5-flash-lite@2026-11-01")
    rates = dict(first.prices)
    for kind, per_million in (("input", 0.30), ("cached", 0.03), ("output", 2.50)):
        for name in USAGE_TYPES[kind]:
            assert rates[name] == pytest.approx(per_million / 1e6)
    assert "input_cache_creation" not in rates
    assert first.match_pattern == r"(?i)^gemini\-3\.5\-flash\-lite$"


def test_a_claude_cache_write_bills_at_a_quarter_over_input():
    (d,) = definitions({"claude-haiku-5-5": (Price(date(2026, 10, 7), 0.10, 0.01, 0.50),)})
    assert dict(d.prices)["input_cache_creation"] == pytest.approx(0.125 / 1e6)

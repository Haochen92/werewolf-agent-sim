"""A model call is priced at the rates in force on its own date and hour (Agents/llm_factory/pricing.py)."""
from datetime import datetime, timezone

import pytest

from Agents.llm_factory.pricing import cost_usd, is_deepseek_peak, price_at, write_factor


def _at(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_deepseek_peak_hours_are_weekday_mornings_utc():
    assert is_deepseek_peak(_at(2026, 10, 5, 2))       # Monday 02:00
    assert is_deepseek_peak(_at(2026, 10, 5, 9, 59))
    assert not is_deepseek_peak(_at(2026, 10, 5, 4))   # the gap between the two windows
    assert not is_deepseek_peak(_at(2026, 10, 5, 10))
    assert not is_deepseek_peak(_at(2026, 10, 4, 2))   # Sunday: off-peak all day


def test_a_game_is_priced_at_its_own_date():
    july, now = price_at("deepseek-v4-pro", _at(2026, 7, 26, 12)), price_at("deepseek-v4-pro", _at(2026, 10, 4, 12))
    assert (july[0].input, july[1]) == (0.435, 1.0)
    assert (now[0].input, now[1]) == (0.66, 1.0)
    assert price_at("deepseek-v4-pro", _at(2026, 10, 5, 7))[1] == 2.0  # Monday peak
    assert price_at("gemini-3.5-flash-lite", _at(2026, 10, 5, 7))[1] == 1.0  # no peak hours


def test_cached_input_bills_at_the_cached_rate():
    # 1M input of which 400k cached, 100k output, V4 Pro off-peak: 0.6*0.66 + 0.4*0.022 + 0.1*1.98
    assert round(cost_usd("deepseek-v4-pro", _at(2026, 10, 4, 12), input=1_000_000, cached=400_000,
                          output=100_000), 4) == round(0.396 + 0.0088 + 0.198, 4)


def test_an_unknown_model_or_date_has_no_price():
    assert cost_usd("some-new-model", _at(2026, 10, 4), input=1, cached=0, output=1) is None
    assert price_at("deepseek-flash", _at(2026, 9, 1)) is None  # before V4.1 Flash existed
    assert price_at("models/gemini-3.1-flash-lite", _at(2026, 10, 4)) is not None


def test_every_menu_model_has_a_price():
    # A model on the menu without a price would show every one of its games as costing nothing known.
    from Agents.llm_factory.catalog import billed_name, seed
    for row in seed().menu():
        assert price_at(billed_name(row.model), _at(2026, 10, 12, 12)) is not None, row.model


def test_a_batched_call_bills_at_half_the_rates():
    at = datetime(2026, 10, 12, tzinfo=timezone.utc)
    direct = cost_usd("claude-haiku-5-5", at, input=1_000_000, cached=200_000, output=100_000)
    batched = cost_usd("claude-haiku-5-5", at, input=1_000_000, cached=200_000, output=100_000, batch=True)
    assert direct == pytest.approx(0.8 * 0.10 + 0.2 * 0.01 + 0.1 * 0.50)
    assert batched == pytest.approx(direct / 2)


def test_claude_usage_is_priced_per_model_with_batches_at_the_batch_rate(monkeypatch):
    from types import SimpleNamespace

    import Agents.llm_factory.providers.anthropic as cs

    monkeypatch.setattr(cs, "usage_by_model", {})
    usage = SimpleNamespace(input_tokens=600_000, output_tokens=100_000, cache_read_input_tokens=400_000,
                            cache_creation_input_tokens=0)
    cs._count(usage, batched=True, model="claude-haiku-5-5")
    # Anthropic's input_tokens excludes the cache read: 600k uncached + 400k cached, all at half rate.
    assert cs.usage_cost_usd() == pytest.approx((0.6 * 0.10 + 0.4 * 0.01 + 0.1 * 0.50) / 2)


def test_a_cache_write_bills_at_the_model_write_premium():
    # Claude and GPT-6 bill a write at 1.25x input; elsewhere a written token is plain input.
    assert (write_factor("claude-haiku-5-5"), write_factor("gpt-6-luna"), write_factor("deepseek-v4-pro")) == (
        1.25, 1.25, 1.0)
    at = _at(2026, 10, 12, 12)
    assert cost_usd("gpt-6-luna", at, input=1_000_000, cached=200_000, written=500_000, output=0) == pytest.approx(
        0.3 * 0.10 + 0.2 * 0.01 + 0.5 * 0.125)
    # written can never exceed the input left after the cached part
    assert cost_usd("gpt-6-luna", at, input=100, cached=100, written=50, output=0) == pytest.approx(100 * 0.01 / 1e6)

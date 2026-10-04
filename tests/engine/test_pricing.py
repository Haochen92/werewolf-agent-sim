"""A model call is priced at the rates in force on its own date and hour (Agents/llm_factory/pricing.py)."""
from datetime import datetime, timezone

from Agents.llm_factory.pricing import cost_usd, is_deepseek_peak, price_at


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
    from server.game.model_catalog import SUPPORTED_GAME_MODELS
    for model in SUPPORTED_GAME_MODELS:
        name = model.split("/", 1)[1] if model.startswith(("openai/", "openrouter/", "deepseek/")) else model
        assert price_at(name, _at(2026, 10, 4, 12)) is not None, model

"""What a model call cost: a dated price table per model, priced from recorded token counts.

Prices change (DeepSeek's V4 Pro rose 1.5–4.6× on 2026-08-13 and added peak hours), and a game
must be priced at the rates of its own date. So nothing stores a cost: a game records its tokens
by model and UTC hour (``server/game/usage.py``) and the cost is worked out here when it is read.
Fixing a wrong price below corrects every game it applied to.

Sources: the July rows are what was entered in Langfuse on 2026-07-26 (its models/prices tables);
DeepSeek from 2026-08-13 is its official pricing page as read on 2026-10-04; Gemini cached rates
never apply in practice, since implicit caching returns no hits on our Vertex path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone


@dataclass(frozen=True)
class Price:
    """USD per million tokens, in force from ``since`` until the model's next entry. ``peak``:
    DeepSeek's peak hours bill at twice these (off-peak) rates."""

    since: date
    input: float
    cached: float
    output: float  # reasoning tokens are billed as output
    peak: bool = False


# Keyed by the model name the provider is called with (no factory prefix), oldest entry first.
PRICES: dict[str, list[Price]] = {
    "gemini-3.1-flash-lite": [Price(date(2026, 1, 1), 0.25, 0.025, 1.50)],
    "gemini-3.5-flash-lite": [Price(date(2026, 7, 21), 0.30, 0.03, 2.50)],
    "gemini-3.6-flash": [Price(date(2026, 7, 21), 1.50, 0.15, 7.50)],
    # Not in the Langfuse table (it used its built-in price); list rates, cached rate unverified.
    "gemini-2.5-pro": [Price(date(2025, 6, 1), 1.25, 0.3125, 10.00)],
    "deepseek-v4-pro": [
        Price(date(2026, 7, 1), 0.435, 0.003625, 0.87),
        Price(date(2026, 8, 13), 0.66, 0.022, 1.98, peak=True),
    ],
    # The 2026-08-13 row is a third-party listing of V4 Flash's August rates, dated from when
    # DeepSeek added peak hours; the exact day V4 Flash's price changed is not known.
    # From 2026-09-10 the name routes to V4.1 Flash and bills at its rates.
    "deepseek-v4-flash": [
        Price(date(2026, 7, 1), 0.14, 0.0028, 0.28),
        Price(date(2026, 8, 13), 0.22, 0.007, 0.66, peak=True),
        Price(date(2026, 9, 10), 0.15, 0.003, 0.60, peak=True),
    ],
    "deepseek-flash": [Price(date(2026, 9, 10), 0.15, 0.003, 0.60, peak=True)],
}


def is_deepseek_peak(at: datetime) -> bool:
    """DeepSeek's peak hours: 01:00–04:00 and 06:00–10:00 UTC, Monday to Friday. (Chinese public
    holidays are off-peak too; they are not modelled, so a holiday game is priced at peak.)"""
    at = at.astimezone(timezone.utc)
    return at.weekday() < 5 and (1 <= at.hour < 4 or 6 <= at.hour < 10)


def price_at(model: str, at: datetime) -> tuple[Price, float] | None:
    """The price in force for ``model`` at ``at`` and its multiplier (2 at DeepSeek peak), or
    None when the table has no price for that model on that date."""
    entries = [p for p in PRICES.get(model.removeprefix("models/"), []) if p.since <= at.date()]
    if not entries:
        return None
    price = entries[-1]
    return price, 2.0 if price.peak and is_deepseek_peak(at) else 1.0


def cost_usd(model: str, at: datetime, *, input: int, cached: int, output: int) -> float | None:
    """What these tokens cost at ``at``. ``input`` includes the cached part, as providers count
    it; the cached part bills at the cached rate and the rest at the input rate."""
    found = price_at(model, at)
    if found is None:
        return None
    price, factor = found
    cached = min(cached, input)
    return factor * ((input - cached) * price.input + cached * price.cached + output * price.output) / 1e6

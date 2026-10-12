"""Langfuse prices from the model catalogue: the database's dated prices written as Langfuse model
definitions, so a trace's cost uses the same rates as the game's usage meter.

Langfuse prices a generation by matching its model name to a model definition and multiplying each
recorded token type by that definition's price: uncached input, cache reads, Anthropic's cache writes
(1.25x input) and output, each under every name a provider's client records it as (USAGE_TYPES). One
definition per dated catalogue price, by the billed name; Langfuse applies the newest whose start date
is before the call, at ingestion (a change prices new traces, not old ones). A definition cannot be edited, so a changed price is deleted and created again. DeepSeek's peak
hours cannot be expressed and take the off-peak rates; batched calls carry their own cost.

``sync`` is idempotent: it leaves a definition that already matches, removes the custom definitions
for the catalogue's models that no longer do, and creates the missing ones. scripts/model_catalog.py
runs it after every price change (``price``) and on demand (``sync-langfuse``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from Agents.schemas.model_catalog import Price

# Anthropic bills a cache write at 1.25x the input rate (5-minute cache); other providers record none.
CACHE_WRITE_FACTOR = 1.25

# The names Langfuse records token counts under, by the rate they bill at. Its LangChain handler takes
# reasoning and cached tokens out of "output" and "input" into their own types, and the providers' clients
# name them differently (Vertex by modality), so every name must be priced or it counts as free.
USAGE_TYPES = {
    "input": ("input", "input_modality_TEXT", "input_modality_text"),
    "cached": ("input_cache_read", "input_cached_tokens", "prompt_cache_hit_tokens",
               "cached_content_token_count", "cached_modality_TEXT", "cached_modality_text"),
    "output": ("output", "output_reasoning", "output_reasoning_tokens", "output_modality_TEXT",
               "output_modality_text"),
}


@dataclass(frozen=True)
class Definition:
    billed: str
    start: datetime
    prices: tuple[tuple[str, float], ...]  # (usage type, USD per token), sorted

    @property
    def model_name(self) -> str:
        # Langfuse refuses two definitions of one name, so a dated price is named by its date; all of a
        # model's definitions share its match pattern and the start dates pick between them.
        return f"{self.billed}@{self.start.date().isoformat()}"

    @property
    def match_pattern(self) -> str:
        return f"(?i)^{re.escape(self.billed)}$"


def _per_token(usd_per_million: float) -> float:
    return round(usd_per_million / 1e6, 12)


def definitions(prices: dict[str, tuple[Price, ...]]) -> list[Definition]:
    """The definitions the catalogue's prices call for, one per dated price."""
    out = []
    for billed, rows in sorted(prices.items()):
        for p in rows:
            rate = {"input": p.input, "cached": p.cached, "output": p.output}
            types = {name: _per_token(rate[kind]) for kind, names in USAGE_TYPES.items() for name in names}
            if billed.startswith("claude-"):
                # a cache write; recorded by its lifetime when Anthropic reports it (1h bills 2x input)
                types["input_cache_creation"] = _per_token(p.input * CACHE_WRITE_FACTOR)
                types["input_ephemeral_5m_input_tokens"] = _per_token(p.input * CACHE_WRITE_FACTOR)
                types["input_ephemeral_1h_input_tokens"] = _per_token(p.input * 2)
            start = datetime(p.since.year, p.since.month, p.since.day, tzinfo=timezone.utc)
            out.append(Definition(billed, start, tuple(sorted(types.items()))))
    return out


def _existing(api: Any, billed: set[str]) -> list[tuple[str, Definition | None]]:
    """(id, definition) for every custom Langfuse definition of one of the ``billed`` models: one this
    module wrote (``name@date``) or one entered by hand under the plain name."""
    found, page = [], 1
    while True:
        res = api.models.list(page=page, limit=100)
        for m in res.data:
            name = m.model_name.split("@", 1)[0]
            if m.is_langfuse_managed or name not in billed:
                continue
            tiers = getattr(m, "pricing_tiers", None) or []
            default = next((t for t in tiers if t.is_default), None)
            raw = default.prices if default else {k: v.price for k, v in (m.prices or {}).items()}
            start = m.start_date.astimezone(timezone.utc) if m.start_date else datetime.min.replace(tzinfo=timezone.utc)
            d = Definition(name, start, tuple(sorted((k, round(float(v), 12)) for k, v in raw.items())))
            # a hand-entered definition (plain name) is never what sync writes, so it is replaced
            found.append((m.id, d if "@" in m.model_name else None))
        if page >= (res.meta.total_pages or 1):
            break
        page += 1
    return found


def sync(api: Any, prices: dict[str, tuple[Price, ...]]) -> dict[str, int]:
    """Make Langfuse's custom definitions for the catalogue's models equal the catalogue's prices."""
    from langfuse.api.resources.commons.types.pricing_tier_input import PricingTierInput
    from langfuse.api.resources.models.types.create_model_request import CreateModelRequest

    wanted = definitions(prices)
    existing = _existing(api, {d.billed for d in wanted})
    have = {d for _, d in existing if d is not None}
    removed = 0
    for model_id, d in existing:
        if d not in wanted:
            api.models.delete(model_id)
            removed += 1
    created = 0
    for d in wanted:
        if d in have:
            continue
        api.models.create(request=CreateModelRequest(
            model_name=d.model_name, match_pattern=d.match_pattern, start_date=d.start, unit="TOKENS",
            pricing_tiers=[PricingTierInput(name="Standard", is_default=True, priority=0, conditions=[],
                                            prices=dict(d.prices))]))
        created += 1
    return {"definitions": len(wanted), "created": created, "removed": removed,
            "unchanged": len(wanted) - created}

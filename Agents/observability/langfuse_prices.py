"""Copies the model prices from this project's catalogue into Langfuse, so that the cost shown on
a trace uses the same rates as the game's own usage meter.

How Langfuse prices a model call. It keeps a list of model definitions. For each call it finds
the definition whose pattern matches the call's model name, then multiplies each kind of token
the call recorded by that definition's price for it. The kinds are uncached input, cache reads,
cache writes and output. Providers' clients record the same kind under different names
(USAGE_TYPES lists them), and a name with no price counts as free, so every name is given one.
A cache write costs the input price times the model's write factor: 1.25 on Claude and on OpenAI
from GPT-5.6, and 1 elsewhere.

What this module writes. One definition for each dated price in the catalogue, under the name
the provider bills the model by. Where a model has several, Langfuse uses the newest one that
starts before the call. It decides this when the trace arrives, so a price change applies to
new traces and not to old ones. A definition cannot be edited, so a changed price is deleted and
created again.

Two limits. DeepSeek's prices differ at peak hours, which a definition cannot express, so its
off-peak rates are used. Batched calls record their own cost and are not priced from these
definitions.

``sync`` can be run any number of times. It leaves a definition that is already right, removes
the catalogue's models' definitions that no longer match, and creates the missing ones.
``scripts/model_catalog.py`` runs it after every price change (``price``) and on request
(``sync-langfuse``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from Agents.llm_factory.pricing import write_factor
from Agents.schemas.model_catalog import Price

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
            # A cache write, priced for every model: an unpriced type counts as free, and OpenAI's
            # writes (GPT-5.6 on) were once priced at nothing that way (caching log §11).
            types["input_cache_creation"] = _per_token(p.input * write_factor(billed))
            if billed.startswith("claude-"):
                # recorded by its lifetime when Anthropic reports it (1h bills 2x input)
                types["input_ephemeral_5m_input_tokens"] = _per_token(p.input * write_factor(billed))
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

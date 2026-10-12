"""Token and cost estimates for model calls made during evaluation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from Agents.llm_factory.catalog import billed_name
from Agents.llm_factory.pricing import cost_usd
from evaluation.src.core.schemas import CostEstimate


# Prices come from the model catalogue (the database's model_prices, read through
# Agents/llm_factory/pricing.py), at the rate in force on the day of the call.
PRICING_VERSION = "model_catalog"
TOKEN_ESTIMATION_METHOD = "chars_per_token_4"
USAGE_METADATA_METHOD = "langchain_usage_metadata"


def estimate_tokens(text: str) -> int:
    """Estimate text tokens without making a provider call.

    This is intentionally simple and stable for experiment comparisons. It is
    not a billing source of truth; it lets paired runs compare expected cost
    when the same estimation method is applied to both variants.
    """
    if not text:
        return 0
    return max(1, round(len(text) / 4))


def estimate_cost(model: str, input_text: str, output_text: str) -> CostEstimate:
    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)
    return cost_from_token_counts(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=0,
        cache_read_tokens=0,
        total_tokens=input_tokens + output_tokens,
        token_estimation_method=TOKEN_ESTIMATION_METHOD,
    )


def cost_from_token_counts(
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int,
    cache_read_tokens: int,
    total_tokens: int,
    token_estimation_method: str,
    batch: bool = False,
) -> CostEstimate:
    """``input_tokens`` includes the cached part; None when the catalogue has no price for the model."""
    estimated_cost_usd = cost_usd(billed_name(model), datetime.now(timezone.utc), input=input_tokens,
                                  cached=cache_read_tokens, output=output_tokens, batch=batch)

    return CostEstimate(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
        cache_read_tokens=cache_read_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost_usd,
        pricing_version=PRICING_VERSION,
        token_estimation_method=token_estimation_method,
    )


def estimate_cost_from_usage_metadata(
    model: str,
    usage_metadata: Any,
    *,
    fallback_input_text: str = "",
    fallback_output_text: str = "",
) -> CostEstimate:
    """Estimate cost from LangChain usage metadata, including thinking tokens.

    LangChain's Google GenAI integration reports Gemini thinking tokens under
    ``output_token_details.reasoning`` and includes them in ``output_tokens``.
    If usage metadata is unavailable, this falls back to the stable char/4
    estimator used by older eval results.
    """
    if not usage_metadata:
        return estimate_cost(model, fallback_input_text, fallback_output_text)

    input_details = usage_metadata.get("input_token_details", {}) or {}
    output_details = usage_metadata.get("output_token_details", {}) or {}
    input_tokens = int(usage_metadata.get("input_tokens") or 0)
    output_tokens = int(usage_metadata.get("output_tokens") or 0)
    total_tokens = int(usage_metadata.get("total_tokens") or 0)
    reasoning_tokens = int(output_details.get("reasoning") or 0)
    cache_read_tokens = int(input_details.get("cache_read") or 0)

    if total_tokens <= 0:
        total_tokens = input_tokens + output_tokens

    return cost_from_token_counts(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
        cache_read_tokens=cache_read_tokens,
        total_tokens=total_tokens,
        token_estimation_method=USAGE_METADATA_METHOD,
    )

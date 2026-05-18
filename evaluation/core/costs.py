from __future__ import annotations

from typing import Any

from evaluation.core.schemas import CostEstimate


PRICING_VERSION = "google_genai_standard_2026_05_14"
TOKEN_ESTIMATION_METHOD = "chars_per_token_4"
USAGE_METADATA_METHOD = "langchain_usage_metadata"

# Standard paid-tier text rates from the Gemini Developer API pricing page.
# Values are USD per 1M tokens. Output pricing includes thinking tokens.
DEFAULT_PRICING_PER_1M_USD: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-preview": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.5-flash-lite-preview": (0.10, 0.40),
    "gemini-2.5-pro": (1.25, 10.00),
}


def estimate_tokens(text: str) -> int:
    """Estimate text tokens without making a provider call.

    This is intentionally simple and stable for experiment comparisons. It is
    not a billing source of truth; it lets paired runs compare expected cost
    when the same estimation method is applied to both variants.
    """
    if not text:
        return 0
    return max(1, round(len(text) / 4))


def _pricing_for_model(model: str) -> tuple[float, float] | None:
    normalized = model.lower()
    if normalized in DEFAULT_PRICING_PER_1M_USD:
        return DEFAULT_PRICING_PER_1M_USD[normalized]
    for prefix, pricing in DEFAULT_PRICING_PER_1M_USD.items():
        if normalized.startswith(prefix):
            return pricing
    return None


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
) -> CostEstimate:
    pricing = _pricing_for_model(model)
    estimated_cost_usd = None
    if pricing:
        input_price, output_price = pricing
        estimated_cost_usd = (
            (input_tokens / 1_000_000) * input_price
            + (output_tokens / 1_000_000) * output_price
        )

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

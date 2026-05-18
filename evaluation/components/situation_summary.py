from __future__ import annotations

import json
import os
import time
from typing import Any

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from Agents.prompt_inputs import build_agent_prompt_input
from Agents.prompts import (
    HEALER_SITUATION_SUMMARY,
    INVESTIGATOR_SITUATION_SUMMARY,
    VILLAGER_SITUATION_SUMMARY,
    WOLF_SITUATION_SUMMARY,
)
from Agents.schemas.evaluation import EvalCase
from Agents.schemas.output import SituationSummary
from evaluation.core.costs import estimate_cost_from_usage_metadata
from evaluation.core.schemas import CostEstimate, VariantConfig


SITUATION_SUMMARY_PROMPTS: dict[str, ChatPromptTemplate] = {
    "villager": VILLAGER_SITUATION_SUMMARY,
    "healer": HEALER_SITUATION_SUMMARY,
    "investigator": INVESTIGATOR_SITUATION_SUMMARY,
    "wolf": WOLF_SITUATION_SUMMARY,
}


def make_google_llm(config: VariantConfig | Any) -> ChatGoogleGenerativeAI:
    kwargs: dict[str, Any] = {
        "model": config.model,
        "temperature": config.temperature,
    }
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if google_api_key:
        kwargs["api_key"] = google_api_key
    if getattr(config, "thinking_budget", None) is not None:
        kwargs["thinking_budget"] = config.thinking_budget
    if getattr(config, "thinking_level", None) is not None:
        kwargs["thinking_level"] = config.thinking_level
    return ChatGoogleGenerativeAI(**kwargs)


def eval_case_to_agent_payload(case: EvalCase) -> dict[str, Any]:
    """Reconstruct the agent payload shape consumed by the live prompt builder.

    The replay runner must use the same formatting path as the game graph, so
    this function maps frozen EvalCase fields back into the keys expected by
    Agents.agents._build_agent_prompt_input.
    """
    private = case.private_context
    return {
        "player_id": case.player_id,
        "player_role": case.player_role,
        "current_day": case.day,
        "current_round": case.round,
        "day_channel": case.visible_discussion,
        "day_summaries": private.day_summaries,
        "wolf_channel": private.wolf_channel,
        "investigator_results": private.investigator_results,
        "previous_strategy": private.previous_strategy,
        "surviving_players": private.surviving_players,
        "surviving_wolves": private.surviving_wolves,
        "surviving_villagers": private.surviving_villagers,
        "retrieved_observations": case.retrieved_observations,
        "strategy_points": case.retrieved_strategy_points,
    }


def message_content_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(item) for item in content)
    return str(content)


def rendered_prompt_text(
    prompt_template: ChatPromptTemplate,
    prompt_input: dict[str, Any],
    output_schema: type[Any] | None = None,
) -> str:
    messages = prompt_template.format_messages(**prompt_input)
    text = "\n\n".join(message_content_text(message) for message in messages)
    if output_schema is not None:
        text += "\n\nSTRUCTURED OUTPUT SCHEMA:\n"
        text += json.dumps(output_schema.model_json_schema(), sort_keys=True)
    return text


def situation_prompt_for_role(role: str, prompt_id: str) -> ChatPromptTemplate:
    if prompt_id != "current":
        raise ValueError(
            f"Unsupported situation_summary prompt_id={prompt_id!r}. "
            "Only 'current' is implemented."
        )
    return SITUATION_SUMMARY_PROMPTS.get(role, VILLAGER_SITUATION_SUMMARY)


def run_situation_summary_variant(
    case: EvalCase,
    config: VariantConfig,
) -> dict[str, Any]:
    """Run the situation-summary component on one frozen EvalCase."""
    payload = eval_case_to_agent_payload(case)
    prompt_input = build_agent_prompt_input(payload)
    prompt_template = situation_prompt_for_role(case.player_role, config.prompt_id)
    llm = make_google_llm(config)
    chain = prompt_template | llm.with_structured_output(
        SituationSummary,
        include_raw=True,
    )

    started = time.perf_counter()
    result_bundle = chain.invoke(
        prompt_input,
        config={
            "run_name": (
                f"eval_pairwise_situation_summary_{config.label}_"
                f"{case.player_role}_day_{case.day}_round_{case.round}"
            )
        },
    )
    latency_ms = round((time.perf_counter() - started) * 1000)
    if result_bundle.get("parsing_error"):
        raise ValueError(
            f"Structured situation summary parsing failed: "
            f"{result_bundle['parsing_error']}"
        )
    result = result_bundle["parsed"]
    raw_message = result_bundle.get("raw")
    situations = list(result.situations)

    input_text = rendered_prompt_text(
        prompt_template,
        prompt_input,
        output_schema=SituationSummary,
    )
    output_text = json.dumps({"situations": situations}, sort_keys=True)
    cost: CostEstimate = estimate_cost_from_usage_metadata(
        config.model,
        getattr(raw_message, "usage_metadata", None),
        fallback_input_text=input_text,
        fallback_output_text=output_text,
    )

    return {
        "label": config.label,
        "model": config.model,
        "prompt_id": config.prompt_id,
        "temperature": config.temperature,
        "thinking_budget": config.thinking_budget,
        "thinking_level": config.thinking_level,
        "situations": situations,
        "latency_ms": latency_ms,
        "cost": cost.model_dump(mode="json"),
    }

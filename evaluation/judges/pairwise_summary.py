"""LLM judge for pairwise situation-summary comparisons."""

from __future__ import annotations

import json
import time
from typing import Any

from Agents.formatters import format_day_channel
from evaluation.components.situation_summary import make_google_llm
from evaluation.core.costs import estimate_cost_from_usage_metadata
from evaluation.core.config_schema import JudgeConfig
from evaluation.core.formatters import (
    format_eval_private_context,
    format_eval_situations,
)
from evaluation.core.schemas import PairwiseJudgeScores
from evaluation.data.datasets import EvalDatasetRecord
from evaluation.judges.prompts import (
    PAIRWISE_SUMMARY_SYSTEM_PROMPT,
    PAIRWISE_SUMMARY_USER_PROMPT,
)


def judge_input_for_summary(
    record: EvalDatasetRecord,
    output_a: dict[str, Any],
    output_b: dict[str, Any],
) -> dict[str, Any]:
    case = record.eval_case
    return {
        "player_id": case.player_id,
        "player_role": case.player_role,
        "day": case.day,
        "round": case.round,
        "action_type": case.action_type,
        "day_channel_excerpt": format_day_channel(case.visible_discussion),
        "private_context": format_eval_private_context(case.private_context),
        "output_a_label": output_a["label"],
        "output_b_label": output_b["label"],
        "output_a": format_eval_situations(output_a["situations"]),
        "output_b": format_eval_situations(output_b["situations"]),
    }


def run_pairwise_summary_judge(
    record: EvalDatasetRecord,
    output_a: dict[str, Any],
    output_b: dict[str, Any],
    judge_config: JudgeConfig,
) -> tuple[PairwiseJudgeScores, dict[str, Any]]:
    """Compare two situation-summary outputs and return judge score plus cost."""
    prompt_input = judge_input_for_summary(record, output_a, output_b)
    user_prompt = PAIRWISE_SUMMARY_USER_PROMPT.format(**prompt_input)
    llm = make_google_llm(judge_config)
    chain = llm.with_structured_output(PairwiseJudgeScores, include_raw=True)

    started = time.perf_counter()
    result_bundle = chain.invoke(
        [
            {"role": "system", "content": PAIRWISE_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )
    latency_ms = round((time.perf_counter() - started) * 1000)
    if result_bundle.get("parsing_error"):
        raise ValueError(
            f"Structured pairwise judge parsing failed: "
            f"{result_bundle['parsing_error']}"
        )
    result = result_bundle["parsed"]
    raw_message = result_bundle.get("raw")

    input_text = (
        PAIRWISE_SUMMARY_SYSTEM_PROMPT
        + "\n\n"
        + user_prompt
        + "\n\nSTRUCTURED OUTPUT SCHEMA:\n"
        + json.dumps(PairwiseJudgeScores.model_json_schema(), sort_keys=True)
    )
    output_text = json.dumps(result.model_dump(mode="json"), sort_keys=True)
    cost = estimate_cost_from_usage_metadata(
        judge_config.model,
        getattr(raw_message, "usage_metadata", None),
        fallback_input_text=input_text,
        fallback_output_text=output_text,
    )
    return result, {
        "model": judge_config.model,
        "prompt_id": judge_config.prompt_id,
        "latency_ms": latency_ms,
        "cost": cost.model_dump(mode="json"),
    }

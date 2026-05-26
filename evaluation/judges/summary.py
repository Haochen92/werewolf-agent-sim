"""Rubric-based LLM judge for situation summary quality."""

from __future__ import annotations

import json

from Agents.llm_factory import create_chat_model
from pydantic import ValidationError

from Agents.formatters import format_day_channel
from Agents.schemas.evaluation import EvalCase
from evaluation.core.formatters import format_eval_private_context, format_eval_situations
from evaluation.core.io import message_content_text, strip_json_fences
from evaluation.core.schemas import SituationSummaryScores
from evaluation.judges.prompts import (
    SUMMARY_RUBRIC,
    SUMMARY_RUBRIC_SYSTEM_PROMPT,
    SUMMARY_RUBRIC_USER_PROMPT,
)


DEFAULT_SUMMARY_JUDGE_MODEL = "gemini-3.1-pro-preview"


def _build_judge_prompt(case: EvalCase, situations: list[str]) -> str:
    return SUMMARY_RUBRIC_USER_PROMPT.format(
        player_id=case.player_id,
        player_role=case.player_role,
        day=case.day,
        round=case.round,
        action_phase=case.action_phase,
        day_channel_excerpt=format_day_channel(case.visible_discussion),
        private_context=format_eval_private_context(case.private_context),
        situations=format_eval_situations(situations),
        summary_rubric=SUMMARY_RUBRIC,
    )


def run_summary_judge(
    case: EvalCase,
    situations: list[str],
    *,
    model: str = DEFAULT_SUMMARY_JUDGE_MODEL,
    max_retries: int = 1,
) -> SituationSummaryScores | None:
    prompt = _build_judge_prompt(case, situations)
    llm = create_chat_model(model)

    for attempt in range(max_retries + 1):
        try:
            response = llm.invoke(
                [
                    {"role": "system", "content": SUMMARY_RUBRIC_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            text = message_content_text(response.content)
            payload = json.loads(strip_json_fences(text))
            return SituationSummaryScores.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            print(f"  Summary judge returned invalid output: {exc}", flush=True)
            if attempt < max_retries:
                continue
            return None
        except Exception as exc:
            print(f"  Summary judge failed: {exc}", flush=True)
            if attempt < max_retries:
                continue
            return None

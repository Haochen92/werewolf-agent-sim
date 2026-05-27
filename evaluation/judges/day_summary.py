"""Rubric-based LLM judge for day summary quality."""

from __future__ import annotations

import json

from Agents.llm_factory import create_chat_model
from pydantic import ValidationError

from evaluation.core.io import message_content_text, strip_json_fences
from evaluation.core.schemas import DaySummaryScores
from evaluation.judges.prompts import (
    DAY_SUMMARY_JUDGE_SYSTEM_PROMPT,
    DAY_SUMMARY_JUDGE_USER_PROMPT,
    DAY_SUMMARY_RUBRIC,
)

DEFAULT_DAY_SUMMARY_JUDGE_MODEL = "gemini-2.5-pro"


def _format_raw_transcript(messages: list[dict], day: int) -> str:
    lines = []
    for msg in messages:
        player = msg.get("player", "unknown")
        rnd = msg.get("round", "?")
        text = msg.get("message", "")
        lines.append(f"[Round {rnd}] {player}: {text}")
    return "\n\n".join(lines)


def _build_judge_prompt(
    raw_discussion: list[dict],
    summary: str,
    day: int,
) -> str:
    return DAY_SUMMARY_JUDGE_USER_PROMPT.format(
        day=day,
        message_count=len(raw_discussion),
        raw_transcript=_format_raw_transcript(raw_discussion, day),
        summary=summary,
        day_summary_rubric=DAY_SUMMARY_RUBRIC,
    )


def run_day_summary_judge(
    raw_discussion: list[dict],
    summary: str,
    day: int,
    *,
    model: str = DEFAULT_DAY_SUMMARY_JUDGE_MODEL,
    max_retries: int = 1,
) -> DaySummaryScores | None:
    prompt = _build_judge_prompt(raw_discussion, summary, day)
    llm = create_chat_model(model)

    for attempt in range(max_retries + 1):
        try:
            response = llm.invoke(
                [
                    {"role": "system", "content": DAY_SUMMARY_JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            text = message_content_text(response.content)
            payload = json.loads(strip_json_fences(text))
            return DaySummaryScores.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            print(f"  Day summary judge returned invalid output: {exc}", flush=True)
            if attempt < max_retries:
                continue
            return None
        except Exception as exc:
            print(f"  Day summary judge failed: {exc}", flush=True)
            if attempt < max_retries:
                continue
            return None

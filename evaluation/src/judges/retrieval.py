"""LLM judge for retrieved memory relevance and redundancy."""

from __future__ import annotations

import json

from pydantic import ValidationError

from Agents.prompts.standards import SITUATION_STANDARDS
from evaluation.src.core.io import message_content_text, strip_json_fences
from evaluation.src.core.schemas import RetrievalScores
from evaluation.src.judges.config import DEFAULT_JUDGE_MODEL, get_judge_llm
from evaluation.src.judges.prompts import RETRIEVAL_SYSTEM_PROMPT, RETRIEVAL_USER_PROMPT


DEFAULT_RETRIEVAL_JUDGE_MODEL = DEFAULT_JUDGE_MODEL


def minimal_retrieval_scores(item_count: int) -> RetrievalScores:
    return RetrievalScores(
        clusters=[],
        relevance=1,
        unique_lessons=item_count,
        efficiency=5,
        brief_reasoning=(
            "No retrieved item was available to judge."
            if item_count == 0
            else "Only one item was retrieved, so efficiency is maximal."
        ),
    )


def parse_retrieval_scores(text: str) -> RetrievalScores:
    payload = json.loads(strip_json_fences(text))
    return RetrievalScores.model_validate(payload)


def run_retrieval_judge(
    *,
    item_type: str,
    situations: list[str],
    items_formatted: str,
    item_count: int,
    model: str,
    thinking_level: str | None = None,
    max_retries: int = 1,
) -> RetrievalScores | None:
    if item_count < 2:
        return minimal_retrieval_scores(item_count)

    prompt = RETRIEVAL_USER_PROMPT.format(
        item_type=item_type,
        situation_standards=SITUATION_STANDARDS,
        situations="\n".join(f"- {situation}" for situation in situations),
        items=items_formatted,
    )
    llm = get_judge_llm(model, thinking_level=thinking_level)
    for attempt in range(max_retries + 1):
        try:
            response = llm.invoke(
                [
                    {"role": "system", "content": RETRIEVAL_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            return parse_retrieval_scores(message_content_text(response.content))
        except (json.JSONDecodeError, ValidationError) as exc:
            print(f"  Retrieval judge returned invalid output: {exc}", flush=True)
            if attempt < max_retries:
                continue
            return None
        except Exception as exc:
            print(f"  Retrieval judge failed: {exc}", flush=True)
            if attempt < max_retries:
                continue
            return None

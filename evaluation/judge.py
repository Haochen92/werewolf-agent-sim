from __future__ import annotations

import json
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

from evaluation.cases import eval_case_to_judge_inputs
from evaluation.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_USER_PROMPT
from Agents.schemas.evaluation import EvalCase
from evaluation.schemas import JudgeScores


DEFAULT_JUDGE_MODEL = "gemini-2.5-pro"


def get_judge_llm(model: str = DEFAULT_JUDGE_MODEL) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=model, temperature=0.0)


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _message_content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _parse_judge_scores(text: str) -> JudgeScores:
    payload = json.loads(_strip_json_fences(text))
    return JudgeScores.model_validate(payload)


def run_judge(
    case: EvalCase,
    model: str = DEFAULT_JUDGE_MODEL,
) -> JudgeScores | None:
    llm = get_judge_llm(model=model)
    inputs = eval_case_to_judge_inputs(case)
    prompt = JUDGE_USER_PROMPT.format(**inputs)

    try:
        response = llm.invoke(
            [
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
        )
        return _parse_judge_scores(_message_content_text(response.content))
    except (json.JSONDecodeError, ValidationError) as exc:
        print(f"  Judge returned invalid scores: {exc}")
        return None
    except Exception as exc:
        print(f"  Judge call failed: {exc}")
        return None

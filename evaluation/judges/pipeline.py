from __future__ import annotations

import json

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

from Agents.schemas.evaluation import EvalCase
from evaluation.core.io import message_content_text, strip_json_fences
from evaluation.core.schemas import JudgeScores
from evaluation.data.cases import eval_case_to_judge_inputs
from evaluation.judges.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_USER_PROMPT


DEFAULT_JUDGE_MODEL = "gemini-2.5-pro"


def get_judge_llm(model: str = DEFAULT_JUDGE_MODEL) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=model, temperature=0.0)


def _parse_judge_scores(text: str) -> JudgeScores:
    payload = json.loads(strip_json_fences(text))
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
        return _parse_judge_scores(message_content_text(response.content))
    except (json.JSONDecodeError, ValidationError) as exc:
        print(f"  Judge returned invalid scores: {exc}")
        return None
    except Exception as exc:
        print(f"  Judge call failed: {exc}")
        return None

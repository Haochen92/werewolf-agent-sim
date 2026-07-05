"""Judge the full turn-level memory pipeline from summary through action."""

from __future__ import annotations

import json

from pydantic import ValidationError

from Agents.schemas.evaluation import EvalCase
from evaluation.src.core.io import message_content_text, strip_json_fences
from evaluation.src.core.schemas import JudgeScores
from evaluation.src.judges.case_inputs import eval_case_to_judge_inputs
from evaluation.src.judges.config import DEFAULT_JUDGE_MODEL, get_judge_llm
from evaluation.src.judges.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_USER_PROMPT


def _parse_judge_scores(text: str) -> JudgeScores:
    payload = json.loads(strip_json_fences(text))
    return JudgeScores.model_validate(payload)


def run_judge(
    case: EvalCase,
    model: str = DEFAULT_JUDGE_MODEL,
    max_retries: int = 1,
) -> JudgeScores | None:
    llm = get_judge_llm(model=model)
    inputs = eval_case_to_judge_inputs(case)
    prompt = JUDGE_USER_PROMPT.format(**inputs)

    for attempt in range(max_retries + 1):
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
            if attempt < max_retries:
                continue
            return None
        except Exception as exc:
            print(f"  Judge call failed: {exc}")
            if attempt < max_retries:
                continue
            return None

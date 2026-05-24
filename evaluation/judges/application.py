"""LLM judge for the final discussion or vote action."""

from __future__ import annotations

import json

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

from Agents.formatters import format_agent_action, format_day_channel
from Agents.schemas.evaluation import EvalCase
from evaluation.core.io import message_content_text, strip_json_fences
from evaluation.core.schemas import ApplicationScores
from evaluation.data.cases import eval_case_to_judge_inputs
from evaluation.judges.prompts import APPLICATION_SYSTEM_PROMPT, APPLICATION_USER_PROMPT


DEFAULT_APPLICATION_JUDGE_MODEL = "gemini-2.5-pro"


def parse_application_scores(text: str) -> ApplicationScores:
    payload = json.loads(strip_json_fences(text))
    return ApplicationScores.model_validate(payload)


def run_application_judge(
    case: EvalCase,
    *,
    model: str,
    max_retries: int = 1,
) -> ApplicationScores | None:
    inputs = eval_case_to_judge_inputs(case)
    prompt = APPLICATION_USER_PROMPT.format(
        player_role=inputs["player_role"],
        day=inputs["day"],
        round=inputs["round"],
        action_phase=inputs["action_phase"],
        day_channel_excerpt=format_day_channel(case.visible_discussion),
        private_context=inputs["private_context"],
        situations=inputs["situations"],
        observations_formatted=inputs["observations_formatted"],
        strategy_points_formatted=inputs["strategy_points_formatted"],
        agent_decision=format_agent_action(
            case.action_phase,
            message=case.agent_message,
            vote=case.agent_vote,
        ),
        agent_updated_strategy=case.updated_strategy,
        agent_adoption_report=inputs["agent_adoption_report"],
    )
    llm = ChatGoogleGenerativeAI(model=model, temperature=0.0)
    for attempt in range(max_retries + 1):
        try:
            response = llm.invoke(
                [
                    {"role": "system", "content": APPLICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            return parse_application_scores(message_content_text(response.content))
        except (json.JSONDecodeError, ValidationError) as exc:
            print(f"  Application judge returned invalid output: {exc}", flush=True)
            if attempt < max_retries:
                continue
            return None
        except Exception as exc:
            print(f"  Application judge failed: {exc}", flush=True)
            if attempt < max_retries:
                continue
            return None

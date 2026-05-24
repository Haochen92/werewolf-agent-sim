"""Judge the quality of postgame extraction output."""

from __future__ import annotations

import json

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS
from Agents.schemas.evaluation import ExtractionCase
from evaluation.core.io import message_content_text, strip_json_fences
from evaluation.core.schemas import ExtractionScores
from evaluation.judges.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_USER_PROMPT,
)

DEFAULT_JUDGE_MODEL = "gemini-2.5-pro"


def _format_dimensional_fields(item: dict) -> str:
    parts = []
    if item.get("information_landscape"):
        parts.append(f"    Information landscape: {item['information_landscape']}")
    if item.get("game_phase"):
        parts.append(f"    Game phase: {item['game_phase']}")
    if item.get("consensus_texture"):
        parts.append(f"    Consensus texture: {item['consensus_texture']}")
    if item.get("agent_exposure"):
        parts.append(f"    Agent exposure: {item['agent_exposure']}")
    return "\n".join(parts)


def _format_observations(observations: list[dict]) -> str:
    if not observations:
        return "(none)"
    lines = []
    for i, obs in enumerate(observations, 1):
        entry = (
            f"[{i}] perspective={obs.get('perspective', '?')} "
            f"phase={obs.get('action_phase', '?')}\n"
            f"    Situation: {obs.get('situation', '')}\n"
            f"{_format_dimensional_fields(obs)}\n"
            f"    Approach: {obs.get('approach', '')}\n"
            f"    Outcome: {obs.get('outcome', '')}"
        )
        lines.append(entry)
    return "\n\n".join(lines)


def _format_strategy_points(points: list[dict]) -> str:
    if not points:
        return "(none)"
    lines = []
    for i, sp in enumerate(points, 1):
        entry = (
            f"[{i}] perspective={sp.get('perspective', '?')} "
            f"phase={sp.get('action_phase', '?')}\n"
            f"    Situation: {sp.get('situation', '')}\n"
            f"{_format_dimensional_fields(sp)}\n"
            f"    Action: {sp.get('action', '')}"
        )
        lines.append(entry)
    return "\n\n".join(lines)


def _format_roles(roles: dict[str, str]) -> str:
    if not roles:
        return "(none)"
    return ", ".join(f"{pid}: {role}" for pid, role in roles.items())


def run_extraction_judge(
    case: ExtractionCase,
    model: str = DEFAULT_JUDGE_MODEL,
    max_retries: int = 1,
) -> ExtractionScores | None:
    llm = ChatGoogleGenerativeAI(model=model, temperature=0.0)
    prompt = EXTRACTION_USER_PROMPT.format(
        roles=_format_roles(case.roles),
        game_outcome=case.game_outcome,
        formatted_discussions=case.formatted_discussions,
        formatted_strategy_notes=case.formatted_strategy_notes,
        situation_standards=SITUATION_STANDARDS,
        epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        num_observations=len(case.observations),
        observations_formatted=_format_observations(case.observations),
        num_strategy_points=len(case.strategy_points),
        strategy_points_formatted=_format_strategy_points(case.strategy_points),
    )

    for attempt in range(max_retries + 1):
        try:
            response = llm.invoke(
                [
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            payload = json.loads(
                strip_json_fences(message_content_text(response.content))
            )
            return ExtractionScores.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            print(f"  Extraction judge returned invalid scores: {exc}")
            if attempt < max_retries:
                continue
            return None
        except Exception as exc:
            print(f"  Extraction judge call failed: {exc}")
            if attempt < max_retries:
                continue
            return None

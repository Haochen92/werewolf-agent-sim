"""Pairwise extraction judge — compares two extraction outputs for one role."""

from __future__ import annotations

import json

from Agents.llm_factory import create_chat_model
from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS
from Agents.schemas.evaluation import ExtractionCase
from pydantic import ValidationError

from evaluation.core.io import message_content_text, strip_json_fences
from evaluation.core.schemas import PairwiseExtractionScores
from evaluation.judges.extraction import (
    DEFAULT_JUDGE_MODEL,
    _format_observations,
    _format_roles,
    _format_strategy_points,
)
from evaluation.judges.prompts import (
    PAIRWISE_EXTRACTION_SYSTEM_PROMPT,
    PAIRWISE_EXTRACTION_USER_PROMPT,
)


def run_pairwise_extraction_judge(
    case: ExtractionCase,
    items_a: tuple[list[dict], list[dict]],
    items_b: tuple[list[dict], list[dict]],
    label_a: str,
    label_b: str,
    role: str,
    model: str = DEFAULT_JUDGE_MODEL,
    max_retries: int = 1,
) -> PairwiseExtractionScores | None:
    """Compare two extraction outputs for one role.

    *items_a* and *items_b* are ``(observations, strategy_points)`` tuples,
    already filtered to the target *role*.
    """
    obs_a, sp_a = items_a
    obs_b, sp_b = items_b

    prompt = PAIRWISE_EXTRACTION_USER_PROMPT.format(
        roles=_format_roles(case.roles),
        game_outcome=case.game_outcome,
        formatted_discussions=case.formatted_discussions,
        formatted_strategy_notes=case.formatted_strategy_notes,
        situation_standards=SITUATION_STANDARDS,
        epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        role=role,
        label_a=label_a,
        num_observations_a=len(obs_a),
        num_strategy_points_a=len(sp_a),
        observations_a_formatted=_format_observations(obs_a),
        strategy_points_a_formatted=_format_strategy_points(sp_a),
        label_b=label_b,
        num_observations_b=len(obs_b),
        num_strategy_points_b=len(sp_b),
        observations_b_formatted=_format_observations(obs_b),
        strategy_points_b_formatted=_format_strategy_points(sp_b),
    )

    llm = create_chat_model(model)
    for attempt in range(max_retries + 1):
        try:
            response = llm.invoke(
                [
                    {"role": "system", "content": PAIRWISE_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            payload = json.loads(
                strip_json_fences(message_content_text(response.content))
            )
            return PairwiseExtractionScores.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            print(f"  Pairwise judge returned invalid scores: {exc}")
            if attempt < max_retries:
                continue
            return None
        except Exception as exc:
            print(f"  Pairwise judge call failed: {exc}")
            if attempt < max_retries:
                continue
            return None

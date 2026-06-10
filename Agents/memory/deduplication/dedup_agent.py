"""Dedup agent: the structured-output `llm.invoke` calls (with retry/validation) that decide
keep/discard for one observation or strategy point against its similar candidates."""

from __future__ import annotations

import logging

from pydantic import BaseModel

from Agents.llm_factory import get_llm_dedup
from Agents.prompts.dedup import OBSERVATION_DEDUP_PROMPT, STRATEGY_DEDUP_PROMPT
from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS
from Agents.schemas import Observation, StrategyPoint

from .config import DEDUP_MAX_RETRIES
from .formatting import _format_existing_entries, _format_existing_observations
from .schemas import (
    ObservationDedupDecisionOutput,
    ObservationDiscard,
    ObservationKeep,
    StrategyDedupDecisionOutput,
    StrategyDiscard,
    StrategyKeep,
)

logger = logging.getLogger(__name__)


def _dedup_agent(
    point: StrategyPoint,
    similar_items: list,
) -> StrategyDiscard | StrategyKeep | None:
    """Call the LLM to decide how to integrate the new point."""
    prompt = STRATEGY_DEDUP_PROMPT.format(
        situation_standards=SITUATION_STANDARDS,
        epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        new_role=point.perspective,
        new_situation=point.composed_situation,
        new_action=point.action,
        total_similar_count=len(similar_items),
        top_n=len(similar_items),
        existing_entries=_format_existing_entries(similar_items),
    )

    llm = get_llm_dedup()
    last_error = None

    for attempt in range(DEDUP_MAX_RETRIES + 1):
        try:
            messages = [{"role": "user", "content": prompt}]
            if last_error:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your previous response failed validation: {last_error}. "
                            f"Please fix and respond again."
                        ),
                    }
                )

            result = llm.with_structured_output(StrategyDedupDecisionOutput).invoke(
                messages,
                config={"run_name": "dedup_strategy_point"},
            )

            if isinstance(result, StrategyDedupDecisionOutput):
                decision = result.result
            elif isinstance(result, dict):
                decision = StrategyDedupDecisionOutput.model_validate(result).result
            else:
                raise TypeError(f"Unexpected dedup LLM result type: {type(result)!r}")

            candidate_error = _candidate_validation_error(
                decision,
                len(similar_items),
            )
            if candidate_error:
                last_error = candidate_error
                continue
            return decision

        except Exception as e:
            last_error = str(e)
            logger.warning(
                f"Dedup LLM call failed (attempt {attempt + 1}/{DEDUP_MAX_RETRIES + 1}): {e}"
            )

    logger.error("Dedup LLM call failed after all retries")
    return None


def _observation_dedup_agent(
    observation: Observation,
    similar_items: list,
) -> ObservationDiscard | ObservationKeep | None:
    """Call the LLM to decide how to integrate the new observation."""
    prompt = OBSERVATION_DEDUP_PROMPT.format(
        new_role=observation.perspective,
        new_situation=observation.composed_situation,
        new_approach=observation.approach,
        new_outcome=observation.outcome,
        total_similar_count=len(similar_items),
        top_n=len(similar_items),
        existing_entries=_format_existing_observations(similar_items),
    )

    llm = get_llm_dedup()
    last_error = None

    for attempt in range(DEDUP_MAX_RETRIES + 1):
        try:
            messages = [{"role": "user", "content": prompt}]
            if last_error:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your previous response failed validation: {last_error}. "
                            f"Please fix and respond again."
                        ),
                    }
                )

            result = llm.with_structured_output(ObservationDedupDecisionOutput).invoke(
                messages,
                config={"run_name": "dedup_observation"},
            )

            if isinstance(result, ObservationDedupDecisionOutput):
                decision = result.result
            elif isinstance(result, dict):
                decision = ObservationDedupDecisionOutput.model_validate(result).result
            else:
                raise TypeError(
                    f"Unexpected observation dedup LLM result type: {type(result)!r}"
                )

            candidate_error = _candidate_validation_error(
                decision,
                len(similar_items),
            )
            if candidate_error:
                last_error = candidate_error
                continue
            return decision

        except Exception as e:
            last_error = str(e)
            logger.warning(
                "Observation dedup LLM call failed "
                f"(attempt {attempt + 1}/{DEDUP_MAX_RETRIES + 1}): {e}"
            )

    logger.error("Observation dedup LLM call failed after all retries")
    return None


def _candidate_validation_error(decision: BaseModel, candidate_count: int) -> str | None:
    candidate: int | None = None
    for field_name in (
        "duplicate_of_candidate",
    ):
        value = getattr(decision, field_name, None)
        if value is not None:
            candidate = value
            break

    if candidate is None:
        return None
    if 1 <= candidate <= candidate_count:
        return None
    return (
        f"candidate number {candidate} is invalid; choose an integer from 1 "
        f"to {candidate_count}, matching the bracketed candidate numbers."
    )

"""Replay a single dedup decision on a frozen ``DedupCase`` with a chosen model.

Reconstructs the observation/strategy dedup prompt from the frozen candidates and
re-runs it, returning the KEEP/DISCARD/MERGE decision letter + detail. The CLI
wrapper (``cli_runner/regen_replay/regen/dedup_regen``) adds record assembly and
distribution reporting so the output can be judged by ``judges/dedup``.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import BaseModel

from Agents.llm_factory import create_chat_model
from Agents.memory.deduplication import (
    ObservationDedupDecisionOutput,
    StrategyDedupDecisionOutput,
)
from Agents.prompts.dedup import OBSERVATION_DEDUP_PROMPT, STRATEGY_DEDUP_PROMPT
from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS
from Agents.schemas.evaluation import DedupCandidate, DedupCase

logger = logging.getLogger(__name__)


def make_dedup_llm(model: str, temperature: float = 0.0, **kwargs):
    return create_chat_model(model, temperature=temperature, **kwargs)


# ---------------------------------------------------------------------------
# Prompt reconstruction from a frozen DedupCase
# ---------------------------------------------------------------------------


def _format_candidates_for_observations(candidates: list[DedupCandidate]) -> str:
    if not candidates:
        return "(none)"
    lines = []
    for c in candidates:
        lines.append(
            f"[{c.candidate_number}] Candidate: {c.candidate_number}; "
            f"Key: {c.key} "
            f"(similarity={c.similarity:.3f}, "
            f"observed={c.observation_count}x)\n"
            f"    Situation: {c.situation}\n"
            f"    Approach: {c.approach or ''}\n"
            f"    Outcome: {c.outcome or ''}"
        )
    return "\n\n".join(lines)


def _format_candidates_for_strategy(candidates: list[DedupCandidate]) -> str:
    if not candidates:
        return "(none)"
    lines = []
    for c in candidates:
        lines.append(
            f"[{c.candidate_number}] Candidate: {c.candidate_number}; "
            f"Key: {c.key} "
            f"(similarity={c.similarity:.3f}, "
            f"observed={c.observation_count}x)\n"
            f"    Action: {c.action or ''}\n"
            f"    Situation: {c.situation}"
        )
    return "\n\n".join(lines)


def build_observation_prompt(case: DedupCase) -> str:
    entry = case.new_entry
    return OBSERVATION_DEDUP_PROMPT.format(
        new_role=case.perspective,
        new_situation=entry.get("situation", ""),
        new_approach=entry.get("approach", ""),
        new_outcome=entry.get("outcome", ""),
        total_similar_count=len(case.candidates),
        top_n=len(case.candidates),
        existing_entries=_format_candidates_for_observations(case.candidates),
    )


def build_strategy_prompt(case: DedupCase) -> str:
    entry = case.new_entry
    return STRATEGY_DEDUP_PROMPT.format(
        situation_standards=SITUATION_STANDARDS,
        epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        new_role=case.perspective,
        new_situation=entry.get("situation", ""),
        new_action=entry.get("action", ""),
        total_similar_count=len(case.candidates),
        top_n=len(case.candidates),
        existing_entries=_format_candidates_for_strategy(case.candidates),
    )


def _output_schema_for(item_type: str) -> type[BaseModel]:
    if item_type == "observation":
        return ObservationDedupDecisionOutput
    return StrategyDedupDecisionOutput


# ---------------------------------------------------------------------------
# Run one replay
# ---------------------------------------------------------------------------


def replay_dedup_decision(
    llm,
    case: DedupCase,
    max_retries: int = 1,
) -> tuple[str, dict[str, Any] | None] | None:
    """Re-run a dedup decision and return (decision_letter, detail_dict)."""
    if case.item_type == "observation":
        prompt = build_observation_prompt(case)
    else:
        prompt = build_strategy_prompt(case)

    output_schema = _output_schema_for(case.item_type)

    for attempt in range(max_retries + 1):
        try:
            result = llm.with_structured_output(output_schema).invoke(
                [{"role": "user", "content": prompt}],
                config={"run_name": f"dedup_replay_{case.item_type}"},
            )
            if isinstance(result, dict):
                result = output_schema.model_validate(result)

            decision = result.result
            decision_letter = decision.decision[0].upper()
            detail = decision.model_dump(mode="json")
            return decision_letter, detail

        except Exception as exc:
            logger.warning(
                "Dedup replay failed attempt %d: %s", attempt + 1, exc
            )
            if attempt < max_retries:
                time.sleep(2)

    return None

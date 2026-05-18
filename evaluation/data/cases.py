from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from Agents.formatters import (
    format_agent_action,
    format_day_channel,
)
from Agents.schemas.evaluation import EvalCase
from evaluation.archive.legacy_cases import legacy_case_from_span
from evaluation.core.formatters import (
    format_eval_private_context,
    format_eval_retrieved_observations,
    format_eval_retrieved_strategy_points,
    format_eval_situations,
)


def eval_case_from_span(span: dict[str, Any]) -> EvalCase | None:
    output = span.get("output") if isinstance(span.get("output"), dict) else {}
    if isinstance(output.get("eval_case"), dict):
        return _case_from_payload(output["eval_case"], span)
    return legacy_case_from_span(span)


def eval_case_to_judge_inputs(case: EvalCase) -> dict[str, Any]:
    return {
        "player_role": case.player_role,
        "day": case.day,
        "round": case.round,
        "action_type": case.action_type,
        "day_channel_excerpt": format_day_channel(case.visible_discussion),
        "private_context": format_eval_private_context(case.private_context),
        "situations": format_eval_situations(case.situations),
        "observations_formatted": format_eval_retrieved_observations(
            case.retrieved_observations
        ),
        "strategy_points_formatted": format_eval_retrieved_strategy_points(
            case.retrieved_strategy_points
        ),
        "num_observations": len(case.retrieved_observations),
        "num_strategy_points": len(case.retrieved_strategy_points),
        "agent_decision": format_agent_action(
            case.action_type,
            message=case.agent_message,
            vote=case.agent_vote,
        ),
        "agent_updated_strategy": case.updated_strategy,
    }


def _case_from_payload(payload: dict[str, Any], span: dict[str, Any]) -> EvalCase | None:
    enriched = {
        **payload,
        "trace_id": payload.get("trace_id") or span.get("trace_id") or "",
        "observation_id": payload.get("observation_id") or span.get("id") or "",
        "span_name": payload.get("span_name") or span.get("name") or "",
    }
    try:
        return EvalCase.model_validate(enriched)
    except ValidationError as exc:
        print(f"  Skipping invalid eval_case payload: {exc}")
        return None

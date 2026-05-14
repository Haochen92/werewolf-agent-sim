from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from Agents.formatters import (
    format_agent_action,
    format_day_channel,
)
from Agents.schemas.evaluation import EvalCase
from Agents.schemas.game_events import DayChannel, DaySummary
from evaluation.formatters import (
    format_eval_private_context,
    format_eval_retrieved_observations,
    format_eval_retrieved_strategy_points,
    format_eval_situations,
)


ACTION_ALIASES = {
    "discussion": "discussion",
    "discuss": "discussion",
    "day_channel": "discussion",
    "vote": "vote",
    "voting": "vote",
    "day_votes": "vote",
}


def normalize_action_type(action_type: Any) -> str | None:
    if not isinstance(action_type, str):
        return None
    return ACTION_ALIASES.get(action_type.lower().strip())


def eval_case_from_span(span: dict[str, Any]) -> EvalCase | None:
    output = span.get("output") if isinstance(span.get("output"), dict) else {}
    if isinstance(output.get("eval_case"), dict):
        return _case_from_payload(output["eval_case"], span)
    return _legacy_case_from_span(span)


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


def _legacy_case_from_span(span: dict[str, Any]) -> EvalCase | None:
    metadata = span.get("metadata", {}) or {}
    span_input = span.get("input") if isinstance(span.get("input"), dict) else {}
    span_output = span.get("output") if isinstance(span.get("output"), dict) else {}
    action_type = (
        normalize_action_type(span_input.get("action_type"))
        or normalize_action_type(metadata.get("action_type"))
    )
    if action_type not in {"discussion", "vote"}:
        return None

    payload = {
        "trace_id": span.get("trace_id", ""),
        "observation_id": span.get("id", ""),
        "span_name": span.get("name", ""),
        "player_id": span_input.get("player_id") or metadata.get("player_id"),
        "player_role": span_input.get("player_role") or metadata.get("player_role"),
        "day": span_input.get("day") or metadata.get("day"),
        "round": span_input.get("round") or metadata.get("round"),
        "action_type": action_type,
        "visible_discussion": _legacy_visible_discussion(
            span_input.get("visible_discussion", ""),
            day=span_input.get("day") or metadata.get("day") or 0,
            round_num=span_input.get("round") or metadata.get("round") or 0,
        ),
        "private_context": {
            "previous_strategy": span_input.get("previous_strategy", "") or "",
            "day_summaries": _legacy_day_summaries(
                span_input.get("day_summaries", ""),
            ),
            "wolf_channel": [],
            "investigator_results": [],
            "surviving_players": span_input.get("surviving_players", []) or [],
            "surviving_wolves": span_input.get("surviving_wolves", []) or [],
            "surviving_villagers": span_input.get("surviving_villagers", []) or [],
        },
        "memory_enabled": bool(span_output.get("memory_enabled")),
        "retrieval_skipped_reason": span_output.get("retrieval_skipped_reason"),
        "situations": _as_list(span_output.get("situations")),
        "retrieved_observations": span_output.get("retrieved_observations") or [],
        "retrieved_strategy_points": span_output.get("retrieved_strategy_points") or [],
        **_legacy_agent_action(action_type, span_output.get("applied_output")),
        "updated_strategy": span_output.get("updated_strategy", "") or "",
    }
    try:
        return EvalCase.model_validate(payload)
    except ValidationError as exc:
        print(f"  Skipping invalid legacy eval span: {exc}")
        return None


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _legacy_visible_discussion(
    value: Any,
    day: int,
    round_num: int,
) -> list[DayChannel]:
    if not isinstance(value, str) or not value.strip():
        return []
    return [
        DayChannel(
            day=day,
            round=round_num,
            player="legacy_trace",
            message=value,
        )
    ]


def _legacy_day_summaries(value: Any) -> list[DaySummary]:
    if not isinstance(value, str) or not value.strip():
        return []
    return [DaySummary(day=0, summary=value)]


def _legacy_agent_action(action_type: str, applied_output: Any) -> dict[str, Any]:
    if action_type == "vote":
        if isinstance(applied_output, list) and applied_output:
            vote = applied_output[0]
            if isinstance(vote, dict):
                target = vote.get("votee") or vote.get("vote_target") or vote.get("vote")
                if target:
                    return {"agent_vote": {"voter": "legacy_trace", "votee": target}}
        return {}

    if isinstance(applied_output, list) and applied_output:
        message = applied_output[0]
        if isinstance(message, dict):
            content = message.get("message")
            if content:
                return {
                    "agent_message": {
                        "day": message.get("day", 0),
                        "round": message.get("round", 0),
                        "player": message.get("player", "legacy_trace"),
                        "message": content,
                    }
                }
        if isinstance(message, str):
            return {
                "agent_message": {
                    "day": 0,
                    "round": 0,
                    "player": "legacy_trace",
                    "message": message,
                }
            }
    return {}

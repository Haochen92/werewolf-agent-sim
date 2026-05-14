from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from Agents.schemas.evaluation import EvalCase
from Agents.schemas.game_events import DayChannel, DaySummary


ACTION_ALIASES = {
    "discussion": "discussion",
    "discuss": "discussion",
    "day_channel": "discussion",
    "vote": "vote",
    "voting": "vote",
    "day_votes": "vote",
}


def legacy_case_from_span(span: dict[str, Any]) -> EvalCase | None:
    metadata = span.get("metadata", {}) or {}
    span_input = span.get("input") if isinstance(span.get("input"), dict) else {}
    span_output = span.get("output") if isinstance(span.get("output"), dict) else {}
    action_type = (
        _normalize_action_type(span_input.get("action_type"))
        or _normalize_action_type(metadata.get("action_type"))
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


def _normalize_action_type(action_type: Any) -> str | None:
    if not isinstance(action_type, str):
        return None
    return ACTION_ALIASES.get(action_type.lower().strip())


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

from __future__ import annotations

from typing import Any

from Agents.formatters import (
    format_day_channel_for_day,
    format_day_summaries,
    format_investigator_results,
    format_retrieved_observations,
    format_strategy_points,
    format_wolf_channel,
)
from Agents.prompts import SITUATION_ROLE_LENS, SITUATION_STANDARDS


def build_agent_prompt_input(payload: dict[str, Any]) -> dict[str, Any]:
    """Format a graph/eval payload into the keys consumed by agent prompts."""
    role = payload.get("player_role", "")
    retrieved_observations = payload.get("retrieved_observations", [])
    strategy_points = payload.get("strategy_points", [])
    return {
        "player_id": payload.get("player_id", ""),
        "player_role": role,
        "current_day": payload.get("current_day", 1),
        "current_round": payload.get("current_round", 1),
        "surviving_players": ", ".join(payload.get("surviving_players", [])),
        "surviving_wolves": ", ".join(payload.get("surviving_wolves", [])),
        "surviving_villagers": ", ".join(payload.get("surviving_villagers", [])),
        "day_channel": format_day_channel_for_day(
            payload.get("day_channel", []),
            payload.get("current_day", 1),
        ),
        "day_summaries": format_day_summaries(
            payload.get("day_summaries", []),
            before_day=payload.get("current_day", 1),
        ),
        "wolf_channel": format_wolf_channel(payload.get("wolf_channel", [])),
        "investigator_results": format_investigator_results(
            payload.get("investigator_results", [])
        ),
        "previous_strategy": payload.get("previous_strategy", ""),
        "strategy_points": (
            strategy_points
            if isinstance(strategy_points, str)
            else format_strategy_points(strategy_points)
        ),
        "retrieved_observations": (
            retrieved_observations
            if isinstance(retrieved_observations, str)
            else format_retrieved_observations(retrieved_observations)
        ),
        "situation_standards": SITUATION_STANDARDS,
        "role_lens": SITUATION_ROLE_LENS.get(role, ""),
    }

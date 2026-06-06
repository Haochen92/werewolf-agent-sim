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
from Agents.prompts import ADOPTION_INSTRUCTION, SITUATION_ROLE_LENS, SITUATION_STANDARDS
from Agents.prompts.standards import EPISTEMIC_STATUS_RULE


def _firing_brief(firing_reason: Any) -> str:
    """Turn the scheduler's firing_reason into a one-line turn brief for the agent.

    Reactive picks get an explicit 'you were addressed by X, respond' nudge so the agent
    aims its reply at the right player (and labels it a response → the debt discharges).
    Proactive / missing reasons add nothing (the silence rule already governs those).
    """
    if firing_reason is None:
        return ""
    if isinstance(firing_reason, dict):
        tier, owes = firing_reason.get("tier"), firing_reason.get("owes") or []
    else:
        tier, owes = getattr(firing_reason, "tier", None), getattr(firing_reason, "owes", []) or []
    if tier == "reactive" and owes:
        return (
            f"You were directly addressed by {', '.join(owes)}. Respond to them this turn — "
            "answer their question or defend against their accusation. Do not stay silent."
        )
    return ""


def build_agent_prompt_input(payload: dict[str, Any]) -> dict[str, Any]:
    """Format a graph/eval payload into the keys consumed by agent prompts."""
    role = payload.get("player_role", "")
    retrieved_observations = payload.get("retrieved_observations", [])
    strategy_points = payload.get("strategy_points", [])
    current_round = payload.get("current_round", 1)
    max_discussion_rounds = payload.get("max_discussion_rounds_per_day", 4)
    final_discussion_round_notice = (
        "This is the final discussion round before voting. "
        "After this round, you will cast your vote."
        if current_round >= max_discussion_rounds
        else ""
    )
    if payload.get("allow_abstain"):
        abstain_instruction = (
            'You may vote "abstain" if you have no one you can justify eliminating yet — '
            "an abstain plurality means no one is eliminated today. Only abstain when "
            "holding off genuinely beats a guess; a wrong elimination is costly, but so is "
            "letting the killers act another night unchecked."
        )
    else:
        abstain_instruction = (
            "Abstaining is not available today — you must vote for a surviving player."
        )
    return {
        "player_id": payload.get("player_id", ""),
        "player_role": role,
        "current_day": payload.get("current_day", 1),
        "current_round": current_round,
        "max_discussion_rounds_per_day": max_discussion_rounds,
        "final_discussion_round_notice": final_discussion_round_notice,
        "abstain_instruction": abstain_instruction,
        "vigilante_bullets": payload.get("vigilante_bullets", 0),
        "firing_brief": _firing_brief(payload.get("firing_reason")),
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
        "vigilante_results": (
            "\n".join(payload.get("vigilante_results", []))
            or "Nothing learned from your shots yet."
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
        "epistemic_status_rule": EPISTEMIC_STATUS_RULE,
        "role_lens": SITUATION_ROLE_LENS.get(role, ""),
        "adoption_instruction": ADOPTION_INSTRUCTION,
    }

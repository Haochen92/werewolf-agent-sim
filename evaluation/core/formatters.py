"""Formatting helpers shared by judge prompts and result records."""

from __future__ import annotations

from typing import Any

from Agents.formatters import (
    format_day_summaries,
    format_investigator_results,
    format_wolf_channel,
)
from Agents.schemas.evaluation import EvalPrivateContext


def format_eval_private_context(context: EvalPrivateContext) -> str:
    fields: list[tuple[str, Any]] = [
        ("Previous strategy", context.previous_strategy),
        ("Day summaries", format_day_summaries(context.day_summaries)),
        ("Wolf channel", format_wolf_channel(context.wolf_channel)),
        ("Investigator results", format_investigator_results(context.investigator_results)),
        ("Surviving players", context.surviving_players),
        ("Surviving wolves", context.surviving_wolves),
        ("Surviving villagers", context.surviving_villagers),
    ]
    lines: list[str] = []
    for label, value in fields:
        if value in (None, "", []):
            continue
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        lines.append(f"- {label}: {value}")
    return "\n".join(lines) if lines else "(not captured)"


def format_eval_situations(situations: list[str]) -> str:
    if not situations:
        return "(none captured)"
    return "\n".join(f"- {situation}" for situation in situations)


def format_eval_retrieved_observations(items: list[Any]) -> str:
    if not items:
        return "(none retrieved)"
    lines = []
    for index, item in enumerate(items, 1):
        score = f"{item.score:.3f}" if item.score is not None else "N/A"
        obs = item.observation
        parts = [f"Situation: {obs.situation}"]
        if obs.approach:
            parts.append(f"Approach: {obs.approach}")
        if obs.outcome:
            parts.append(f"Outcome: {obs.outcome}")
        lines.append(f"[{index}] (score: {score})\n" + " | ".join(parts))
    return "\n\n".join(lines)


def format_eval_retrieved_strategy_points(items: list[Any]) -> str:
    if not items:
        return "(none retrieved)"
    lines = []
    for index, item in enumerate(items, 1):
        score = f"{item.score:.3f}" if item.score is not None else "N/A"
        sp = item.strategy_point
        lines.append(
            f"[{index}] (score: {score})\n"
            f"Situation: {sp.situation}\n"
            f"Action: {sp.action}"
        )
    return "\n\n".join(lines)

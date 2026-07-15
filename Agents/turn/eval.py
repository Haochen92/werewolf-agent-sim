"""Eval-case read snapshot.

Captures the private context an agent acted on, for the EvalCase the
orchestrator assembles. Pure read (the adoption store write-back lives in
``adoption.py``).
"""

from typing import Any

from Agents.schemas import (
    EvalPrivateContext,
)


def _build_eval_private_context(
    payload: dict[str, Any],
    day: int,
) -> EvalPrivateContext:
    """Snapshot the private context an agent acted on, for the eval case.

    Reads everything via ``.get`` so it works for both day payloads (which carry
    faction-split survivor lists) and night payloads (flat ``surviving_players``,
    plus ``vigilante_results`` for the vigilante).
    """
    return EvalPrivateContext(
        previous_strategy=payload.get("previous_strategy", "") or "",
        day_summaries=[
            summary
            for summary in payload.get("day_summaries", [])
            if summary.day < day
        ],
        wolf_channel=payload.get("wolf_channel", []),
        investigator_results=payload.get("investigator_results", []),
        vigilante_results=payload.get("vigilante_results", []),
        surviving_players=payload.get("surviving_players", []),
        surviving_wolves=payload.get("surviving_wolves", []),
        surviving_villagers=payload.get("surviving_villagers", []),
        dead_roster=payload.get("dead_roster", []),
        cast_role_counts=payload.get("cast_role_counts", {}),
    )

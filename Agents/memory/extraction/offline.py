"""Offline extraction: what the batch job makes of a finished game's saved extraction input.

Extraction never runs in a live game (owner's ruling 2026-10-12, evidence/memory_system/v8/
decisions.md §11): a game saves its input when it ends (the post-game node) and the offline job
extracts in batches. This module holds what the job hands on: the replay's "what this game taught"
payload, the same shape the post-game node once streamed.
"""

from __future__ import annotations

from typing import Any

from Agents.schemas.memory import BaseSituation


def extracted_dimensions(item: Any) -> dict | None:
    """The structured fields of one extracted v6 cell record, dumped the way the store write keeps
    them (store_ops: ``dimensions=model_dump``). None for a legacy Observation / StrategyPoint,
    which has no structured situation."""
    return item.model_dump(mode="json") if isinstance(item, BaseSituation) else None


def memory_extracted_payload(output: Any, *, day: int) -> dict[str, Any]:
    """What a finished game taught, for its replay's X-ray: the raw extraction, before any dedup
    against the store (a served game never writes the store, so there is no post-dedup form)."""
    observations = [
        {"perspective": o.perspective, "action_phase": o.action_phase, "situation": o.situation,
         "approach": getattr(o, "approach", ""), "outcome": getattr(o, "outcome", ""),
         "net_verdict": getattr(o, "net_verdict", ""), "dimensions": extracted_dimensions(o)}
        for o in output.observations
    ]
    strategy_points = [
        {"perspective": s.perspective, "action_phase": s.action_phase, "situation": s.situation,
         "action": s.action, "dimensions": extracted_dimensions(s)}
        for s in output.strategy_points
    ]
    return {"event": "memory_extracted", "day": day,
            "observations": observations, "strategy_points": strategy_points}

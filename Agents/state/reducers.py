"""Reducer helpers for graph state channels."""

from Agents.schemas.night import NightChoice


def merge_strategies(existing: dict[str, str], new: dict[str, str]) -> dict[str, str]:
    """Per-key last-writer-wins merge for the agent_strategies channel.

    Concurrent actor nodes each emit a single-key update; merging by key (rather than the default
    overwrite) lets fan-out updates compose without clobbering other agents' notes.
    """
    return dict(existing, **new)


def merge_night_choices(existing: list[NightChoice] | None, new: list[NightChoice] | None) -> list[NightChoice]:
    """The night's choices accumulate across the parallel night branches; ``None`` clears them
    for the next night (one_more_day). Every branch's choice is kept, in arrival order."""
    if new is None:
        return []
    return [*(existing or []), *new]

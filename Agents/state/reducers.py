"""Reducer helpers for graph state channels."""


def merge_strategies(existing: dict[str, str], new: dict[str, str]) -> dict[str, str]:
    """Per-key last-writer-wins merge for the agent_strategies channel.

    Concurrent actor nodes each emit a single-key update; merging by key (rather than the default
    overwrite) lets fan-out updates compose without clobbering other agents' notes.
    """
    return dict(existing, **new)

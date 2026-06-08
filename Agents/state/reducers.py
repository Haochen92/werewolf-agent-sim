"""Reducer helpers for graph state channels."""


def merge_strategies(existing: dict[str, str], new: dict[str, str]) -> dict[str, str]:
    return dict(existing, **new)

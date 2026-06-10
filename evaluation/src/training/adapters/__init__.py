"""Training adapters + a name→class registry.

The registry lets an execution backend (e.g. a Modal container) reconstruct an
adapter from the ``name`` shipped with the job.
"""
from __future__ import annotations

from ..base import TrainingAdapter
from .dedup import DedupAdapter
from .reranker import RerankerAdapter

REGISTRY: dict[str, type[TrainingAdapter]] = {
    RerankerAdapter.name: RerankerAdapter,
    DedupAdapter.name: DedupAdapter,
}


def get_adapter(name: str, **kwargs) -> TrainingAdapter:
    if name not in REGISTRY:
        raise KeyError(f"unknown adapter {name!r}; known: {sorted(REGISTRY)}")
    return REGISTRY[name](**kwargs)


__all__ = ["RerankerAdapter", "DedupAdapter", "REGISTRY", "get_adapter"]

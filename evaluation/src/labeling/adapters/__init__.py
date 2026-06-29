"""Domain-specific adapters for the labeling pipeline.

``get_adapter(name, **kwargs)`` constructs an adapter by registry key so a config
or CLI can select the domain without importing the class directly. Lazy-imported
so selecting one adapter doesn't pull the others' dependencies.
"""
from __future__ import annotations

import importlib

from evaluation.src.labeling.base import LabelingAdapter

# name → (module, class). `dedup` builds zero-arg; `reranker`/`context_relevance`
# take constructor kwargs (pass via adapter_kwargs).
_REGISTRY: dict[str, tuple[str, str]] = {
    "dedup": ("evaluation.src.labeling.adapters.dedup", "DedupAdapter"),
    "reranker": ("evaluation.src.labeling.adapters.reranker", "RerankerAdapter"),
    "context_relevance": (
        "evaluation.src.labeling.adapters.context_relevance",
        "ContextRerankerAdapter",
    ),
}


def get_adapter(name: str, **kwargs) -> LabelingAdapter:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown adapter {name!r}; known: {sorted(_REGISTRY)}")
    module, cls = _REGISTRY[name]
    return getattr(importlib.import_module(module), cls)(**kwargs)


def available_adapters() -> list[str]:
    return sorted(_REGISTRY)

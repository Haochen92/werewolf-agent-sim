"""Retrieval result filters — narrow/diversify a candidate list before it reaches the agent.

MMR diversification, per-situation capping, and a near-duplicate gate. Built on the shared vector
primitives in Agents.memory.vectors. Used by the read-path pipeline and the retrieval eval.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, TypeVar

from numpy.typing import NDArray
import numpy as np

from Agents.memory.vectors import cosine_similarity

T = TypeVar("T")


def mmr_filter(
    items: list[T],
    embeddings: list[NDArray[np.float64]],
    relevance_scores: list[float],
    lambda_: float = 0.8,
    top_k: int = 5,
) -> list[T]:
    if len(items) <= 1:
        return list(items)

    max_score = max(relevance_scores)
    min_score = min(relevance_scores)
    score_range = max_score - min_score
    if score_range == 0:
        normalized = [1.0] * len(relevance_scores)
    else:
        normalized = [(s - min_score) / score_range for s in relevance_scores]

    best_idx = max(range(len(items)), key=lambda i: normalized[i])
    selected_indices: list[int] = [best_idx]
    remaining = set(range(len(items))) - {best_idx}

    while len(selected_indices) < top_k and remaining:
        best_mmr = float("-inf")
        best_remaining = -1

        for i in remaining:
            rel = normalized[i]
            max_sim = max(
                cosine_similarity(embeddings[i], embeddings[j])
                for j in selected_indices
            )
            mmr = lambda_ * rel - (1 - lambda_) * max_sim
            if mmr > best_mmr:
                best_mmr = mmr
                best_remaining = i

        selected_indices.append(best_remaining)
        remaining.discard(best_remaining)

    return [items[i] for i in selected_indices]


def cap_per_situation(
    items: list[T],
    get_situation: Callable[[T], str],
    get_score: Callable[[T], float],
    keep: int = 3,
) -> list[T]:
    groups: dict[str, list[T]] = defaultdict(list)
    for item in items:
        groups[get_situation(item)].append(item)
    result: list[T] = []
    for sit_items in groups.values():
        sit_items.sort(key=get_score, reverse=True)
        result.extend(sit_items[:keep])
    result.sort(key=get_score, reverse=True)
    return result


def dedup_gate(
    items: list[T],
    embeddings: list[NDArray[np.float64]],
    similarity_threshold: float = 0.92,
) -> list[T]:
    if len(items) <= 1:
        return list(items)

    selected_indices: list[int] = [0]

    for i in range(1, len(items)):
        too_similar = any(
            cosine_similarity(embeddings[i], embeddings[j]) > similarity_threshold
            for j in selected_indices
        )
        if not too_similar:
            selected_indices.append(i)

    return [items[i] for i in selected_indices]

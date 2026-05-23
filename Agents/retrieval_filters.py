from __future__ import annotations

import time
from collections import defaultdict
from logging import getLogger
from typing import Callable, TypeVar

import numpy as np
from numpy.typing import NDArray

from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = getLogger(__name__)

T = TypeVar("T")

RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5


def embed_texts(
    texts: list[str],
    embedding_model: GoogleGenerativeAIEmbeddings,
) -> list[NDArray[np.float64]]:
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            raw = embedding_model.embed_documents(texts)
            return [np.asarray(v, dtype=np.float64) for v in raw]
        except Exception as exc:
            if attempt == RETRY_ATTEMPTS:
                raise
            logger.warning(
                "embed_texts failed (attempt %d/%d): %s — retrying in %ds",
                attempt, RETRY_ATTEMPTS, exc, RETRY_DELAY_SECONDS,
            )
            time.sleep(RETRY_DELAY_SECONDS)
    return []


def _cosine_similarity(a: NDArray[np.float64], b: NDArray[np.float64]) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


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
                _cosine_similarity(embeddings[i], embeddings[j])
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
            _cosine_similarity(embeddings[i], embeddings[j]) > similarity_threshold
            for j in selected_indices
        )
        if not too_similar:
            selected_indices.append(i)

    return [items[i] for i in selected_indices]

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

# PROVEN-SP TIER (§0.4): follows an SP must earn before its raw tally is trustworthy — matches
# consolidation's synth_track_min_follow (the shared noise floor for a followed-lesson verdict).
SP_PROVEN_MIN_FOLLOW = 5


def _sp_is_proven(rsp) -> bool:
    """Game-side PROVEN predicate (counter heuristic): cleared the follow floor AND its outcome tally
    leans positive. Deliberately DIFFERS from the loop's lift-based `_is_proven` — the read path has no
    base_rates at retrieval time; post-§0.5 the counts are same-window verdicts (positive/negative are
    already de-lucked), so raw positive>negative at >=5 follows is a sound proven signal without the base.
    Single definition shared by the proven-first tiering and the exploration-slot cap so they can't drift."""
    sp = rsp.strategy_point
    return sp.follow_count >= SP_PROVEN_MIN_FOLLOW and sp.positive_count > sp.negative_count


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
    is_proven: Callable[[T], bool] | None = None,
) -> list[T]:
    groups: dict[str, list[T]] = defaultdict(list)
    for item in items:
        groups[get_situation(item)].append(item)
    result: list[T] = []
    for sit_items in groups.values():
        sit_items.sort(key=get_score, reverse=True)
        kept = sit_items[:keep]
        if is_proven is not None:
            kept = _ensure_exploration_slot(kept, sit_items, keep, is_proven, get_score)
        result.extend(kept)
    result.sort(key=get_score, reverse=True)
    return result


def _ensure_exploration_slot(
    kept: list[T],
    pool: list[T],
    keep: int,
    is_proven: Callable[[T], bool],
    get_score: Callable[[T], float],
) -> list[T]:
    """Guarantee the CONTESTED lane a retrieval slot. SP credit is usage-gated — a candidate never
    retrieved never earns — so if every kept SP is proven, surface the best unproven candidate the pool
    offers (swap the lowest-scoring proven slot for it, or fill a free slot), never exceeding `keep`. This
    is what drains the synthesis cap's contested lane: an untested SP only proves out once it gets read."""
    if not kept or any(not is_proven(it) for it in kept):
        return kept  # an unproven already surfaces (or nothing was kept) -> no exploration slot needed
    unproven = [it for it in pool if not is_proven(it)]
    if not unproven:
        return kept  # nothing to explore this situation
    best_unproven = max(unproven, key=get_score)
    if len(kept) < keep:
        return kept + [best_unproven]        # free slot -> fill it (still <= keep)
    return kept[:-1] + [best_unproven]       # full -> swap out the lowest-scoring proven slot


def partition_proven_first(
    items: list[T],
    is_proven: Callable[[T], bool],
) -> list[T]:
    """STABLE partition: proven items first, unproven after, with the incoming (semantic) order preserved
    WITHIN each tier. Not a re-rank — no score touched, no re-sort — so a proven SP simply outranks an
    unproven one at equal relevance while the retrieval order otherwise stands. Used by the read path to
    tier SPs on their credit track record (proven SPs surface before never-followed churn)."""
    proven = [it for it in items if is_proven(it)]
    unproven = [it for it in items if not is_proven(it)]
    return proven + unproven


def dedup_gate(
    items: list[T],
    embeddings: list[NDArray[np.float64]],
    similarity_threshold: float = 0.87,  # ≡ 0.92 on -001 (p96 of real obs-pair sims), remapped for gemini-embedding-2's lower similarity scale — 2026-07-16 percentile check
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

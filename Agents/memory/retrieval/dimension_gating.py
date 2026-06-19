"""Soft, selective dimension-aware reweighting of retrieved memory (the v7 retrieval-precision lever).

Embedding similarity is BLIND to applicability (G3c: not_relevant items scored 0.827 vs 0.828 for
applicable — indistinguishable), yet not_relevant DOMINATES retrieval (~58%). The v6 structured dims
carry applicability signal the embedding does not (gating-efficacy screen: matching alive_bucket /
is_swing cut not_relevant 5-6pp; dist_parity was flat). This reweights each retrieved item's similarity
score by how well its STORED dims align with the QUERY's dims:

  - SOFT: a multiplicative tilt (score *= 1 + WEIGHT*alignment), never a hard drop — retrieval stays
    soft (the strict-dedup / soft-retrieval rule); a strongly-similar but dim-mismatched memory is
    demoted, not removed.
  - SELECTIVE: only dims with evidence or a strong structural prior — the two playbook-invalidating
    semantic enums (exposure_class, info_landscape_class) + the two criticality dims that screened
    helpful (alive bucket, is_swing). dist_parity is EXCLUDED (screened flat) — we do NOT gate on every
    dimension.

Deterministic, no LLM. `alignment ∈ [-1, 1]`: mean over the comparable gate dims of +1 (match) /
-1 (mismatch); dims missing on either side are skipped; 0 when nothing is comparable (score unchanged).
"""

from __future__ import annotations

from typing import Any, Callable

# Soft tilt magnitude. score *= (1 + WEIGHT * alignment), alignment in [-1, 1] → score scaled in
# [0.7x, 1.3x] at WEIGHT=0.3 — enough to reorder within the compressed bi-encoder band (~0.8 baseline)
# without ever zeroing a match.
WEIGHT = 0.3

# The two playbook-invalidating semantic enums: crossing them makes a lesson the WRONG lesson, not just
# less applicable (per the dimension spec). The dedup gate already pair-checks these; retrieval gates
# them softly.
_SEMANTIC_ENUMS = ("exposure_class", "info_landscape_class")


def _alive_bucket(n: int) -> str:
    """Match the dedup gate's bucketing: early (8-9), mid (5-7), late (<=4)."""
    return "early" if n >= 8 else "mid" if n >= 5 else "late"


def alignment(query_dims: dict[str, Any], stored_dims: dict[str, Any]) -> float:
    """Mean over the SELECTIVE gate dims of +1 (match) / -1 (mismatch). Dims absent on either side are
    skipped; returns 0.0 when nothing is comparable (a no-op tilt)."""
    scores: list[float] = []
    for field in _SEMANTIC_ENUMS:
        q, s = query_dims.get(field), stored_dims.get(field)
        if q and s:
            scores.append(1.0 if q == s else -1.0)
    qa, sa = query_dims.get("players_alive"), stored_dims.get("players_alive")
    if qa is not None and sa is not None:
        scores.append(1.0 if _alive_bucket(qa) == _alive_bucket(sa) else -1.0)
    qs, ss = query_dims.get("is_swing"), stored_dims.get("is_swing")
    if qs is not None and ss is not None:
        scores.append(1.0 if bool(qs) == bool(ss) else -1.0)
    return sum(scores) / len(scores) if scores else 0.0


def reweight(
    items: list,
    situation_to_query_dims: dict[str, dict[str, Any]],
    get_stored_dims: Callable[[Any], dict[str, Any]],
    weight: float = WEIGHT,
) -> list:
    """Reweight `items` in place by dimension alignment and return them re-sorted by the new score.

    Each item is aligned against the query dims of the SITUATION IT MATCHED (`item.matched_situation`),
    so multi-situation queries gate each item against its own query. Items with no query dims (legacy /
    no match) or no stored dims are left untouched (alignment 0).
    """
    for it in items:
        q = situation_to_query_dims.get(getattr(it, "matched_situation", None))
        if not q:
            continue
        stored = get_stored_dims(it) or {}
        if not stored:
            continue
        base = it.score if it.score is not None else 0.0
        it.score = base * (1.0 + weight * alignment(q, stored))
    items.sort(key=lambda it: it.score if it.score is not None else 0.0, reverse=True)
    return items

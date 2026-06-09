"""Embedding pre-filters that short-circuit the dedup LLM at high/low similarity extremes."""

from __future__ import annotations

import logging
from typing import Literal

from Agents.memory.store import embeddings as _embedding_model
from Agents.memory.retrieval_filters import cosine_similarity, embed_texts
from Agents.schemas import Observation, StrategyPoint

from .config import (
    OBS_CONTENT_DISCARD_THRESHOLD,
    OBS_CONTENT_KEEP_THRESHOLD,
    SP_ACTION_DISCARD_THRESHOLD,
    SP_ACTION_KEEP_THRESHOLD,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Embedding pre-filters
# ---------------------------------------------------------------------------


def _embedding_prefilter_strategy_point(
    point: StrategyPoint,
    candidates: list,
) -> tuple[Literal["discard", "keep"] | None, dict[str, float]]:
    """Compare action embeddings to decide before LLM.

    Returns (decision_or_None, similarity_scores_dict).
    """
    scores: dict[str, float] = {}
    try:
        texts = [point.action] + [c.value.get("action", "") for c in candidates]
        vecs = embed_texts(texts, _embedding_model)
        if len(vecs) < 2:
            return None, scores

        new_vec = vecs[0]
        max_action_sim = 0.0
        for i, cand_vec in enumerate(vecs[1:]):
            sim = cosine_similarity(new_vec, cand_vec)
            scores[f"action_sim_c{i + 1}"] = round(sim, 4)
            max_action_sim = max(max_action_sim, sim)

        scores["max_action_sim"] = round(max_action_sim, 4)

        if max_action_sim >= SP_ACTION_DISCARD_THRESHOLD:
            return "discard", scores
        if max_action_sim < SP_ACTION_KEEP_THRESHOLD:
            return "keep", scores
        return None, scores

    except Exception:
        logger.warning("Embedding pre-filter failed for strategy point; falling through to LLM", exc_info=True)
        return None, scores


def _embedding_prefilter_observation(
    observation: Observation,
    candidates: list,
) -> tuple[Literal["discard", "keep"] | None, dict[str, float]]:
    """Compare content embeddings to decide before LLM.

    Uses max content similarity (situation+approach+outcome concatenated) for
    both auto-discard (high end) and auto-keep (low end).

    Returns (decision_or_None, similarity_scores_dict).
    """
    scores: dict[str, float] = {}
    try:
        new_content = f"{observation.composed_situation} {observation.approach} {observation.outcome}"
        content_texts = [new_content] + [
            f"{c.value.get('situation', '')} {c.value.get('approach', '')} {c.value.get('outcome', '')}"
            for c in candidates
        ]
        content_vecs = embed_texts(content_texts, _embedding_model)
        if len(content_vecs) < 2:
            return None, scores

        new_vec = content_vecs[0]
        max_content_sim = 0.0
        for i, cand_vec in enumerate(content_vecs[1:]):
            sim = cosine_similarity(new_vec, cand_vec)
            scores[f"content_sim_c{i + 1}"] = round(sim, 4)
            max_content_sim = max(max_content_sim, sim)
        scores["max_content_sim"] = round(max_content_sim, 4)

        if max_content_sim >= OBS_CONTENT_DISCARD_THRESHOLD:
            return "discard", scores

        if max_content_sim < OBS_CONTENT_KEEP_THRESHOLD:
            return "keep", scores

        return None, scores

    except Exception:
        logger.warning("Embedding pre-filter failed for observation; falling through to LLM", exc_info=True)
        return None, scores

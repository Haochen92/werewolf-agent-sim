"""Per-item dedup orchestration, Langfuse span emission, and batch entry points."""

from __future__ import annotations

import logging

from langgraph.store.base import BaseStore

from Agents.schemas import Observation, StrategyPoint
from Agents.schemas.evaluation import DedupCase, DedupCandidate
from Agents.tracing import langfuse

from .config import DEDUP_SIMILARITY_THRESHOLD, DEDUP_TOP_N
from .formatting import _serialize_candidates
from .llm import _call_dedup_llm, _call_observation_dedup_llm
from .prefilter import _embedding_prefilter_observation, _embedding_prefilter_strategy_point
from .schemas import DedupAction, DedupResult, DedupStats
from .store_ops import (
    _apply_decision,
    _apply_observation_decision,
    _store_new_observation,
    _store_new_point,
    _update_auto_duplicate,
    _update_auto_observation_duplicate,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core dedup logic for a single observation
# ---------------------------------------------------------------------------


def dedup_single_observation(
    store: BaseStore,
    observation: Observation,
    game_id: str,
) -> DedupResult | None:
    """
    Compare a single new observation against existing entries and apply the
    LLM's dedup decision to the store.

    Returns the decision taken, or None if dedup failed (observation stored raw).
    """
    namespace = ("observations", observation.perspective, observation.action_phase)

    all_similar = store.search(
        namespace,
        query=observation.composed_situation,
        limit=DEDUP_TOP_N,
    )

    candidates = _serialize_candidates(all_similar) if all_similar else []

    similar = [
        item
        for item in all_similar
        if item.score and item.score >= DEDUP_SIMILARITY_THRESHOLD
    ]

    if not similar:
        _store_new_observation(store, namespace, observation, game_id)
        return DedupResult(
            action=DedupAction.KEEP, auto=True, candidates=candidates,
        )

    prefilter_decision, sim_scores = _embedding_prefilter_observation(
        observation, similar,
    )

    if prefilter_decision == "discard":
        top_item = similar[0]
        _update_auto_observation_duplicate(store, namespace, top_item.key, top_item)
        return DedupResult(
            action=DedupAction.DISCARD, auto=True, candidates=candidates,
            similarity_scores=sim_scores,
        )

    if prefilter_decision == "keep":
        _store_new_observation(store, namespace, observation, game_id)
        return DedupResult(
            action=DedupAction.KEEP, auto=True, candidates=candidates,
            similarity_scores=sim_scores,
        )

    decision = _call_observation_dedup_llm(observation, similar)
    if decision is None:
        return None

    action = _apply_observation_decision(
        store,
        namespace,
        observation,
        similar,
        decision,
        game_id,
    )
    return DedupResult(
        action=action,
        candidates=_serialize_candidates(similar),
        decision_detail=decision.model_dump(mode="json"),
        similarity_scores=sim_scores,
    )


# ---------------------------------------------------------------------------
# Core dedup logic for a single strategy point
# ---------------------------------------------------------------------------


def dedup_single_strategy_point(
    store: BaseStore,
    point: StrategyPoint,
    game_id: str,
) -> DedupResult | None:
    """
    Compare a single new strategy point against existing entries and
    apply the LLM's dedup decision to the store.

    Returns the decision taken, or None if dedup failed (point stored raw).
    """
    namespace = ("strategy_points", point.perspective, point.action_phase)

    all_similar = store.search(
        namespace,
        query=point.composed_situation,
        limit=DEDUP_TOP_N,
    )

    candidates = _serialize_candidates(all_similar) if all_similar else []

    similar = [
        item
        for item in all_similar
        if item.score and item.score >= DEDUP_SIMILARITY_THRESHOLD
    ]

    if not similar:
        _store_new_point(store, namespace, point, game_id)
        return DedupResult(
            action=DedupAction.KEEP, auto=True, candidates=candidates,
        )

    prefilter_decision, sim_scores = _embedding_prefilter_strategy_point(
        point, similar,
    )

    if prefilter_decision == "discard":
        top_item = similar[0]
        _update_auto_duplicate(store, namespace, top_item.key, top_item, point)
        return DedupResult(
            action=DedupAction.DISCARD, auto=True, candidates=candidates,
            similarity_scores=sim_scores,
        )

    if prefilter_decision == "keep":
        _store_new_point(store, namespace, point, game_id)
        return DedupResult(
            action=DedupAction.KEEP, auto=True, candidates=candidates,
            similarity_scores=sim_scores,
        )

    decision = _call_dedup_llm(point, similar)
    if decision is None:
        return None

    action = _apply_decision(store, namespace, point, similar, decision, game_id)
    return DedupResult(
        action=action,
        candidates=_serialize_candidates(similar),
        decision_detail=decision.model_dump(mode="json"),
        similarity_scores=sim_scores,
    )


# ---------------------------------------------------------------------------
# Trace helpers
# ---------------------------------------------------------------------------


def _emit_dedup_span(
    item_type: str,
    perspective: str,
    action_phase: str,
    index: int,
    game_id: str,
    new_entry: dict,
    result: DedupResult | None,
) -> None:
    """Emit a Langfuse span capturing one dedup decision for later eval."""
    span_name = f"dedup_{item_type}_{perspective}_{action_phase}_{index}"
    decision = result.action.value if result else "failed"
    auto = result.auto if result else False

    dedup_case = DedupCase(
        span_name=span_name,
        game_id=game_id,
        item_type=item_type,
        perspective=perspective,
        action_phase=action_phase,
        new_entry=new_entry,
        candidates=[
            DedupCandidate.model_validate(c) for c in (result.candidates if result else [])
        ],
        decision=decision,
        decision_detail=result.decision_detail if result else None,
        auto=auto,
        similarity_scores=result.similarity_scores if result else None,
    )

    with langfuse.start_as_current_observation(
        as_type="span",
        name=span_name,
        input={"new_entry": new_entry, "item_type": item_type},
        metadata={
            "eval_schema": "dedup_case_v1",
            "item_type": item_type,
            "perspective": perspective,
            "action_phase": action_phase,
            "decision": decision,
            "auto": auto,
            "candidate_count": len(dedup_case.candidates),
        },
    ) as span:
        span.update(output={"dedup_case": dedup_case.model_dump(mode="json")})


# ---------------------------------------------------------------------------
# Batch entry points
# ---------------------------------------------------------------------------


def run_observation_downstream_dedup(
    store: BaseStore,
    observations: list[Observation],
    game_id: str,
) -> DedupStats:
    """
    Run LLM-based dedup for a batch of newly extracted observations.

    For each observation:
    1. Search for similar existing entries
    2. If similar entries exist, ask the LLM how to integrate
    3. Apply the decision to the store
    4. If the LLM fails after retries, store the observation raw (fail-open)

    Returns a DedupStats summary.
    """
    stats = DedupStats()

    for i, observation in enumerate(observations, 1):
        logger.info(
            f"Observation dedup [{i}/{len(observations)}] "
            f"role={observation.perspective} "
            f"phase={observation.action_phase} "
            f"situation={observation.situation[:80]}..."
        )

        result = dedup_single_observation(store, observation, game_id)

        _emit_dedup_span(
            item_type="observation",
            perspective=observation.perspective,
            action_phase=observation.action_phase,
            index=i,
            game_id=game_id,
            new_entry={
                "situation": observation.composed_situation,
                "approach": observation.approach,
                "outcome": observation.outcome,
            },
            result=result,
        )

        if result is None:
            logger.warning(f"Observation dedup failed for item {i}; storing raw")
            _store_new_observation(
                store,
                ("observations", observation.perspective, observation.action_phase),
                observation,
                game_id,
            )
            stats.failed += 1
        elif result.action == DedupAction.KEEP:
            stats.kept += 1
            if result.auto:
                stats.auto_kept += 1
                if result.similarity_scores:
                    stats.embedding_auto_kept += 1
        elif result.action == DedupAction.DISCARD:
            stats.discarded += 1
            if result.auto:
                stats.auto_discarded += 1
                if result.similarity_scores:
                    stats.embedding_auto_discarded += 1

    logger.info(
        f"Observation dedup complete: {stats.kept} kept, "
        f"{stats.discarded} discarded, "
        f"{stats.failed} failed, "
        f"{stats.auto_kept} auto-kept ({stats.embedding_auto_kept} embedding), "
        f"{stats.auto_discarded} auto-discarded ({stats.embedding_auto_discarded} embedding)"
    )
    return stats


def run_downstream_dedup(
    store: BaseStore,
    strategy_points: list[StrategyPoint],
    game_id: str,
) -> DedupStats:
    """
    Run LLM-based dedup for a batch of newly extracted strategy points.

    For each point:
    1. Search for similar existing entries
    2. If similar entries exist, ask the LLM how to integrate
    3. Apply the decision to the store
    4. If the LLM fails after retries, store the point raw (fail-open)

    Returns a DedupStats summary.
    """
    stats = DedupStats()

    for i, point in enumerate(strategy_points, 1):
        logger.info(
            f"Dedup [{i}/{len(strategy_points)}] role={point.perspective} "
            f"phase={point.action_phase} "
            f"situation={point.situation[:80]}..."
        )

        result = dedup_single_strategy_point(store, point, game_id)

        _emit_dedup_span(
            item_type="strategy_point",
            perspective=point.perspective,
            action_phase=point.action_phase,
            index=i,
            game_id=game_id,
            new_entry={
                "situation": point.composed_situation,
                "action": point.action,
            },
            result=result,
        )

        if result is None:
            logger.warning(f"Dedup failed for point {i}; storing raw")
            _store_new_point(
                store,
                ("strategy_points", point.perspective, point.action_phase),
                point,
                game_id,
            )
            stats.failed += 1
        elif result.action == DedupAction.KEEP:
            stats.kept += 1
            if result.auto:
                stats.auto_kept += 1
                if result.similarity_scores:
                    stats.embedding_auto_kept += 1
        elif result.action == DedupAction.DISCARD:
            stats.discarded += 1
            if result.auto:
                stats.auto_discarded += 1
                if result.similarity_scores:
                    stats.embedding_auto_discarded += 1

    logger.info(
        f"Dedup complete: {stats.kept} kept, {stats.discarded} discarded, "
        f"{stats.failed} failed, {stats.auto_kept} auto-kept ({stats.embedding_auto_kept} embedding), "
        f"{stats.auto_discarded} auto-discarded ({stats.embedding_auto_discarded} embedding)"
    )
    return stats

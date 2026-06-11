"""Memory-enrichment orchestrator — the read-side pipeline.

Given an agent's day/night payload, gating produces a RetrievalPlan (what to do this turn); the
pipeline then generates situations, retrieves observations + strategy points, optionally filters
(dedup/MMR) and reranks, caps, and returns the enriched payload plus a retrieval-metadata dict for
the eval/trace record. The pipeline owns the single retriever span; the stage helpers below it stay
pure (trace-free).

``enrich_payload_with_memory`` is the whole flow top-to-bottom; the helpers below it
(skip metadata → retrieve → snapshot → filter → rerank) are the per-step detail.
"""
from __future__ import annotations

from logging import getLogger
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.llm_factory import get_llm
from Agents.memory.retrieval import (
    RERANK_TOP_K,
    RETRIEVAL_KEEP_PER_SITUATION,
    cap_per_situation,
    dedup_gate,
    mmr_filter,
    rerank_observations,
    rerank_strategy_points,
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
)
from Agents.memory.vectors import embed_texts
from Agents.memory.store import embeddings as memory_embeddings
from Agents.memory.enrichment.gating import retrieval_plan
from Agents.memory.enrichment.situation_agent import _generate_situations_for_agent
from Agents.state import (
    HealerDayState,
    InvestigatorDayState,
    VillagerDayState,
    WolfDayState,
)
from Agents.tracing import GraphContext, langfuse

logger = getLogger(__name__)


def enrich_payload_with_memory(
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
    action_phase: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    enriched_payload = dict(payload)
    active_store = runtime.store
    plan = retrieval_plan(config, payload, active_store)

    if plan.skip_reason:
        enriched_payload["retrieved_observations"] = []
        enriched_payload["strategy_points"] = payload.get("strategy_points", [])
        return enriched_payload, _skipped_metadata(plan.store_dir, plan.skip_reason)

    situations = _generate_situations_for_agent(payload)
    # Non-reranked cap = 5: the observations-only saturation point measured in
    # evidence/retrieval/capacity_limits (cap=7 regresses action quality below
    # cap=3). The wide/reranked path fetches RERANK_TOP_K, then reranks down.
    retrieval_top_k = RERANK_TOP_K if plan.needs_wide_retrieval else 5

    with langfuse.start_as_current_observation(
        as_type="retriever",
        name=(
            f"memory_retrieval_{payload['player_id']}"
            f"_day_{payload['current_day']}_round_{payload['current_round']}"
        ),
        input={"situations": situations},
        metadata={
            "player_id": payload["player_id"],
            "player_role": payload["player_role"],
            "current_day": payload["current_day"],
            "current_round": payload["current_round"],
            "action_phase": action_phase,
            "retrieve_observations": plan.retrieve_observations,
            "retrieve_strategy_points": plan.retrieve_strategy,
            "reranking_enabled": plan.reranking,
            "observation_reranking_enabled": plan.observation_reranking,
            "strategy_point_reranking_enabled": plan.strategy_point_reranking,
            "filtering_enabled": plan.filtering,
            "retrieval_top_k": retrieval_top_k,
        },
    ) as span:
        retrieved_observations, retrieved_strategy_points = _retrieve(
            active_store,
            payload,
            action_phase,
            situations,
            retrieval_top_k,
            plan.retrieve_observations,
            plan.retrieve_strategy,
        )

        pre_filter_counts = {
            "observations": len(retrieved_observations),
            "strategy_points": len(retrieved_strategy_points),
        }

        candidate_observations_json, candidate_strategy_points_json = _snapshot_candidates(
            plan.needs_wide_retrieval,
            retrieved_observations,
            retrieved_strategy_points,
        )

        if plan.filtering:
            retrieved_observations, retrieved_strategy_points = _apply_filtering(
                retrieved_observations,
                retrieved_strategy_points,
            )

        post_filter_counts = {
            "observations": len(retrieved_observations),
            "strategy_points": len(retrieved_strategy_points),
        }

        retrieved_observations, retrieved_strategy_points = _apply_reranking(
            retrieved_observations,
            retrieved_strategy_points,
            situations,
            plan.observation_reranking,
            plan.strategy_point_reranking,
        )

        retrieved_observations = cap_per_situation(
            retrieved_observations,
            get_situation=lambda o: o.matched_situation,
            get_score=lambda o: o.score or 0.0,
            keep=RETRIEVAL_KEEP_PER_SITUATION,
        )
        retrieved_strategy_points = cap_per_situation(
            retrieved_strategy_points,
            get_situation=lambda sp: sp.matched_situation,
            get_score=lambda sp: sp.score or 0.0,
            keep=RETRIEVAL_KEEP_PER_SITUATION,
        )

        retrieved_observations_json = [
            item.model_dump(mode="json") for item in retrieved_observations
        ]
        retrieved_strategy_points_json = [
            item.model_dump(mode="json") for item in retrieved_strategy_points
        ]
        span.update(
            output={
                "retrieved_observations": retrieved_observations_json,
                "retrieved_strategy_points": retrieved_strategy_points_json,
                "candidate_observations": candidate_observations_json,
                "candidate_strategy_points": candidate_strategy_points_json,
            },
            metadata={
                "num_situations": len(situations),
                "num_observations": len(retrieved_observations),
                "num_strategy_points": len(retrieved_strategy_points),
                "observation_scores": [item.score for item in retrieved_observations],
                "strategy_point_scores": [item.score for item in retrieved_strategy_points],
                "reranking_enabled": plan.reranking,
                "observation_reranking_enabled": plan.observation_reranking,
                "strategy_point_reranking_enabled": plan.strategy_point_reranking,
                "filtering_enabled": plan.filtering,
                "pre_filter_candidates": pre_filter_counts,
                "post_filter_candidates": post_filter_counts,
                "num_candidate_observations": len(candidate_observations_json),
                "num_candidate_strategy_points": len(candidate_strategy_points_json),
            }
        )

    enriched_payload["retrieved_observations"] = retrieved_observations
    enriched_payload["strategy_points"] = retrieved_strategy_points
    strategy_point_index_map = {
        i + 1: sp.key for i, sp in enumerate(retrieved_strategy_points)
    }
    enriched_payload["strategy_point_index_map"] = strategy_point_index_map
    return enriched_payload, {
        "memory_enabled": True,
        "retrieval_skipped_reason": None,
        "reranking_enabled": plan.reranking,
        "observation_reranking_enabled": plan.observation_reranking,
        "strategy_point_reranking_enabled": plan.strategy_point_reranking,
        "filtering_enabled": plan.filtering,
        "situations": situations,
        "retrieved_observations": retrieved_observations_json,
        "retrieved_strategy_points": retrieved_strategy_points_json,
        "candidate_observations": candidate_observations_json,
        "candidate_strategy_points": candidate_strategy_points_json,
        "store_dir": plan.store_dir,
        "strategy_point_index_map": strategy_point_index_map,
        "num_situations": len(situations),
        "num_observations": len(retrieved_observations),
        "num_strategy_points": len(retrieved_strategy_points),
    }


def _skipped_metadata(store_dir: str, skip_reason: str) -> dict[str, Any]:
    """The retrieval-metadata record for a skipped turn — mirrors the active-path keys, all empty."""
    return {
        "memory_enabled": False,
        "retrieval_skipped_reason": skip_reason,
        "situations": [],
        "retrieved_observations": [],
        "retrieved_strategy_points": [],
        "candidate_observations": [],
        "candidate_strategy_points": [],
        "store_dir": store_dir,
        "reranking_enabled": False,
        "filtering_enabled": False,
        "num_situations": 0,
        "num_observations": 0,
        "num_strategy_points": 0,
    }


def _retrieve(
    active_store: Any,
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
    action_phase: str,
    situations: list[str],
    retrieval_top_k: int,
    retrieve_observations: bool,
    retrieve_strategy: bool,
) -> tuple[list, list]:
    """Embedding search for observations + strategy points, each gated by its retrieval-type flag."""
    retrieved_observations = (
        retrieve_observations_for_agent(
            store=active_store,
            role=payload["player_role"],
            action_phase=action_phase,
            situations=situations,
            top_k=retrieval_top_k,
        )
        if retrieve_observations
        else []
    )
    retrieved_strategy_points = (
        retrieve_strategy_points_for_agent(
            store=active_store,
            role=payload["player_role"],
            action_phase=action_phase,
            situations=situations,
            top_k=retrieval_top_k,
        )
        if retrieve_strategy
        else []
    )
    return retrieved_observations, retrieved_strategy_points


def _snapshot_candidates(
    needs_wide_retrieval: bool,
    retrieved_observations: list,
    retrieved_strategy_points: list,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Snapshot the wide candidate pool exactly as embedding search surfaced it — before
    filtering/reranking narrows and reorders — so reranker training and retrieval eval can see what
    entered the rerank. Only when a wide retrieval ran; otherwise top-k IS the pool and the
    ``retrieved_*`` lists already carry it (kept empty here to keep cases lean)."""
    candidate_observations_json: list[dict[str, Any]] = []
    candidate_strategy_points_json: list[dict[str, Any]] = []
    if needs_wide_retrieval:
        candidate_observations_json = [
            item.model_dump(mode="json") for item in retrieved_observations
        ]
        candidate_strategy_points_json = [
            item.model_dump(mode="json") for item in retrieved_strategy_points
        ]
    return candidate_observations_json, candidate_strategy_points_json


def _apply_filtering(
    retrieved_observations: list,
    retrieved_strategy_points: list,
) -> tuple[list, list]:
    """Score-sort, then narrow: dedup-gate the observations, MMR-diversify the strategy points."""
    retrieved_observations = sorted(
        retrieved_observations,
        key=lambda o: o.score or 0.0,
        reverse=True,
    )
    retrieved_strategy_points = sorted(
        retrieved_strategy_points,
        key=lambda sp: sp.score or 0.0,
        reverse=True,
    )

    if len(retrieved_observations) > 1:
        obs_texts = [
            o.observation.situation for o in retrieved_observations
        ]
        obs_embeddings = embed_texts(obs_texts, memory_embeddings)
        retrieved_observations = dedup_gate(
            retrieved_observations, obs_embeddings,
        )

    if len(retrieved_strategy_points) > 1:
        sp_texts = [
            sp.strategy_point.situation
            for sp in retrieved_strategy_points
        ]
        sp_embeddings = embed_texts(sp_texts, memory_embeddings)
        sp_scores = [
            sp.score or 0.0 for sp in retrieved_strategy_points
        ]
        retrieved_strategy_points = mmr_filter(
            retrieved_strategy_points,
            sp_embeddings,
            sp_scores,
        )

    return retrieved_observations, retrieved_strategy_points


def _apply_reranking(
    retrieved_observations: list,
    retrieved_strategy_points: list,
    situations: list[str],
    observation_reranking: bool,
    strategy_point_reranking: bool,
) -> tuple[list, list]:
    """LLM-rerank observations and/or strategy points, sharing one LLM when either is enabled."""
    if observation_reranking or strategy_point_reranking:
        llm = get_llm()
    if observation_reranking:
        retrieved_observations = rerank_observations(
            llm, situations, retrieved_observations,
        )
    if strategy_point_reranking:
        retrieved_strategy_points = rerank_strategy_points(
            llm, situations, retrieved_strategy_points,
        )
    return retrieved_observations, retrieved_strategy_points

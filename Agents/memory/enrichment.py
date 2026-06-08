"""Memory enrichment for agent payloads — the read-side of the memory system.

Extracted from agents.py during the pre-v5 refactor (structure_audit.md group B).
Given an agent's day/night payload, generates retrieval situations, applies the
per-role/per-kind gating from the runnable config, retrieves observations and
strategy points, optionally filters (dedup/MMR) and reranks them, and returns the
enriched payload plus a retrieval-metadata dict for the eval/trace record.

The gating helpers (`_memory_enabled_for_role`, `_retrieval_type_enabled`, …) are
the Phase C independent variable and are covered by
tests/test_memory_enrichment_gating.py.
"""
from __future__ import annotations

from logging import getLogger
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.llm_factory import get_llm
from Agents.memory.core import (
    RETRIEVAL_KEEP_PER_SITUATION,
    embeddings as memory_embeddings,
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
)
from Agents.memory.reranker import (
    RERANK_TOP_K,
    rerank_observations,
    rerank_strategy_points,
)
from Agents.memory.retrieval_filters import cap_per_situation, dedup_gate, embed_texts, mmr_filter
from Agents.prompt_inputs import build_agent_prompt_input as _build_agent_prompt_input
from Agents.prompts import (
    HEALER_SITUATION_SUMMARY,
    INVESTIGATOR_SITUATION_SUMMARY,
    SERIAL_KILLER_SITUATION_SUMMARY,
    VIGILANTE_SITUATION_SUMMARY,
    VILLAGER_SITUATION_SUMMARY,
    WOLF_SITUATION_SUMMARY,
)
from Agents.schemas import SituationSummary
from Agents.state import (
    HealerDayState,
    InvestigatorDayState,
    VillagerDayState,
    WolfDayState,
)
from Agents.tracing import GraphContext, langfuse

logger = getLogger(__name__)


def _generate_situations_for_agent(
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
    max_retries: int = 1,
) -> list[str]:
    player_id = payload["player_id"]
    role = payload["player_role"]
    current_day = payload["current_day"]
    current_round = payload["current_round"]
    prompt_template = {
        "villager": VILLAGER_SITUATION_SUMMARY,
        "healer": HEALER_SITUATION_SUMMARY,
        "investigator": INVESTIGATOR_SITUATION_SUMMARY,
        "wolf": WOLF_SITUATION_SUMMARY,
        "serial_killer": SERIAL_KILLER_SITUATION_SUMMARY,
        "vigilante": VIGILANTE_SITUATION_SUMMARY,
    }.get(role, VILLAGER_SITUATION_SUMMARY)
    chain = prompt_template | get_llm().with_structured_output(SituationSummary)

    for attempt in range(max_retries + 1):
        try:
            result = chain.invoke(
                _build_agent_prompt_input(payload),
                config={
                    "run_name": (
                        f"situation_summary_{role}_day_{current_day}_round_{current_round}"
                    )
                },
            )
            return result.composed_situations
        except Exception as e:
            logger.warning(f"Situation summary LLM call failed for {player_id}: {e}")
            if attempt < max_retries:
                continue
            break

    logger.error(f"{player_id} situation summary failed all retries, using fallback")
    return [f"Day {current_day} as {role}, round {current_round}"]


def _memory_enabled_for_role(config: RunnableConfig, role: str) -> bool:
    configurable = config.get("configurable", {}) if config else {}
    memory_config = configurable.get("memory_config")
    if not isinstance(memory_config, dict):
        return True
    return bool(memory_config.get(role, False))


def _reranking_enabled_for_memory_kind(
    config: RunnableConfig,
    role: str,
    memory_kind: str,
) -> bool:
    configurable = config.get("configurable", {}) if config else {}
    reranking_config = configurable.get("reranking_config")
    if not isinstance(reranking_config, dict):
        return False
    if isinstance(reranking_config.get(memory_kind), dict):
        return bool(reranking_config[memory_kind].get(role, False))
    return False


def _filtering_enabled_for_role(config: RunnableConfig, role: str) -> bool:
    configurable = config.get("configurable", {}) if config else {}
    filtering_config = configurable.get("filtering_config")
    if not isinstance(filtering_config, dict):
        return False
    return bool(filtering_config.get(role, False))


def _retrieval_type_enabled(config: RunnableConfig, memory_kind: str) -> bool:
    configurable = config.get("configurable", {}) if config else {}
    retrieval_types_config = configurable.get("retrieval_types_config")
    if not isinstance(retrieval_types_config, dict):
        return True
    return bool(retrieval_types_config.get(memory_kind, True))


def _store_dir_from_config(config: RunnableConfig) -> str:
    """The seeded store directory = the store identity (provenance gap #4).

    Lives on ``memory_persistence_config`` in the runnable config (a
    ``MemoryPersistenceConfig`` or a plain dict, depending on call site).
    """
    configurable = (config or {}).get("configurable", {}) or {}
    mpc = configurable.get("memory_persistence_config")
    if mpc is None:
        return ""
    seed = getattr(mpc, "seed_store_dir", None)
    if seed is None and isinstance(mpc, dict):
        seed = mpc.get("seed_store_dir")
    return str(seed) if seed else ""


def _enrich_payload_with_memory(
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
    action_phase: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    enriched_payload = dict(payload)

    store_dir = _store_dir_from_config(config)
    active_store = runtime.store
    skip_reason = None
    if payload["current_day"] == 1:
        skip_reason = "day_1"
    elif active_store is None:
        skip_reason = "no_store"
    elif not _memory_enabled_for_role(config, payload["player_role"]):
        skip_reason = "memory_disabled_for_role"

    if skip_reason:
        enriched_payload["retrieved_observations"] = []
        enriched_payload["strategy_points"] = payload.get(
            "strategy_points",
            [],
        )
        return enriched_payload, {
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

    situations = _generate_situations_for_agent(payload)
    retrieve_observations = _retrieval_type_enabled(config, "observations")
    retrieve_strategy = _retrieval_type_enabled(config, "strategy_points")
    observation_reranking = _reranking_enabled_for_memory_kind(
        config,
        payload["player_role"],
        "observations",
    )
    strategy_point_reranking = _reranking_enabled_for_memory_kind(
        config,
        payload["player_role"],
        "strategy_points",
    )
    reranking = observation_reranking or strategy_point_reranking
    filtering = _filtering_enabled_for_role(config, payload["player_role"])
    needs_wide_retrieval = reranking or filtering
    retrieval_top_k = RERANK_TOP_K if needs_wide_retrieval else 3

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
            "retrieve_observations": retrieve_observations,
            "retrieve_strategy_points": retrieve_strategy,
            "reranking_enabled": reranking,
            "observation_reranking_enabled": observation_reranking,
            "strategy_point_reranking_enabled": strategy_point_reranking,
            "filtering_enabled": filtering,
            "retrieval_top_k": retrieval_top_k,
        },
    ) as span:
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

        pre_filter_counts = {
            "observations": len(retrieved_observations),
            "strategy_points": len(retrieved_strategy_points),
        }

        # Snapshot the wide candidate pool exactly as embedding search surfaced
        # it — before filtering/reranking narrows and reorders — so reranker
        # training and retrieval eval can see what entered the rerank. Only when
        # a wide retrieval ran; otherwise top-k IS the pool and ``retrieved_*``
        # already carries it (kept empty here to keep cases lean).
        candidate_observations_json: list[dict[str, Any]] = []
        candidate_strategy_points_json: list[dict[str, Any]] = []
        if needs_wide_retrieval:
            candidate_observations_json = [
                item.model_dump(mode="json") for item in retrieved_observations
            ]
            candidate_strategy_points_json = [
                item.model_dump(mode="json") for item in retrieved_strategy_points
            ]

        if filtering:
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

        post_filter_counts = {
            "observations": len(retrieved_observations),
            "strategy_points": len(retrieved_strategy_points),
        }

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
                "reranking_enabled": reranking,
                "observation_reranking_enabled": observation_reranking,
                "strategy_point_reranking_enabled": strategy_point_reranking,
                "filtering_enabled": filtering,
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
        "reranking_enabled": reranking,
        "observation_reranking_enabled": observation_reranking,
        "strategy_point_reranking_enabled": strategy_point_reranking,
        "filtering_enabled": filtering,
        "situations": situations,
        "retrieved_observations": retrieved_observations_json,
        "retrieved_strategy_points": retrieved_strategy_points_json,
        "candidate_observations": candidate_observations_json,
        "candidate_strategy_points": candidate_strategy_points_json,
        "store_dir": store_dir,
        "strategy_point_index_map": strategy_point_index_map,
        "num_situations": len(situations),
        "num_observations": len(retrieved_observations),
        "num_strategy_points": len(retrieved_strategy_points),
    }

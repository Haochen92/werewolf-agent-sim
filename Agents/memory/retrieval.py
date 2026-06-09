"""Read accessors over a langgraph BaseStore: retrieve observations / strategy points for an agent.

Stateless — the store is passed in. Moved out of core.py; re-exported from Agents.memory so the
common ``from Agents.memory import retrieve_*`` call sites are unchanged.
"""

from langgraph.store.base import BaseStore

from Agents.schemas import (
    RetrievedObservation,
    RetrievedStrategyPoint,
    StoredObservation,
    StoredStrategyPoint,
)

RETRIEVAL_KEEP_PER_SITUATION = 3


def retrieve_observations_for_agent(
    store: BaseStore,
    role: str,
    action_phase: str,
    situations: list[str],
    top_k: int = 3,
) -> list[RetrievedObservation]:
    namespace = ("observations", role, action_phase)
    retrieved_by_key: dict[str, RetrievedObservation] = {}
    for situation in situations:
        try:
            items = store.search(namespace, query=situation, limit=top_k)
            for item in items:
                retrieved_observation = RetrievedObservation(
                    key=item.key,
                    observation=StoredObservation.model_validate(item.value),
                    matched_situation=situation,
                    score=item.score,
                )
                existing = retrieved_by_key.get(item.key)
                if existing is None or (retrieved_observation.score or 0.0) > (
                    existing.score or 0.0
                ):
                    retrieved_by_key[item.key] = retrieved_observation
        except Exception:
            continue

    return list(retrieved_by_key.values())


def retrieve_strategy_points_for_agent(
    store: BaseStore,
    role: str,
    action_phase: str,
    situations: list[str],
    top_k: int = 3,
) -> list[RetrievedStrategyPoint]:
    namespace = ("strategy_points", role, action_phase)
    retrieved_by_key: dict[str, RetrievedStrategyPoint] = {}

    for situation in situations:
        try:
            items = store.search(
                namespace,
                query=situation,
                limit=top_k,
            )
            for item in items:
                retrieved_strategy_point = RetrievedStrategyPoint(
                    key=item.key,
                    strategy_point=StoredStrategyPoint.model_validate(item.value),
                    matched_situation=situation,
                    score=item.score,
                )
                existing = retrieved_by_key.get(item.key)
                if existing is None or (retrieved_strategy_point.score or 0.0) > (
                    existing.score or 0.0
                ):
                    retrieved_by_key[item.key] = retrieved_strategy_point
        except Exception:
            continue

    return list(retrieved_by_key.values())

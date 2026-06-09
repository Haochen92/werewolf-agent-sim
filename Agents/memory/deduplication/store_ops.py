"""Store mutations applying dedup decisions: new-entry writes and duplicate-count bumps."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from langgraph.store.base import BaseStore

from Agents.schemas import Observation, StoredObservation, StrategyPoint, StoredStrategyPoint

from .schemas import (
    DedupAction,
    ObservationDiscard,
    ObservationKeep,
    StrategyDiscard,
    StrategyKeep,
)

logger = logging.getLogger(__name__)


def _apply_decision(
    store: BaseStore,
    namespace: tuple[str, ...],
    point: StrategyPoint,
    similar_items: list,
    decision: StrategyDiscard | StrategyKeep,
    game_id: str,
) -> DedupAction:
    """Apply the LLM's dedup decision to the store."""

    match decision:
        case StrategyDiscard(duplicate_of_candidate=candidate):
            item = _item_for_candidate(similar_items, candidate)
            if item is not None:
                existing_value = item.value
                store.put(
                    namespace,
                    item.key,
                    {
                        "situation": existing_value.get("situation", ""),
                        "action": existing_value.get("action", ""),
                        "observation_count": existing_value.get("observation_count", 1) + 1,
                        "last_observed": datetime.now().isoformat(),
                        "game_id": game_id,
                        "retrieved_count": existing_value.get("retrieved_count", 0),
                        "used_count": existing_value.get("used_count", 0),
                        "positive_count": existing_value.get("positive_count", 0),
                        "neutral_count": existing_value.get("neutral_count", 0),
                        "negative_count": existing_value.get("negative_count", 0),
                    },
                )
            else:
                logger.warning(
                    f"DISCARD referenced invalid candidate {candidate}; storing as new"
                )
                _store_new_point(store, namespace, point, game_id)
            return DedupAction.DISCARD

        case StrategyKeep():
            store.put(
                namespace,
                str(uuid.uuid4()),
                {
                    "situation": point.composed_situation,
                    "action": point.action,
                    "observation_count": 1,
                    "last_observed": datetime.now().isoformat(),
                    "game_id": game_id,
                    "retrieved_count": 0,
                    "used_count": 0,
                    "positive_count": 0,
                    "neutral_count": 0,
                    "negative_count": 0,
                },
            )
            return DedupAction.KEEP


def _apply_observation_decision(
    store: BaseStore,
    namespace: tuple[str, ...],
    observation: Observation,
    similar_items: list,
    decision: ObservationDiscard | ObservationKeep,
    game_id: str,
) -> DedupAction:
    """Apply the LLM's observation dedup decision to the store."""

    match decision:
        case ObservationDiscard(duplicate_of_candidate=candidate):
            item = _item_for_candidate(similar_items, candidate)
            if item is not None:
                _bump_observation_count(store, namespace, item.key, item)
            else:
                logger.warning(
                    f"DISCARD referenced invalid candidate {candidate}; storing as new"
                )
                _store_new_observation(store, namespace, observation, game_id)
            return DedupAction.DISCARD

        case ObservationKeep():
            _store_new_observation(
                store,
                namespace,
                observation,
                game_id,
            )
            return DedupAction.KEEP


def _item_for_candidate(similar_items: list, candidate: int):
    index = candidate - 1
    if 0 <= index < len(similar_items):
        return similar_items[index]
    return None


def _store_new_point(
    store: BaseStore,
    namespace: tuple[str, ...],
    point: StrategyPoint,
    game_id: str,
) -> None:
    """Store a strategy point as-is with no dedup modifications."""
    stored = {
        "situation": point.composed_situation,
        "action": point.action,
        "observation_count": 1,
        "last_observed": datetime.now().isoformat(),
        "game_id": game_id,
        "retrieved_count": 0,
        "used_count": 0,
        "positive_count": 0,
        "neutral_count": 0,
        "negative_count": 0,
    }
    store.put(namespace, str(uuid.uuid4()), stored)


def _store_new_observation(
    store: BaseStore,
    namespace: tuple[str, ...],
    observation: Observation,
    game_id: str,
    situation: str | None = None,
    approach: str | None = None,
    outcome: str | None = None,
) -> None:
    """Store an observation as-is with no dedup modifications."""
    stored = {
        "situation": situation or observation.composed_situation,
        "approach": approach or observation.approach,
        "outcome": outcome or observation.outcome,
        "observation_count": 1,
        "last_observed": datetime.now().isoformat(),
        "game_id": game_id,
    }
    store.put(namespace, str(uuid.uuid4()), stored)


def _bump_observation_count(
    store: BaseStore,
    namespace: tuple[str, ...],
    key: str,
    item,
) -> None:
    """Increment observation count on an existing entry."""
    value = dict(item.value)
    value["observation_count"] = value.get("observation_count", 1) + 1
    value["last_observed"] = datetime.now().isoformat()
    store.put(namespace, key, value)


def _update_auto_observation_duplicate(
    store: BaseStore,
    namespace: tuple[str, ...],
    key: str,
    item,
) -> None:
    """Apply the high-confidence observation dedup behavior."""
    stored_observation = StoredObservation.model_validate(item.value)
    stored_observation.observation_count += 1
    stored_observation.last_observed = datetime.now()
    store.put(namespace, key, stored_observation.model_dump())


def _update_auto_duplicate(
    store: BaseStore,
    namespace: tuple[str, ...],
    key: str,
    item,
    point: StrategyPoint,
) -> None:
    """Apply the high-confidence strategy-point dedup behavior."""
    stored_point = StoredStrategyPoint.model_validate(item.value)
    stored_point.observation_count += 1
    stored_point.last_observed = datetime.now()
    stored_point.action = point.action
    store.put(namespace, key, stored_point.model_dump())

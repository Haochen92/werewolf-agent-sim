"""Store mutations that apply a dedup decision to the LangGraph store.

Three entry points, each with a strategy and an observation variant, one per
outcome ``pipeline._dedup_single_memory`` reaches (via the ``_DedupKind`` binding):

    pipeline outcome                strategy variant          observation variant
    ------------------------------  ------------------------  ----------------------------------
    KEEP (novel / prefilter-keep)   _store_new_point          _store_new_observation
    auto-DISCARD (prefilter sure)   _update_auto_duplicate    _update_auto_observation_duplicate
    LLM band (keep|discard)         _apply_strategy_decision  _apply_observation_decision

``_apply_*`` is the only branching entry; ``_item_for_candidate`` and the bumps
are its helpers. Per-function docstrings cover the behaviour.
"""

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


def _apply_strategy_decision(
    store: BaseStore,
    namespace: tuple[str, ...],
    point: StrategyPoint,
    similar_items: list,
    decision: StrategyDiscard | StrategyKeep,
    game_id: str,
) -> DedupAction:
    """Apply the LLM's strategy-point verdict — the ambiguous-middle entry point.

    DISCARD bumps the named candidate's entry in place (the inline ``store.put``
    below preserves its existing ``action``) or, if the candidate index is stale,
    falls back to ``_store_new_point``. KEEP writes the point as a new entry — the
    inline write here duplicates ``_store_new_point``. Returns the DedupAction taken.
    """

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
    """Apply the LLM's observation verdict — the ambiguous-middle entry point.

    Observation twin of ``_apply_strategy_decision``. DISCARD bumps the named candidate via
    ``_bump_observation_count`` (raw-dict mutation), or stores new if the index is
    stale. KEEP stores the observation new. Returns the DedupAction taken.
    """

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
    """Map the LLM's 1-based candidate number back to its store item, or None.

    The LLM sees candidates numbered from 1 in prompt order; this resolves that to
    the matching search hit. Out of range means the LLM named a candidate that
    isn't there — ``_apply_*`` treats that as "store the item new".
    """
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
    """Write a strategy point as a brand-new entry under a fresh uuid (the KEEP path).

    Reached for a novel point (no similar / prefilter-keep / LLM KEEP) and as the
    fallback when an LLM DISCARD names a candidate that no longer exists. Counters
    start at zero.
    """
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
) -> None:
    """Write an observation as a brand-new entry under a fresh uuid (the KEEP path).

    Observation twin of ``_store_new_point`` (same triggers): stores the
    observation as-is with usage counters at zero.
    """
    stored = {
        "situation": observation.composed_situation,
        "approach": observation.approach,
        "outcome": observation.outcome,
        "net_verdict": getattr(observation, "net_verdict", ""),
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
    """Bump an existing observation's count by mutating the raw stored dict.

    The LLM-DISCARD bump for observations (called from ``_apply_observation_decision``).
    Preserves every existing field and touches only ``observation_count`` /
    ``last_observed``. Raw-dict counterpart to ``_update_auto_observation_duplicate``,
    which instead roundtrips through the pydantic model.
    """
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
    """Bump an existing observation's count for the prefilter auto-DISCARD path.

    Reached only when the embedding prefilter is confident the new observation
    duplicates the top match. Roundtrips through ``StoredObservation`` (missing
    fields take model defaults), then increments the count. Pydantic counterpart to
    ``_bump_observation_count``; differs only in mechanism, so they are not
    interchangeable.
    """
    stored_observation = StoredObservation.model_validate(item.value)
    stored_observation.observation_count += 1
    stored_observation.last_observed = datetime.now()
    store.put(namespace, key, stored_observation.model_dump())


def _update_auto_duplicate(
    store: BaseStore,
    namespace: tuple[str, ...],
    key: str,
    item,
) -> None:
    """Bump an existing strategy point's count for the prefilter auto-DISCARD path.

    Strategy twin of ``_update_auto_observation_duplicate``: roundtrips through
    ``StoredStrategyPoint`` and increments the count, keeping the existing entry's
    content untouched. DISCARD means the new point is redundant, so its action is
    dropped rather than written over the old one — matching the LLM-DISCARD bump in
    ``_apply_strategy_decision``.
    """
    stored_point = StoredStrategyPoint.model_validate(item.value)
    stored_point.observation_count += 1
    stored_point.last_observed = datetime.now()
    store.put(namespace, key, stored_point.model_dump())

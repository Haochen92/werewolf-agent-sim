"""
Downstream per-extraction dedup for memory entries.

After each game's extraction, each new observation or strategy point is compared
against the most similar existing entries via LLM judgment. The LLM decides
whether to DISCARD, REPLACE, DIFFERENTIATE, or KEEP the new entry.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Annotated, Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.store.base import BaseStore
from pydantic import BaseModel, Field

from Agents.memory import DEDUP_THRESHOLD
from Agents.prompts.dedup import OBSERVATION_DEDUP_PROMPT, STRATEGY_DEDUP_PROMPT
from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS
from Agents.schemas import Observation, StoredObservation, StrategyPoint, StoredStrategyPoint
from Agents.schemas.evaluation import DedupCase, DedupCandidate
from Agents.tracing import langfuse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEDUP_SIMILARITY_THRESHOLD = 0.55  # Lower than rule-based to cast a wider net
DEDUP_TOP_N = 5
DEDUP_MAX_RETRIES = 2
DEDUP_MODEL = "gemini-3.1-flash-lite"
DEDUP_THINKING_LEVEL = "low"


# ---------------------------------------------------------------------------
# Schemas — strategy point dedup (unchanged structure)
# ---------------------------------------------------------------------------


class StrategyDiscard(BaseModel):
    decision: Literal["D", "DISCARD"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )
    duplicate_of_candidate: int = Field(
        ge=1,
        description="The 1-based candidate number of the existing entry this duplicates",
    )
    improved_situation: Optional[str] = Field(
        default=None,
        description=(
            "If the new entry is better written, the improved situation text "
            "to overwrite the existing entry. Omit if the existing is equal or better."
        ),
    )
    improved_action: Optional[str] = Field(
        default=None,
        description=(
            "If the new entry is better written, the improved action text "
            "to overwrite the existing entry. Omit if the existing is equal or better."
        ),
    )


class StrategyKeep(BaseModel):
    decision: Literal["K", "KEEP"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )


class StrategyDedupDecisionOutput(BaseModel):
    result: Annotated[
        StrategyDiscard | StrategyKeep,
        Field(discriminator="decision"),
    ]


# ---------------------------------------------------------------------------
# Schemas — observation dedup (structured situation/approach/outcome)
# ---------------------------------------------------------------------------


class ObservationDiscard(BaseModel):
    decision: Literal["D", "DISCARD"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )
    duplicate_of_candidate: int = Field(
        ge=1,
        description="The 1-based candidate number of the existing observation this duplicates",
    )


class ObservationMerge(BaseModel):
    decision: Literal["M", "MERGE"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )
    merge_candidate: int = Field(
        ge=1,
        description="The 1-based candidate number of the existing observation to merge with",
    )
    merged_situation: str = Field(
        description="The merged situation text, keeping the best specificity from both",
    )
    merged_approach: str = Field(
        description=(
            "The merged approach text listing ALL distinct tactics from both entries"
        ),
    )
    merged_outcome: str = Field(
        description="The merged outcome summarizing the shared lesson",
    )


class ObservationKeep(BaseModel):
    decision: Literal["K", "KEEP"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )


class ObservationDedupDecisionOutput(BaseModel):
    result: Annotated[
        ObservationDiscard
        | ObservationMerge
        | ObservationKeep,
        Field(discriminator="decision"),
    ]


# ---------------------------------------------------------------------------
# Common schemas
# ---------------------------------------------------------------------------


class DedupAction(str, Enum):
    """Compact dedup outcome label for stats and return values."""

    DISCARD = "A"
    REPLACE = "B"
    DIFFERENTIATE = "C"
    KEEP = "D"
    MERGE = "M"


class DedupResult(BaseModel):
    """Internal result with enough detail to separate auto and LLM paths."""

    action: DedupAction
    auto: bool = False
    candidates: list[dict] = Field(default_factory=list)
    decision_detail: dict | None = None


class DedupStats(BaseModel):
    """Summary of dedup outcomes for a batch of memory entries."""

    kept: int = 0
    discarded: int = 0
    replaced: int = 0
    differentiated: int = 0
    merged: int = 0
    failed: int = 0  # Fell back to raw storage
    auto_kept: int = 0
    auto_discarded: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize_candidates(items: list) -> list[dict]:
    """Serialize store search results into plain dicts for tracing."""
    result = []
    for i, item in enumerate(items, 1):
        value = item.value
        candidate: dict = {
            "candidate_number": i,
            "key": item.key,
            "similarity": round(item.score or 0.0, 4),
            "observation_count": value.get("observation_count", 1),
            "situation": value.get("situation", ""),
        }
        if "action" in value:
            candidate["action"] = value["action"]
        if "approach" in value:
            candidate["approach"] = value["approach"]
        if "outcome" in value:
            candidate["outcome"] = value["outcome"]
        result.append(candidate)
    return result


def _format_existing_entries(items: list) -> str:
    if not items:
        return "(none)"
    lines = []
    for i, item in enumerate(items, 1):
        value = item.value
        lines.append(
            f"[{i}] Candidate: {i}; Key: {item.key} "
            f"(similarity={item.score:.3f}, observed={value.get('observation_count', 1)}x)\n"
            f"    Situation: {value.get('situation', '')}\n"
            f"    Action: {value.get('action', '')}"
        )
    return "\n\n".join(lines)


def _format_existing_observations(items: list) -> str:
    if not items:
        return "(none)"
    lines = []
    for i, item in enumerate(items, 1):
        value = item.value
        lines.append(
            f"[{i}] Candidate: {i}; Key: {item.key} "
            f"(similarity={item.score:.3f}, observed={value.get('observation_count', 1)}x)\n"
            f"    Situation: {value.get('situation', '')}\n"
            f"    Approach: {value.get('approach', '')}\n"
            f"    Outcome: {value.get('outcome', '')}"
        )
    return "\n\n".join(lines)


def _get_dedup_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=DEDUP_MODEL,
        temperature=0.0,
        thinking_level=DEDUP_THINKING_LEVEL,
    )


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

    if all_similar:
        top_item = all_similar[0]
        top_score = top_item.score or 0.0
        if top_score >= DEDUP_THRESHOLD:
            _update_auto_observation_duplicate(store, namespace, top_item.key, top_item)
            return DedupResult(
                action=DedupAction.DISCARD, auto=True, candidates=candidates,
            )

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
    )


def _call_observation_dedup_llm(
    observation: Observation,
    similar_items: list,
) -> ObservationDiscard | ObservationMerge | ObservationKeep | None:
    """Call the LLM to decide how to integrate the new observation."""
    prompt = OBSERVATION_DEDUP_PROMPT.format(
        new_role=observation.perspective,
        new_situation=observation.composed_situation,
        new_approach=observation.approach,
        new_outcome=observation.outcome,
        total_similar_count=len(similar_items),
        top_n=len(similar_items),
        existing_entries=_format_existing_observations(similar_items),
    )

    llm = _get_dedup_llm()
    last_error = None

    for attempt in range(DEDUP_MAX_RETRIES + 1):
        try:
            messages = [{"role": "user", "content": prompt}]
            if last_error:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your previous response failed validation: {last_error}. "
                            f"Please fix and respond again."
                        ),
                    }
                )

            result = llm.with_structured_output(ObservationDedupDecisionOutput).invoke(
                messages,
                config={"run_name": "dedup_observation"},
            )

            if isinstance(result, ObservationDedupDecisionOutput):
                decision = result.result
            elif isinstance(result, dict):
                decision = ObservationDedupDecisionOutput.model_validate(result).result
            else:
                raise TypeError(
                    f"Unexpected observation dedup LLM result type: {type(result)!r}"
                )

            candidate_error = _candidate_validation_error(
                decision,
                len(similar_items),
            )
            if candidate_error:
                last_error = candidate_error
                continue
            return decision

        except Exception as e:
            last_error = str(e)
            logger.warning(
                "Observation dedup LLM call failed "
                f"(attempt {attempt + 1}/{DEDUP_MAX_RETRIES + 1}): {e}"
            )

    logger.error("Observation dedup LLM call failed after all retries")
    return None


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

    if all_similar:
        top_item = all_similar[0]
        top_score = top_item.score or 0.0
        if top_score >= DEDUP_THRESHOLD:
            _update_auto_duplicate(store, namespace, top_item.key, top_item, point)
            return DedupResult(
                action=DedupAction.DISCARD, auto=True, candidates=candidates,
            )

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

    decision = _call_dedup_llm(point, similar)
    if decision is None:
        return None

    action = _apply_decision(store, namespace, point, similar, decision, game_id)
    return DedupResult(
        action=action,
        candidates=_serialize_candidates(similar),
        decision_detail=decision.model_dump(mode="json"),
    )


def _call_dedup_llm(
    point: StrategyPoint,
    similar_items: list,
) -> StrategyDiscard | StrategyKeep | None:
    """Call the LLM to decide how to integrate the new point."""
    prompt = STRATEGY_DEDUP_PROMPT.format(
        situation_standards=SITUATION_STANDARDS,
        epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        new_role=point.perspective,
        new_situation=point.composed_situation,
        new_action=point.action,
        total_similar_count=len(similar_items),
        top_n=len(similar_items),
        existing_entries=_format_existing_entries(similar_items),
    )

    llm = _get_dedup_llm()
    last_error = None

    for attempt in range(DEDUP_MAX_RETRIES + 1):
        try:
            messages = [{"role": "user", "content": prompt}]
            if last_error:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your previous response failed validation: {last_error}. "
                            f"Please fix and respond again."
                        ),
                    }
                )

            result = llm.with_structured_output(StrategyDedupDecisionOutput).invoke(
                messages,
                config={"run_name": "dedup_strategy_point"},
            )

            if isinstance(result, StrategyDedupDecisionOutput):
                decision = result.result
            elif isinstance(result, dict):
                decision = StrategyDedupDecisionOutput.model_validate(result).result
            else:
                raise TypeError(f"Unexpected dedup LLM result type: {type(result)!r}")

            candidate_error = _candidate_validation_error(
                decision,
                len(similar_items),
            )
            if candidate_error:
                last_error = candidate_error
                continue
            return decision

        except Exception as e:
            last_error = str(e)
            logger.warning(
                f"Dedup LLM call failed (attempt {attempt + 1}/{DEDUP_MAX_RETRIES + 1}): {e}"
            )

    logger.error("Dedup LLM call failed after all retries")
    return None


def _candidate_validation_error(decision: BaseModel, candidate_count: int) -> str | None:
    candidate: int | None = None
    for field_name in (
        "duplicate_of_candidate",
        "merge_candidate",
    ):
        value = getattr(decision, field_name, None)
        if value is not None:
            candidate = value
            break

    if candidate is None:
        return None
    if 1 <= candidate <= candidate_count:
        return None
    return (
        f"candidate number {candidate} is invalid; choose an integer from 1 "
        f"to {candidate_count}, matching the bracketed candidate numbers."
    )


def _item_for_candidate(similar_items: list, candidate: int):
    index = candidate - 1
    if 0 <= index < len(similar_items):
        return similar_items[index]
    return None


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
        case StrategyDiscard(
            duplicate_of_candidate=candidate,
            improved_situation=improved_sit,
            improved_action=improved_act,
        ):
            item = _item_for_candidate(similar_items, candidate)
            if item is not None:
                existing_value = item.value
                situation = improved_sit or existing_value.get("situation", "")
                action = improved_act or existing_value.get("action", "")
                store.put(
                    namespace,
                    item.key,
                    {
                        "situation": situation,
                        "action": action,
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
    decision: ObservationDiscard | ObservationMerge | ObservationKeep,
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

        case ObservationMerge(
            merge_candidate=candidate,
            merged_situation=situation,
            merged_approach=approach,
            merged_outcome=outcome,
        ):
            item = _item_for_candidate(similar_items, candidate)
            if item is not None:
                existing_value = item.value
                store.put(
                    namespace,
                    item.key,
                    {
                        "situation": situation,
                        "approach": approach,
                        "outcome": outcome,
                        "observation_count": existing_value.get("observation_count", 1)
                        + 1,
                        "last_observed": datetime.now().isoformat(),
                        "game_id": game_id,
                    },
                )
            else:
                logger.warning(
                    f"MERGE referenced invalid candidate {candidate}; storing as new"
                )
                _store_new_observation(store, namespace, observation, game_id)
            return DedupAction.MERGE

        case ObservationKeep():
            _store_new_observation(
                store,
                namespace,
                observation,
                game_id,
            )
            return DedupAction.KEEP


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
        elif result.action == DedupAction.DISCARD:
            stats.discarded += 1
            if result.auto:
                stats.auto_discarded += 1
        elif result.action == DedupAction.MERGE:
            stats.merged += 1

    logger.info(
        f"Observation dedup complete: {stats.kept} kept, "
        f"{stats.discarded} discarded, {stats.merged} merged, "
        f"{stats.failed} failed, "
        f"{stats.auto_kept} auto-kept, {stats.auto_discarded} auto-discarded"
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
        elif result.action == DedupAction.DISCARD:
            stats.discarded += 1
            if result.auto:
                stats.auto_discarded += 1

    logger.info(
        f"Dedup complete: {stats.kept} kept, {stats.discarded} discarded, "
        f"{stats.failed} failed, {stats.auto_kept} auto-kept, "
        f"{stats.auto_discarded} auto-discarded"
    )
    return stats

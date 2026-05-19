"""
Downstream per-extraction dedup for strategy points.

After each game's extraction, each new strategy point is compared against
the most similar existing entries via LLM judgment. The LLM decides whether
to DISCARD, REPLACE, DIFFERENTIATE, or KEEP the new point.
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
from Agents.prompts.standards import SITUATION_STANDARDS
from Agents.schemas import StrategyPoint, StoredStrategyPoint

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEDUP_SIMILARITY_THRESHOLD = 0.55  # Lower than rule-based to cast a wider net
DEDUP_TOP_N = 5
DEDUP_MAX_RETRIES = 2
DEDUP_MODEL = "gemini-2.5-flash"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class Discard(BaseModel):
    decision: Literal["A", "DISCARD"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )
    duplicate_of_candidate: int = Field(
        ge=1,
        description="The 1-based candidate number of the existing entry this duplicates",
    )


class Replace(BaseModel):
    decision: Literal["B", "REPLACE"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )
    replace_candidate: int = Field(
        ge=1,
        description="The 1-based candidate number of the existing entry to replace",
    )
    merged_situation: str = Field(
        description="The merged situation text, keeping the best elements of both",
    )
    merged_action: str = Field(
        description="The merged action text, keeping the best elements of both",
    )


class Differentiate(BaseModel):
    decision: Literal["C", "DIFFERENTIATE"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )
    distinguishing_variable: str = Field(
        description=(
            "The situational variable that distinguishes the two entries "
            "(e.g., consensus strength, game phase)"
        ),
    )
    existing_candidate: int = Field(
        ge=1,
        description="The 1-based candidate number of the existing entry to rewrite",
    )
    existing_rewritten_situation: str = Field(
        description="Rewritten situation for the existing entry",
    )
    existing_rewritten_action: Optional[str] = Field(
        default=None,
        description="Rewritten action for the existing entry (if changed)",
    )
    new_rewritten_situation: str = Field(
        description="Rewritten situation for the new entry",
    )
    new_rewritten_action: Optional[str] = Field(
        default=None,
        description="Rewritten action for the new entry (if changed)",
    )


class Keep(BaseModel):
    decision: Literal["D", "KEEP"]
    reasoning: str = Field(
        description="2-3 sentences explaining the decision",
    )
    new_rewritten_situation: Optional[str] = Field(
        default=None,
        description="Rewritten situation for the new entry, if minor wording improvements are suggested",
    )
    new_rewritten_action: Optional[str] = Field(
        default=None,
        description="Rewritten action for the new entry, if minor wording improvements are suggested",
    )

class DedupDecisionOutput(BaseModel):
    result: Annotated[
        Discard | Replace | Differentiate | Keep,
        Field(discriminator="decision"),
    ]


class DedupAction(str, Enum):
    """Compact dedup outcome label for stats and return values."""

    DISCARD = "A"
    REPLACE = "B"
    DIFFERENTIATE = "C"
    KEEP = "D"


class DedupResult(BaseModel):
    """Internal result with enough detail to separate auto and LLM paths."""

    action: DedupAction
    auto: bool = False


class DedupStats(BaseModel):
    """Summary of dedup outcomes for a batch of strategy points."""

    kept: int = 0
    discarded: int = 0
    replaced: int = 0
    differentiated: int = 0
    failed: int = 0  # Fell back to raw storage
    auto_kept: int = 0
    auto_discarded: int = 0


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

PER_EXTRACTION_DEDUP_PROMPT = """
You are maintaining a strategy database for an AI Werewolf agent. A new
strategy point has just been extracted from a game. Your job is to compare
it against the most similar existing entries and decide how to integrate it.

{situation_standards}

All situation fields you write or rewrite must conform to the standards above.
For the structured output field named "decision", use exactly the letter tag
"A", "B", "C", or "D"; do not use DISCARD, REPLACE, DIFFERENTIATE, or KEEP.

---

NEW EXTRACTION:
Role: {new_role}
Situation: {new_content}
Action: {new_action}

SIMILAR EXISTING ENTRIES ({total_similar_count} entries above similarity
threshold; top {top_n} shown):
{existing_entries}

---

Decide ONE of the following outcomes:

(A) DISCARD — The new point is a duplicate of an existing entry. Both the
    situation and action express the same idea, even if worded differently.
    Output: the candidate number of the entry it duplicates.

(B) REPLACE — The new point covers the same situation and action as an
    existing entry, but is more specific, better reasoned, or captures a
    nuance the existing entry misses. Output: the candidate number to
    replace, and the final merged situation + action (keeping the best
    elements of both).

(C) DIFFERENTIATE — The new point describes a similar situation but
    recommends a meaningfully different action. This is an action-spectrum
    case: both actions may be correct under slightly different conditions.
    Output: identify the situational variable that distinguishes them —
    typically one of: information landscape (what evidence exists), consensus
    texture (how strong or fragile agreement is), social pressure dynamics
    (who is driving accusations and how), or game phase (early/mid/endgame).
    Then rewrite BOTH situations to make the distinguishing variable explicit
    in the text. Do not split into more than 3 entries along any single
    variable.

(D) KEEP — The new point is genuinely novel. No existing entry covers this
    situation or this action. Output: confirm it should be added as-is, or
    suggest minor wording improvements.

DECISION RULES:
- If the new point would be the 4th+ entry on the same spectrum, prefer
  merging it into the closest existing entry over creating another split.
- "Same idea, different words" is a duplicate, not a differentiation. The
  test: would a player in that situation do anything differently based on
  reading one entry vs. the other? If no, it is a duplicate.
- For REPLACE and DIFFERENTIATE, the output must meet the quality bar in the
  situation standards above: the situation must describe a recognizable game
  dynamic using the dimensional framework and epistemic status rule. The
  action must explain a non-obvious mechanism, not restate common-sense play.
- When an output field asks for a candidate number, use only the bracketed
  candidate number shown in SIMILAR EXISTING ENTRIES. Do not output UUID keys.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_existing_entries(items: list) -> str:
    if not items:
        return "(none)"
    lines = []
    for i, item in enumerate(items, 1):
        value = item.value
        lines.append(
            f"[{i}] Candidate: {i}; Key: {item.key} "
            f"(similarity={item.score:.3f}, observed={value.get('observation_count', 1)}x)\n"
            f"    Situation: {value.get('content', '')}\n"
            f"    Action: {value.get('action', '')}"
        )
    return "\n\n".join(lines)


def _get_dedup_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=DEDUP_MODEL, temperature=0.0)


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
    namespace = ("strategy_points", point.perspective)

    # Search for similar existing entries
    all_similar = store.search(
        namespace,
        query=point.situation,
        limit=DEDUP_TOP_N,
    )

    if all_similar:
        top_item = all_similar[0]
        top_score = top_item.score or 0.0
        if top_score >= DEDUP_THRESHOLD:
            _update_auto_duplicate(store, namespace, top_item.key, top_item, point)
            return DedupResult(action=DedupAction.DISCARD, auto=True)

    similar = [
        item
        for item in all_similar
        if item.score and item.score >= DEDUP_SIMILARITY_THRESHOLD
    ]

    # No similar entries — store directly as novel
    if not similar:
        _store_new_point(store, namespace, point, game_id)
        return DedupResult(action=DedupAction.KEEP, auto=True)

    # Build prompt and call LLM
    decision = _call_dedup_llm(point, similar)
    if decision is None:
        return None

    # Apply decision to store
    action = _apply_decision(store, namespace, point, similar, decision, game_id)
    return DedupResult(action=action)


def _call_dedup_llm(
    point: StrategyPoint,
    similar_items: list,
) -> Discard | Replace | Differentiate | Keep | None:
    """Call the LLM to decide how to integrate the new point."""
    prompt = PER_EXTRACTION_DEDUP_PROMPT.format(
        situation_standards=SITUATION_STANDARDS,
        new_role=point.perspective,
        new_content=point.situation,
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

            result = llm.with_structured_output(DedupDecisionOutput).invoke(
                messages,
                config={"run_name": "dedup_strategy_point"},
            )

            if isinstance(result, DedupDecisionOutput):
                decision = result.result
            elif isinstance(result, dict):
                decision = DedupDecisionOutput.model_validate(result).result
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


def _candidate_validation_error(
    decision: Discard | Replace | Differentiate | Keep,
    candidate_count: int,
) -> str | None:
    candidate: int | None = None
    if isinstance(decision, Discard):
        candidate = decision.duplicate_of_candidate
    elif isinstance(decision, Replace):
        candidate = decision.replace_candidate
    elif isinstance(decision, Differentiate):
        candidate = decision.existing_candidate

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
    namespace: tuple[str, str],
    point: StrategyPoint,
    similar_items: list,
    decision: Discard | Replace | Differentiate | Keep,
    game_id: str,
) -> DedupAction:
    """Apply the LLM's dedup decision to the store."""

    match decision:
        case Discard(duplicate_of_candidate=candidate):
            item = _item_for_candidate(similar_items, candidate)
            if item is not None:
                _bump_observation_count(store, namespace, item.key, item)
            else:
                logger.warning(
                    f"DISCARD referenced invalid candidate {candidate}; storing as new"
                )
                _store_new_point(store, namespace, point, game_id)
            return DedupAction.DISCARD

        case Replace(replace_candidate=candidate, merged_situation=sit, merged_action=act):
            item = _item_for_candidate(similar_items, candidate)
            if item is not None:
                existing_value = item.value
                store.put(
                    namespace,
                    item.key,
                    {
                        "content": sit,
                        "action": act,
                        "observation_count": existing_value.get("observation_count", 1) + 1,
                        "last_observed": datetime.now().isoformat(),
                        "game_id": game_id,
                    },
                )
            else:
                logger.warning(
                    f"REPLACE referenced invalid candidate {candidate}; storing as new"
                )
                _store_new_point(store, namespace, point, game_id)
            return DedupAction.REPLACE

        case Differentiate(
            existing_candidate=candidate,
            existing_rewritten_situation=ex_sit,
            existing_rewritten_action=ex_act,
            new_rewritten_situation=new_sit,
            new_rewritten_action=new_act,
        ):
            item = _item_for_candidate(similar_items, candidate)
            if item is not None:
                existing_value = item.value
                store.put(
                    namespace,
                    item.key,
                    {
                        "content": ex_sit,
                        "action": ex_act or existing_value.get("action", ""),
                        "observation_count": existing_value.get("observation_count", 1),
                        "last_observed": existing_value.get(
                            "last_observed", datetime.now().isoformat()
                        ),
                        "game_id": existing_value.get("game_id", ""),
                    },
                )
                store.put(
                    namespace,
                    str(uuid.uuid4()),
                    {
                        "content": new_sit,
                        "action": new_act or point.action,
                        "observation_count": 1,
                        "last_observed": datetime.now().isoformat(),
                        "game_id": game_id,
                    },
                )
            else:
                logger.warning(
                    f"DIFFERENTIATE referenced invalid candidate {candidate}; storing as new"
                )
                _store_new_point(store, namespace, point, game_id)
            return DedupAction.DIFFERENTIATE

        case Keep(new_rewritten_situation=sit, new_rewritten_action=act):
            store.put(
                namespace,
                str(uuid.uuid4()),
                {
                    "content": sit or point.situation,
                    "action": act or point.action,
                    "observation_count": 1,
                    "last_observed": datetime.now().isoformat(),
                    "game_id": game_id,
                },
            )
            return DedupAction.KEEP


def _store_new_point(
    store: BaseStore,
    namespace: tuple[str, str],
    point: StrategyPoint,
    game_id: str,
) -> None:
    """Store a strategy point as-is with no dedup modifications."""
    stored = {
        "content": point.situation,
        "action": point.action,
        "observation_count": 1,
        "last_observed": datetime.now().isoformat(),
        "game_id": game_id,
    }
    store.put(namespace, str(uuid.uuid4()), stored)


def _bump_observation_count(
    store: BaseStore,
    namespace: tuple[str, str],
    key: str,
    item,
) -> None:
    """Increment observation count on an existing entry."""
    value = dict(item.value)
    value["observation_count"] = value.get("observation_count", 1) + 1
    value["last_observed"] = datetime.now().isoformat()
    store.put(namespace, key, value)


def _update_auto_duplicate(
    store: BaseStore,
    namespace: tuple[str, str],
    key: str,
    item,
    point: StrategyPoint,
) -> None:
    """Apply the old high-confidence strategy-point dedup behavior."""
    stored_point = StoredStrategyPoint.model_validate(item.value)
    stored_point.observation_count += 1
    stored_point.last_observed = datetime.now()
    stored_point.action = point.action
    store.put(namespace, key, stored_point.model_dump())


# ---------------------------------------------------------------------------
# Batch entry point
# ---------------------------------------------------------------------------


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
            f"situation={point.situation[:80]}..."
        )

        result = dedup_single_strategy_point(store, point, game_id)

        if result is None:
            # LLM failed — store raw as fallback
            logger.warning(f"Dedup failed for point {i}; storing raw")
            _store_new_point(
                store,
                ("strategy_points", point.perspective),
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
        elif result.action == DedupAction.REPLACE:
            stats.replaced += 1
        elif result.action == DedupAction.DIFFERENTIATE:
            stats.differentiated += 1

    logger.info(
        f"Dedup complete: {stats.kept} kept, {stats.discarded} discarded, "
        f"{stats.replaced} replaced, {stats.differentiated} differentiated, "
        f"{stats.failed} failed, {stats.auto_kept} auto-kept, "
        f"{stats.auto_discarded} auto-discarded"
    )
    return stats

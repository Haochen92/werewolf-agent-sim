"""Per-item dedup orchestration, Langfuse span emission, and batch entry points.

## Steps (per item, in _dedup_single_memory):
1. Search the store for the DEDUP_TOP_N most similar existing entries, using the new item's situation text as the query.
2. Threshold filter — keep only hits scoring ≥ DEDUP_SIMILARITY_THRESHOLD. If nothing clears it, the item is clearly novel: store it, return auto-KEEP. No LLM involved.
3. Similarity prefilter (the per-kind discard/keep cutoffs in config.py) — currently a static
   bi-encoder: cosine of independently embedded texts (prefilter.py). If the top match is extremely
   similar, it's an obvious duplicate: bump the existing entry's counts, return auto-DISCARD. If
   similarity is low enough, obviously novel: store, auto-KEEP. Both skip the LLM. (A fine-tuned
   cross-encoder is the planned swap-in here — see the fine-tuning plan — not yet wired in.)
4. LLM fallback — only the ambiguous middle band reaches here. The LLM decides keep or discard; apply_decision writes the outcome to the store. (Merge lives in the offline batch_deduplication module, not here.)
5. Fail-open — if the LLM errors out after retries, return None; the batch loop stores the item raw rather than losing a memory.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from langgraph.store.base import BaseStore

from Agents.memory.dedup_gate import gate_filter_for
from Agents.observability import EvalCaseSink, dedup_span_name, freeze_case
from Agents.schemas import Observation, StrategyPoint
from Agents.schemas.evaluation import DedupCase, DedupCandidate
from Agents.tracing import langfuse

from .config import DEDUP_SIMILARITY_THRESHOLD, DEDUP_TOP_N
from .formatting import _serialize_candidates
from .dedup_agent import _dedup_agent, _observation_dedup_agent
from .prefilter import _embedding_prefilter_observation, _embedding_prefilter_strategy_point
from .schemas import DedupAction, DedupResult, DedupStats
from .store_ops import (
    _apply_observation_decision,
    _apply_strategy_decision,
    _store_new_observation,
    _store_new_point,
    _update_auto_duplicate,
    _update_auto_observation_duplicate,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Per-kind bindings
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _DedupKind:
    """The per-kind operations the shared pipeline is parameterised over."""

    item_type: str
    memory_kind: str
    log_label: str
    fail_noun: str
    new_entry: Callable[[Any], dict]
    prefilter: Callable[..., Any]
    call_llm: Callable[..., Any]
    apply_decision: Callable[..., Any]
    store_new: Callable[..., Any]
    update_auto_duplicate: Callable[..., Any]


_OBSERVATION_KIND = _DedupKind(
    item_type="observation",
    memory_kind="observations",
    log_label="Observation dedup",
    fail_noun="item",
    new_entry=lambda o: {
        "situation": o.composed_situation,
        "approach": o.approach,
        "outcome": o.outcome,
    },
    prefilter=_embedding_prefilter_observation,
    call_llm=_observation_dedup_agent,
    apply_decision=_apply_observation_decision,
    store_new=_store_new_observation,
    update_auto_duplicate=lambda store, namespace, top_item, item: (
        _update_auto_observation_duplicate(store, namespace, top_item.key, top_item)
    ),
)

_STRATEGY_POINT_KIND = _DedupKind(
    item_type="strategy_point",
    memory_kind="strategy_points",
    log_label="Dedup",
    fail_noun="point",
    new_entry=lambda p: {
        "situation": p.composed_situation,
        "action": p.action,
    },
    prefilter=_embedding_prefilter_strategy_point,
    call_llm=_dedup_agent,
    apply_decision=_apply_strategy_decision,
    store_new=_store_new_point,
    update_auto_duplicate=lambda store, namespace, top_item, item: (
        _update_auto_duplicate(store, namespace, top_item.key, top_item)
    ),
)


# ---------------------------------------------------------------------------
# Batch entry points
# ---------------------------------------------------------------------------


def run_downstream_observation_dedup(
    store: BaseStore,
    observations: list[Observation],
    game_id: str,
    sink: EvalCaseSink | None = None,
) -> DedupStats:
    """
    Run LLM-based dedup for a batch of newly extracted observations.

    For each observation:
    1. Search for similar existing entries
    2. If similar entries exist, ask the LLM how to integrate
    3. Apply the decision to the store
    4. If the LLM fails after retries, store the observation raw (fail-open)

    Returns a DedupStats summary. The pipeline runs below the graph runtime,
    so the in-game caller threads its eval-case *sink* in; offline callers
    (tests, labeling adapters) omit it and emit to Langfuse only.
    """
    return _dedup_memory_items(store, observations, game_id, _OBSERVATION_KIND, sink)


def run_downstream_strategy_dedup(
    store: BaseStore,
    strategy_points: list[StrategyPoint],
    game_id: str,
    sink: EvalCaseSink | None = None,
) -> DedupStats:
    """
    Run LLM-based dedup for a batch of newly extracted strategy points.

    For each point:
    1. Search for similar existing entries
    2. If similar entries exist, ask the LLM how to integrate
    3. Apply the decision to the store
    4. If the LLM fails after retries, store the point raw (fail-open)

    Returns a DedupStats summary. (Same *sink* contract as the observation
    entry point above.)
    """
    return _dedup_memory_items(store, strategy_points, game_id, _STRATEGY_POINT_KIND, sink)


def _dedup_memory_items(
    store: BaseStore,
    items: list[Observation] | list[StrategyPoint],
    game_id: str,
    kind: _DedupKind,
    sink: EvalCaseSink | None = None,
) -> DedupStats:
    stats = DedupStats()

    for i, item in enumerate(items, 1):
        logger.info(
            f"{kind.log_label} [{i}/{len(items)}] "
            f"role={item.perspective} "
            f"phase={item.action_phase} "
            f"situation={item.situation[:80]}..."
        )

        result = _dedup_single_memory(store, item, game_id, kind)

        _emit_dedup_span(
            item_type=kind.item_type,
            perspective=item.perspective,
            action_phase=item.action_phase,
            index=i,
            game_id=game_id,
            new_entry=kind.new_entry(item),
            result=result,
            sink=sink,
        )

        if result is None:
            logger.warning(f"{kind.log_label} failed for {kind.fail_noun} {i}; storing raw")
            kind.store_new(
                store,
                (kind.memory_kind, item.perspective, item.action_phase),
                item,
                game_id,
            )
            stats.failed += 1
        else:
            _tally_result(stats, result)

    logger.info(
        f"{kind.log_label} complete: {stats.kept} kept, "
        f"{stats.discarded} discarded, "
        f"{stats.failed} failed, "
        f"{stats.auto_kept} auto-kept ({stats.embedding_auto_kept} embedding), "
        f"{stats.auto_discarded} auto-discarded ({stats.embedding_auto_discarded} embedding)"
    )
    return stats


def _tally_result(stats: DedupStats, result: DedupResult) -> None:
    if result.action == DedupAction.KEEP:
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


# ---------------------------------------------------------------------------
# Core dedup logic for a single item
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
    return _dedup_single_memory(store, observation, game_id, _OBSERVATION_KIND)


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
    return _dedup_single_memory(store, point, game_id, _STRATEGY_POINT_KIND)


def _dedup_single_memory(
    store: BaseStore,
    item: Observation | StrategyPoint,
    game_id: str,
    kind: _DedupKind,
) -> DedupResult | None:
    namespace = (kind.memory_kind, item.perspective, item.action_phase)

    all_similar = store.search(
        namespace,
        query=item.composed_situation,
        limit=DEDUP_TOP_N,
    )

    candidates = _serialize_candidates(all_similar) if all_similar else []

    similar = [
        candidate
        for candidate in all_similar
        if candidate.score and candidate.score >= DEDUP_SIMILARITY_THRESHOLD
    ]

    # Structured GATE (v6): keep only candidates in the same criticality/consensus bucket AND with the
    # same net_verdict, so the cosine/LLM only ever compares already-homogeneous entries. No-op for v5
    # entries (no v6 fields). This is the gate-then-embed partition — it does the "same situation" work
    # deterministically so the LLM is left with the free-text residual.
    similar = gate_filter_for(kind.memory_kind, item, similar)

    if not similar:
        kind.store_new(store, namespace, item, game_id)
        return DedupResult(
            action=DedupAction.KEEP, auto=True, candidates=candidates,
        )

    prefilter_decision, sim_scores = kind.prefilter(item, similar)

    if prefilter_decision == "discard":
        kind.update_auto_duplicate(store, namespace, similar[0], item)
        return DedupResult(
            action=DedupAction.DISCARD, auto=True, candidates=candidates,
            similarity_scores=sim_scores,
        )

    if prefilter_decision == "keep":
        kind.store_new(store, namespace, item, game_id)
        return DedupResult(
            action=DedupAction.KEEP, auto=True, candidates=candidates,
            similarity_scores=sim_scores,
        )

    decision = kind.call_llm(item, similar)
    if decision is None:
        return None

    action = kind.apply_decision(store, namespace, item, similar, decision, game_id)
    # The auto paths report every search hit; here only the above-threshold
    # candidates the LLM actually saw.
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
    sink: EvalCaseSink | None = None,
) -> None:
    """Emit a Langfuse span capturing one dedup decision for later eval,
    teeing the case to the local *sink* when one is threaded in."""
    span_name = dedup_span_name(item_type, perspective, action_phase, index)
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
        span.update(
            output={
                "dedup_case": freeze_case(
                    span,
                    dedup_case,
                    kind="dedup",
                    case_key="dedup_case",
                    sink=sink,
                ),
            }
        )

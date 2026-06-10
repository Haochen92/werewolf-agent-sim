"""LLM resolution of a single near-duplicate cluster.

Given one cluster's formatted entries, calls the batch-dedup model (with the role/phase-appropriate
prompt + schema) and remaps the returned operation keys back to store keys. ``_two_pass_cluster_dedup``
wraps this in a fast-triage → targeted-verify escalation: only MERGE-flagged entries are re-evaluated
by the stronger verify model. This is the eval-relevant stage (prompt variant, model, thinking level,
single- vs two-pass are the levers we ablate); the orchestration loop calls in here per cluster.
"""

from __future__ import annotations

import logging
from typing import Any

from Agents.llm_factory import get_llm_batch_dedup
from Agents.prompts.dedup import (
    BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT,
    BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT_LITE,
    BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT,
)
from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS

from .config import TwoPassConfig
from .formatting import _format_cluster_entries
from .operations import _remap_operation_keys
from .schemas import (
    MemoryKind,
    ObservationBatchDedupOutput,
    ObservationBatchOperation,
    StrategyBatchDedupOutput,
    StrategyBatchOperation,
)

_OBS_PROMPT_VARIANTS = {
    "default": BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT,
    "lite": BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT_LITE,
}

logger = logging.getLogger(__name__)


def _two_pass_cluster_dedup(
    memory_kind: MemoryKind,
    role: str,
    action_phase: str,
    live_cluster_keys: list[str],
    items_by_key: dict[str, Any],
    two_pass: TwoPassConfig,
) -> StrategyBatchDedupOutput | ObservationBatchDedupOutput:
    """Run two-pass dedup on a single cluster.

    Pass 1: triage model classifies all entries.
    Pass 2: verify model re-evaluates only MERGE-flagged entries.
    Returns a combined output with trusted + verified operations.
    """
    entries, index_to_key = _format_cluster_entries(
        memory_kind, live_cluster_keys, items_by_key,
    )

    triage_result = _call_cluster_llm(
        memory_kind, role, action_phase, entries, index_to_key,
        model=two_pass.triage_model,
        thinking_level=two_pass.triage_thinking_level,
    )

    trusted_ops = []
    merge_keys: set[str] = set()

    for op in triage_result.operations:
        if op.action == "MERGE":
            merge_keys.update(op.source_keys)
        else:
            trusted_ops.append(op)

    if not merge_keys:
        return triage_result

    logger.info(
        "Two-pass: triage flagged %d keys as MERGE in cluster of %d, "
        "escalating to verify model",
        len(merge_keys), len(live_cluster_keys),
    )

    verify_keys = [k for k in live_cluster_keys if k in merge_keys]
    if len(verify_keys) < 2:
        for op in triage_result.operations:
            if op.action == "MERGE":
                _downgrade_merge_to_keep(op)
        return triage_result

    verify_entries, verify_index_to_key = _format_cluster_entries(
        memory_kind, verify_keys, items_by_key,
    )
    verify_result = _call_cluster_llm(
        memory_kind, role, action_phase, verify_entries, verify_index_to_key,
        model=two_pass.verify_model,
        thinking_level=two_pass.verify_thinking_level,
    )

    all_ops = trusted_ops + list(verify_result.operations)
    if memory_kind == "strategy_points":
        return StrategyBatchDedupOutput(operations=all_ops)
    return ObservationBatchDedupOutput(operations=all_ops)


def _call_cluster_llm(
    memory_kind: MemoryKind,
    role: str,
    action_phase: str,
    entries: str,
    index_to_key: dict[str, str],
    model: str,
    thinking_level: str | None,
    prompt_variant: str = "default",
) -> StrategyBatchDedupOutput | ObservationBatchDedupOutput:
    llm = get_llm_batch_dedup(model, thinking_level)
    if memory_kind == "strategy_points":
        prompt = BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT.format(
            role=role,
            action_phase=action_phase,
            entries=entries,
            situation_standards=SITUATION_STANDARDS,
            epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        )
        output_schema = StrategyBatchDedupOutput
        run_name = "batch_dedup_strategy_points"
    else:
        obs_prompt_template = _OBS_PROMPT_VARIANTS.get(
            prompt_variant, BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT,
        )
        prompt = obs_prompt_template.format(
            role=role,
            action_phase=action_phase,
            entries=entries,
            situation_standards=SITUATION_STANDARDS,
        )
        output_schema = ObservationBatchDedupOutput
        run_name = "batch_dedup_observations"

    result = llm.with_structured_output(output_schema).invoke(
        [{"role": "user", "content": prompt}],
        config={"run_name": run_name, "callbacks": [_langfuse_handler()]},
    )
    if isinstance(result, dict):
        result = output_schema.model_validate(result)
    elif not isinstance(result, output_schema):
        raise TypeError(f"Unexpected batch dedup result type: {type(result)!r}")

    for op in result.operations:
        _remap_operation_keys(op, index_to_key)
    return result


def _downgrade_merge_to_keep(
    op: StrategyBatchOperation | ObservationBatchOperation,
) -> None:
    """Turn a MERGE the verify pass can't act on into a plain KEEP, clearing all merge text."""
    op.action = "KEEP"
    op.survivor_key = None
    for field in ("merged_situation", "merged_action", "merged_approach", "merged_outcome"):
        if hasattr(op, field):
            setattr(op, field, None)


def _langfuse_handler():
    from langfuse.langchain import CallbackHandler
    return CallbackHandler()

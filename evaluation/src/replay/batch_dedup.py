"""Replay the batch cluster-dedup prompt on a frozen cluster with a chosen model.

Formats a cluster's entries with numbered indices, invokes the observation or
strategy batch-dedup prompt (single-pass or two-pass triage->verify), and returns
the model's operations remapped back to real keys. Deterministic golden scoring of
these operations lives in ``audits.batch_dedup_score``; the CLI wrapper
(``experiments/cli_runners/batch_dedup_judge``) chains regen + score.
"""

from __future__ import annotations

from typing import Any

from Agents.llm_factory import create_chat_model
from Agents.memory.batch_deduplication import (
    ObservationBatchDedupOutput,
    StrategyBatchDedupOutput,
)
from Agents.prompts.dedup import (
    BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT,
    BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT_LITE,
    BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT,
)
from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS

PROMPT_VARIANTS = {
    "default": {
        "observation": BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT,
        "strategy": BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT,
    },
    "lite": {
        "observation": BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT_LITE,
        "strategy": BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT,
    },
}


def format_entries(cluster: dict) -> tuple[str, dict[str, str]]:
    """Format cluster entries using numbered indices, returning index-to-key map."""
    lines: list[str] = []
    index_to_key: dict[str, str] = {}
    for i, item in enumerate(cluster["items"], 1):
        index_to_key[str(i)] = item["key"]
        val = item.get("value", item)
        lines.append(f"[{i}]")
        lines.append(f"observation_count: {val.get('observation_count', 1)}")
        lines.append(f"last_observed: {val.get('last_observed', 'N/A')}")
        lines.append(f"situation: {val.get('situation', '')}")
        if cluster["kind"] == "strategy_points":
            lines.append(f"action: {val.get('action', '')}")
        else:
            lines.append(f"approach: {val.get('approach', '')}")
            lines.append(f"outcome: {val.get('outcome', '')}")
        lines.append("")
    return "\n".join(lines).strip(), index_to_key


def _remap_keys(source_keys: list[str], index_to_key: dict[str, str]) -> list[str]:
    return [index_to_key.get(k, k) for k in source_keys]


def _extract_ops(result, index_to_key: dict[str, str]) -> list[dict]:
    ops = []
    for op in result.operations:
        d = {
            "action": op.action,
            "source_keys": _remap_keys(op.source_keys, index_to_key),
        }
        if op.survivor_key:
            d["survivor_key"] = index_to_key.get(op.survivor_key, op.survivor_key)
        if hasattr(op, "merged_situation") and op.merged_situation:
            d["merged_situation"] = op.merged_situation
        if hasattr(op, "merged_approach") and op.merged_approach:
            d["merged_approach"] = op.merged_approach
        if hasattr(op, "merged_outcome") and op.merged_outcome:
            d["merged_outcome"] = op.merged_outcome
        if hasattr(op, "merged_action") and op.merged_action:
            d["merged_action"] = op.merged_action
        if hasattr(op, "reasoning"):
            d["reasoning"] = op.reasoning
        ops.append(d)
    return ops


def _invoke_model(
    cluster: dict,
    model: str,
    thinking_level: str | None,
    entries: str,
    index_to_key: dict[str, str],
    prompt_variant: str = "default",
):
    llm = create_chat_model(model, temperature=0.0, thinking_level=thinking_level)
    ns = cluster["namespace"]
    role = ns[1] if isinstance(ns, list) else ns.split("/")[1]
    action_phase = ns[2] if isinstance(ns, list) else ns.split("/")[2]
    kind = cluster["kind"]

    prompts = PROMPT_VARIANTS[prompt_variant]

    if kind == "strategy_points":
        prompt = prompts["strategy"].format(
            role=role,
            action_phase=action_phase,
            entries=entries,
            situation_standards=SITUATION_STANDARDS,
            epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        )
        schema = StrategyBatchDedupOutput
    else:
        prompt = prompts["observation"].format(
            role=role,
            action_phase=action_phase,
            entries=entries,
            situation_standards=SITUATION_STANDARDS,
        )
        schema = ObservationBatchDedupOutput

    result = llm.with_structured_output(schema).invoke(
        [{"role": "user", "content": prompt}],
    )
    if isinstance(result, dict):
        result = schema.model_validate(result)
    return result


def call_model(
    cluster: dict,
    model: str,
    thinking_level: str | None,
    prompt_variant: str = "default",
) -> dict[str, Any]:
    entries, index_to_key = format_entries(cluster)
    result = _invoke_model(cluster, model, thinking_level, entries, index_to_key, prompt_variant=prompt_variant)
    return {"operations": _extract_ops(result, index_to_key)}


def call_model_two_pass(
    cluster: dict,
    triage_model: str,
    triage_thinking: str | None,
    verify_model: str,
    verify_thinking: str | None,
    prompt_variant: str = "default",
) -> dict[str, Any]:
    """Two-pass: triage model classifies, KEEP/DISCARD trusted, MERGE escalated."""
    entries, index_to_key = format_entries(cluster)
    key_to_index = {v: k for k, v in index_to_key.items()}

    triage_result = _invoke_model(
        cluster, triage_model, triage_thinking, entries, index_to_key,
        prompt_variant=prompt_variant,
    )

    trusted_ops = []
    merge_keys: set[str] = set()
    for op in triage_result.operations:
        real_keys = _remap_keys(op.source_keys, index_to_key)
        if op.action == "MERGE":
            merge_keys.update(real_keys)
        else:
            trusted_ops.append(op)

    escalated_count = len(merge_keys)

    if not merge_keys:
        ops = _extract_ops(triage_result, index_to_key)
        return {"operations": ops, "escalated_keys": 0, "total_keys": len(index_to_key)}

    if len(merge_keys) < 2:
        for op in triage_result.operations:
            if op.action == "MERGE":
                op.action = "KEEP"
                op.merged_situation = None
                op.survivor_key = None
                if hasattr(op, "merged_approach"):
                    op.merged_approach = None
                if hasattr(op, "merged_outcome"):
                    op.merged_outcome = None
        ops = _extract_ops(triage_result, index_to_key)
        return {"operations": ops, "escalated_keys": escalated_count, "total_keys": len(index_to_key)}

    verify_items = [
        item for item in cluster["items"] if item["key"] in merge_keys
    ]
    verify_cluster = dict(cluster, items=verify_items, size=len(verify_items))
    verify_entries, verify_index_to_key = format_entries(verify_cluster)

    verify_result = _invoke_model(
        verify_cluster, verify_model, verify_thinking,
        verify_entries, verify_index_to_key,
    )

    all_ops = (
        _extract_ops(type(triage_result)(operations=trusted_ops), index_to_key)
        + _extract_ops(verify_result, verify_index_to_key)
    )
    return {
        "operations": all_ops,
        "escalated_keys": escalated_count,
        "total_keys": len(index_to_key),
    }

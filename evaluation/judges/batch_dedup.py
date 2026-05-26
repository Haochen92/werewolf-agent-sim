"""Judge the quality of batch dedup merge/rewrite operations."""

from __future__ import annotations

import json

from Agents.llm_factory import create_chat_model

from evaluation.core.io import message_content_text, strip_json_fences
from evaluation.core.schemas import BatchDedupMergeScores
from evaluation.judges.prompts import (
    BATCH_DEDUP_MERGE_SYSTEM_PROMPT,
    BATCH_DEDUP_MERGE_USER_PROMPT,
)

DEFAULT_JUDGE_MODEL = "gemini-2.5-pro"


def _format_source_entries(
    source_items: list[dict],
    memory_kind: str,
) -> str:
    lines: list[str] = []
    for i, item in enumerate(source_items, 1):
        val = item.get("value", item)
        lines.append(f"[{i}]")
        lines.append(f"  situation: {val.get('situation', '')}")
        if memory_kind == "strategy_points":
            lines.append(f"  action: {val.get('action', '')}")
        else:
            lines.append(f"  approach: {val.get('approach', '')}")
            lines.append(f"  outcome: {val.get('outcome', '')}")
        lines.append("")
    return "\n".join(lines).strip()


def _format_merged_output(operation: dict, memory_kind: str) -> str:
    parts: list[str] = []
    if operation.get("merged_situation"):
        parts.append(f"situation: {operation['merged_situation']}")
    if memory_kind == "strategy_points":
        if operation.get("merged_action"):
            parts.append(f"action: {operation['merged_action']}")
    else:
        if operation.get("merged_approach"):
            parts.append(f"approach: {operation['merged_approach']}")
        if operation.get("merged_outcome"):
            parts.append(f"outcome: {operation['merged_outcome']}")
    if not parts:
        return "(no rewrite — survivor entry preserved as-is)"
    return "\n".join(parts)


def run_batch_merge_judge(
    source_items: list[dict],
    operation: dict,
    memory_kind: str,
    role: str,
    action_phase: str,
    model: str = DEFAULT_JUDGE_MODEL,
    max_retries: int = 1,
) -> BatchDedupMergeScores | None:
    llm = create_chat_model(model)

    prompt = BATCH_DEDUP_MERGE_USER_PROMPT.format(
        memory_kind=memory_kind,
        role=role,
        action_phase=action_phase,
        action=operation["action"],
        source_entries_formatted=_format_source_entries(source_items, memory_kind),
        merged_output_formatted=_format_merged_output(operation, memory_kind),
    )

    for attempt in range(max_retries + 1):
        try:
            response = llm.invoke(
                [
                    {"role": "system", "content": BATCH_DEDUP_MERGE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            payload = json.loads(
                strip_json_fences(message_content_text(response.content))
            )
            return BatchDedupMergeScores.model_validate(payload)
        except (json.JSONDecodeError, Exception) as exc:
            print(f"  Judge error: {exc}")
            if attempt < max_retries:
                continue
            return None

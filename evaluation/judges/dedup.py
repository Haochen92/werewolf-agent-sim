"""Judge the quality of a dedup decision."""

from __future__ import annotations

import json

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

from Agents.schemas.evaluation import DedupCase
from evaluation.core.io import message_content_text, strip_json_fences
from evaluation.core.schemas import DedupScores
from evaluation.judges.prompts import DEDUP_SYSTEM_PROMPT, DEDUP_USER_PROMPT

DEFAULT_JUDGE_MODEL = "gemini-2.5-pro"

DECISION_LABELS = {
    # Current per-extraction decisions
    "D": "DISCARD",
    "M": "MERGE",
    "K": "KEEP",
    # Legacy decisions (for evaluating older spans)
    "A": "DISCARD",
    "B": "REPLACE",
    "C": "DIFFERENTIATE",
}


def _format_new_entry(entry: dict, item_type: str) -> str:
    situation = entry.get("situation", "")
    if item_type == "observation":
        return (
            f"Situation: {situation}\n"
            f"Approach: {entry.get('approach', '')}\n"
            f"Outcome: {entry.get('outcome', '')}"
        )
    return f"Situation: {situation}\nAction: {entry.get('action', '')}"


def _format_candidates(candidates: list) -> str:
    if not candidates:
        return "(none — no similar entries above threshold)"
    lines = []
    for c in candidates:
        num = c.get("candidate_number", c.get("candidateNumber", "?"))
        key = c.get("key", "")
        sim = c.get("similarity", 0.0)
        count = c.get("observation_count", c.get("observationCount", 1))
        situation = c.get("situation", "")
        action = c.get("action") or c.get("approach", "")
        outcome = c.get("outcome", "")

        entry = (
            f"[{num}] Key: {key} (similarity={sim:.3f}, observed={count}x)\n"
            f"    Situation: {situation}\n"
        )
        if c.get("action") is not None:
            entry += f"    Action: {action}"
        else:
            entry += f"    Approach: {action}\n    Outcome: {outcome}"
        lines.append(entry)
    return "\n\n".join(lines)


def _format_decision_output(case: DedupCase) -> str:
    detail = case.decision_detail
    if not detail:
        return ""
    parts = []
    for key in (
        "merged_situation",
        "merged_action",
        "merged_approach",
        "merged_outcome",
        "improved_situation",
        "improved_action",
        # Legacy fields (for evaluating older spans)
        "distinguishing_variable",
        "existing_rewritten_situation",
        "existing_rewritten_action",
        "existing_rewritten_approach",
        "existing_rewritten_outcome",
        "new_rewritten_situation",
        "new_rewritten_action",
        "new_rewritten_approach",
        "new_rewritten_outcome",
    ):
        value = detail.get(key)
        if value:
            label = key.replace("_", " ").title()
            parts.append(f"{label}: {value}")
    if not parts:
        return ""
    return "DECISION OUTPUT:\n" + "\n".join(parts)


def run_dedup_judge(
    case: DedupCase,
    model: str = DEFAULT_JUDGE_MODEL,
    max_retries: int = 1,
) -> DedupScores | None:
    llm = ChatGoogleGenerativeAI(model=model, temperature=0.0)

    decision_label = DECISION_LABELS.get(case.decision, case.decision)
    reasoning = ""
    if case.decision_detail:
        reasoning = case.decision_detail.get("reasoning", "")

    candidates_raw = [
        c.model_dump(mode="json") if hasattr(c, "model_dump") else c
        for c in case.candidates
    ]

    prompt = DEDUP_USER_PROMPT.format(
        item_type=case.item_type,
        perspective=case.perspective,
        action_phase=case.action_phase,
        new_entry_formatted=_format_new_entry(case.new_entry, case.item_type),
        candidate_count=len(case.candidates),
        candidates_formatted=_format_candidates(candidates_raw),
        decision=f"{case.decision} ({decision_label})",
        decision_reasoning=reasoning,
        decision_output=_format_decision_output(case),
    )

    for attempt in range(max_retries + 1):
        try:
            response = llm.invoke(
                [
                    {"role": "system", "content": DEDUP_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            payload = json.loads(
                strip_json_fences(message_content_text(response.content))
            )
            return DedupScores.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            print(f"  Dedup judge returned invalid scores: {exc}")
            if attempt < max_retries:
                continue
            return None
        except Exception as exc:
            print(f"  Dedup judge call failed: {exc}")
            if attempt < max_retries:
                continue
            return None

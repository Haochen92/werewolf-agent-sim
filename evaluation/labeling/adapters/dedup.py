"""Dedup Keep/Discard labeling adapter.

Labels (new_entry, candidates) pairs as Keep or Discard for dedup
classifier training and threshold calibration.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.labeling.base import LabelingAdapter, LabelItem, VoteResult


DECISION_NORMALIZATION = {
    "D": "D", "K": "K",
    "DISCARD": "D", "KEEP": "K",
    "discard": "D", "keep": "K",
    "0": "D", "1": "K",
}


def _format_obs_candidates(candidates: list[dict]) -> str:
    if not candidates:
        return "(none)"
    lines = []
    for c in candidates:
        lines.append(
            f"[{c['candidate_number']}] Candidate: {c['candidate_number']}; "
            f"Key: {c.get('key', '')} "
            f"(similarity={c.get('similarity', 0):.3f}, "
            f"observed={c.get('observation_count', 1)}x)\n"
            f"    Situation: {c.get('situation', '')}\n"
            f"    Approach: {c.get('approach', '')}\n"
            f"    Outcome: {c.get('outcome', '')}"
        )
    return "\n\n".join(lines)


def _format_sp_candidates(candidates: list[dict]) -> str:
    if not candidates:
        return "(none)"
    lines = []
    for c in candidates:
        lines.append(
            f"[{c['candidate_number']}] Candidate: {c['candidate_number']}; "
            f"Key: {c.get('key', '')} "
            f"(similarity={c.get('similarity', 0):.3f}, "
            f"observed={c.get('observation_count', 1)}x)\n"
            f"    Action: {c.get('action', '')}\n"
            f"    Situation: {c.get('situation', '')}"
        )
    return "\n\n".join(lines)


class DedupAdapter(LabelingAdapter):
    """Adapter for dedup Keep/Discard labeling."""

    def __init__(self):
        from Agents.prompts.dedup import (
            OBSERVATION_DEDUP_PROMPT,
            STRATEGY_DEDUP_PROMPT,
        )
        from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS

        self._obs_prompt = OBSERVATION_DEDUP_PROMPT
        self._sp_prompt = STRATEGY_DEDUP_PROMPT
        self._situation_standards = SITUATION_STANDARDS
        self._epistemic_rule = EPISTEMIC_STATUS_RULE

    @property
    def label_values(self) -> list[str]:
        return ["K", "D"]

    def format_prompt(self, item: LabelItem) -> str:
        ctx = item.context
        if item.item_type == "observation":
            return self._obs_prompt.format(
                new_role=ctx["perspective"],
                new_situation=ctx["new_situation"],
                new_approach=ctx.get("new_approach", ""),
                new_outcome=ctx.get("new_outcome", ""),
                total_similar_count=ctx["n_candidates"],
                top_n=ctx["n_candidates"],
                existing_entries=ctx["formatted_candidates"],
            )
        else:
            return self._sp_prompt.format(
                situation_standards=self._situation_standards,
                epistemic_status_rule=self._epistemic_rule,
                new_role=ctx["perspective"],
                new_situation=ctx["new_situation"],
                new_action=ctx.get("new_action", ""),
                total_similar_count=ctx["n_candidates"],
                top_n=ctx["n_candidates"],
                existing_entries=ctx["formatted_candidates"],
            )

    def parse_response(self, text: str) -> str | None:
        text = text.strip().upper()
        for token in text.split():
            if token in DECISION_NORMALIZATION:
                return DECISION_NORMALIZATION[token]
        for char in text:
            if char in ("K", "D"):
                return char
        return None

    def item_key(self, item: LabelItem) -> str:
        return str(item.case_index)

    def load_items(self, candidates_path: Path) -> list[LabelItem]:
        items = []
        with open(candidates_path) as f:
            for line in f:
                record = json.loads(line)
                entry = record.get("new_entry", {})
                candidates = record.get("candidates", [])
                item_type = record.get("item_type", "observation")

                if item_type == "observation":
                    formatted = _format_obs_candidates(candidates)
                else:
                    formatted = _format_sp_candidates(candidates)

                items.append(LabelItem(
                    case_index=record["case_index"],
                    key=str(record["case_index"]),
                    item_type=item_type,
                    context={
                        "perspective": record.get("perspective", ""),
                        "new_situation": entry.get("situation", ""),
                        "new_approach": entry.get("approach", ""),
                        "new_outcome": entry.get("outcome", ""),
                        "new_action": entry.get("action", ""),
                        "n_candidates": len(candidates),
                        "formatted_candidates": formatted,
                        "situation": entry.get("situation", ""),
                    },
                    raw=record,
                ))
        return items

    def build_output_entry(self, item: LabelItem, vote: VoteResult) -> dict[str, Any]:
        return {
            "case_index": item.case_index,
            "item_type": item.item_type,
            "label": vote.label,
            "perspective": item.context.get("perspective", ""),
            "labeling": {
                "scores": vote.scores,
                "confidence": vote.confidence,
            },
        }

    def load_cases_metadata(self, candidates_path: Path) -> list[dict[str, Any]]:
        cases = []
        with open(candidates_path) as f:
            for line in f:
                record = json.loads(line)
                cases.append({
                    "case_index": record["case_index"],
                    "item_type": record.get("item_type", "observation"),
                    "perspective": record.get("perspective", ""),
                })
        return cases

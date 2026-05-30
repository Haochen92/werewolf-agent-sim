"""Reranker relevance labeling adapter.

Labels (situation_query, retrieved_memory) pairs on a 0/1/2 relevance scale
for cross-encoder reranker training.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.labeling.base import LabelingAdapter, LabelItem, VoteResult


RERANKER_LABEL_PROMPT = """\
You are labeling retrieval results for a werewolf social deduction game's episodic memory system.

A player in a specific game situation is retrieving past experiences from memory. Rate how relevant each retrieved memory is to the player's current situation.

## Current situation (the retrieval query)
{golden_situation}

## Retrieved memory
{memory_text}

## Relevance scale
- **2** = Highly relevant: The memory directly addresses the same game dynamic, information landscape, or strategic challenge. A player in the current situation would clearly benefit from recalling this.
- **1** = Partially relevant: The memory is related (similar role, similar phase, overlapping themes) but addresses a different angle, specificity level, or game phase. Useful background but not a direct match.
- **0** = Not relevant: The memory describes a fundamentally different situation. Recalling it would not help the player.

## Key factors to consider
- Does the memory address the same type of strategic challenge (e.g., analyzing voting records, navigating information-starved situations, managing role exposure)?
- Is the game phase comparable (early vs mid vs endgame)?
- Does the memory involve the same role dynamics?
- Would recalling this memory actually help the player decide what to do?

Respond with ONLY a single digit: 0, 1, or 2."""


RERANKER_MANUAL_INSTRUCTIONS = """\
You are labeling retrieval results for a werewolf social deduction game's episodic memory system.

A player in a specific game situation is retrieving past experiences from memory to inform their decision.
For each retrieved memory, rate how relevant it would be to recall in the current situation.

## Relevance Scale
- **2** (Highly relevant): Directly addresses the same game dynamic, information landscape, or strategic challenge. The player would clearly benefit from recalling this.
- **1** (Partially relevant): Related (similar role, overlapping themes, adjacent phase) but different angle or specificity. Useful background but not a direct match.
- **0** (Not relevant): Different situation entirely. Recalling it would not help.

## Key Factors
- Same type of strategic challenge? (voting record analysis, information-starved play, role exposure management)
- Comparable game phase? (early/mid/endgame)
- Same role dynamics?
- Would recalling this memory actually help the player decide what to do?

For EACH case below, read the game state and golden situation query, then rate every retrieved memory.
Respond with a JSON array per case containing objects with "key" (the 12-char prefix shown) and "relevance" (0/1/2)."""


def _format_memory_text(item: dict, mem_type: str, show_action: bool = True) -> str:
    if mem_type == "observation":
        parts = [f"Situation: {item['situation']}"]
        if item.get("approach"):
            parts.append(f"Approach: {item['approach']}")
        if item.get("outcome"):
            parts.append(f"Outcome: {item['outcome']}")
        return " | ".join(parts)
    else:
        if show_action and item.get("action"):
            return f"Situation: {item['situation']} | Action: {item['action']}"
        return f"Situation: {item['situation']}"


class RerankerAdapter(LabelingAdapter):
    """Adapter for reranker cross-encoder relevance labeling (0/1/2 scale).

    ``show_action`` controls whether strategy-point candidates expose the action
    field (default True = production labeling format). Setting it False shows the
    situation only — used by the SP label-drift diagnostic to isolate how much
    the action text moves labels. ``sp_only`` skips observation candidates.
    """

    def __init__(self, show_action: bool = True, sp_only: bool = False):
        self.show_action = show_action
        self.sp_only = sp_only

    @property
    def label_values(self) -> list[int]:
        return [0, 1, 2]

    def format_prompt(self, item: LabelItem) -> str:
        return RERANKER_LABEL_PROMPT.format(
            golden_situation=item.context["golden_situation"],
            memory_text=item.context["memory_text"],
        )

    def parse_response(self, text: str) -> int | None:
        for char in text:
            if char in "012":
                return int(char)
        return None

    def item_key(self, item: LabelItem) -> str:
        return f"{item.case_index}:{item.key}"

    def load_items(self, candidates_path: Path) -> list[LabelItem]:
        with open(candidates_path) as f:
            data = json.load(f)

        items = []
        for case in data["cases"]:
            query = "\n".join(case["golden_situations"])

            for obs in case["retrieved_observations"]:
                items.append(LabelItem(
                    case_index=case["case_index"],
                    key=obs["key"],
                    item_type="observation",
                    context={
                        "golden_situation": query,
                        "memory_text": _format_memory_text(obs, "observation"),
                        "situation": obs["situation"],
                    },
                    raw=obs,
                ))

            for sp in case["retrieved_strategy_points"]:
                items.append(LabelItem(
                    case_index=case["case_index"],
                    key=sp["key"],
                    item_type="strategy_point",
                    context={
                        "golden_situation": query,
                        "memory_text": _format_memory_text(sp, "strategy_point"),
                        "situation": sp["situation"],
                    },
                    raw=sp,
                ))

        return items

    def build_output_entry(self, item: LabelItem, vote: VoteResult) -> dict[str, Any]:
        entry = {
            "case_index": item.case_index,
            "key": item.key,
            "item_type": item.item_type,
            "relevance": vote.label,
            "score": item.raw.get("score"),
            "situation": item.context.get("situation", ""),
            "labeling": {
                "scores": vote.scores,
                "confidence": vote.confidence,
            },
        }
        if item.item_type == "observation":
            entry["approach"] = item.raw.get("approach", "")
            entry["outcome"] = item.raw.get("outcome", "")
        else:
            entry["action"] = item.raw.get("action", "")
        return entry

    def format_for_manual(self, item: LabelItem, game_state: str | None = None) -> str:
        lines = [
            f"### Memory [{item.key[:12]}] ({item.item_type}) "
            f"(score: {item.raw.get('score', 0):.4f})"
        ]
        lines.append(f"**Situation:** {item.context.get('situation', '')}")
        if item.item_type == "observation":
            if item.raw.get("approach"):
                lines.append(f"**Approach:** {item.raw['approach']}")
            if item.raw.get("outcome"):
                lines.append(f"**Outcome:** {item.raw['outcome']}")
        else:
            if item.raw.get("action"):
                lines.append(f"**Action:** {item.raw['action']}")
        return "\n".join(lines)

"""Context-augmented relevance labeling adapter.

Subclasses :class:`RerankerAdapter` to run the SAME 0/1/2 relevance labeling, but
with the full game state injected into the prompt. The only difference from the
query-only reranker prompt is one added ``## Full game state`` block — everything
else (intro, situation, memory, scale, response instruction) is byte-identical, so
the label delta vs. the stored query-only labels isolates the effect of seeing
context.

Used by the context-drift diagnostic (does giving the auto panel full context move
its labels?) and, later, as the basis for context-based golden labeling. The
candidate-pool file format is identical to the reranker's; the only extra input is
the eval dataset, needed to render game state per case.
"""
from __future__ import annotations

import json
from pathlib import Path

from Agents.prompts.formatters import (
    format_day_channel_for_day,
    format_day_summaries,
    format_investigator_results,
    format_wolf_channel,
)
from Agents.schemas.evaluation import EvalCase
from evaluation.labeling.adapters.reranker import (
    RERANKER_LABEL_PROMPT,
    RerankerAdapter,
)
from evaluation.labeling.base import LabelItem


# RERANKER_LABEL_PROMPT, with one extra block inserted before the situation. The
# intro line, situation header, memory, scale, and response instruction are reused
# verbatim from RERANKER_LABEL_PROMPT so the only delta is the game-state context.
_CONTEXT_BLOCK = """\
## Full game state (what the player actually faces right now)
{game_state}

## Current situation (the retrieval query)"""

CONTEXT_LABEL_PROMPT = RERANKER_LABEL_PROMPT.replace(
    "## Current situation (the retrieval query)", _CONTEXT_BLOCK, 1
)


def render_game_state(case: EvalCase) -> str:
    """Render the raw game facts a player faces.

    Deliberately omits the situation-summary *authoring* guidance (the shared
    SITUATION_STANDARDS and role lens that the labeler's ``format_game_state``
    appends): those instruct *how to write a summary* and would reframe a
    relevance-labeling task. We want relevance judged against the facts.
    """
    private = case.private_context
    role = case.player_role

    lines: list[str] = []
    lines.append(f"{role} | day {case.day} round {case.round} | {case.action_phase}")
    lines.append("")

    if role == "wolf":
        lines.append(f"Surviving villagers: {', '.join(private.surviving_villagers)}")
        lines.append(
            f"Known surviving wolf allies: {', '.join(private.surviving_wolves)}"
        )
    else:
        lines.append(f"Surviving players: {', '.join(private.surviving_players)}")
    lines.append("")

    lines.append("--- Previous days summary ---")
    lines.append(format_day_summaries(private.day_summaries, before_day=case.day))
    lines.append("")

    lines.append("--- Today's public discussion ---")
    lines.append(format_day_channel_for_day(case.visible_discussion, case.day))
    lines.append("")

    if role == "wolf":
        lines.append("--- Wolf night chat ---")
        lines.append(format_wolf_channel(private.wolf_channel))
        lines.append("")

    if role == "investigator":
        lines.append("--- Your private investigation results ---")
        lines.append(format_investigator_results(private.investigator_results))
        lines.append("")

    lines.append("--- This player's standing strategy note ---")
    lines.append(private.previous_strategy or "(none)")

    return "\n".join(lines)


class ContextRerankerAdapter(RerankerAdapter):
    """Reranker relevance labeling with full game state added to the prompt.

    Args:
        eval_dataset_path: JSONL holding full game state. Candidate
            ``case_index`` values index into this dataset (verified via ``case_id``).
        show_action / sp_only: inherited from RerankerAdapter.
    """

    def __init__(self, eval_dataset_path: Path, show_action: bool = True,
                 sp_only: bool = False):
        super().__init__(show_action=show_action, sp_only=sp_only)
        self._eval_dataset_path = Path(eval_dataset_path)
        self._game_state_cache: dict[int, str] = {}
        self._records = None

    def _game_state_for(self, case_index: int, case_id: str) -> str:
        if case_index not in self._game_state_cache:
            if self._records is None:
                from evaluation.data.datasets import read_eval_dataset

                self._records = read_eval_dataset(self._eval_dataset_path)
            rec = self._records[case_index]
            if rec.case_id != case_id:
                raise ValueError(
                    f"case_index {case_index} -> case_id {rec.case_id!r} in "
                    f"{self._eval_dataset_path.name}, but candidates say {case_id!r}. "
                    "Dataset/candidates misaligned."
                )
            self._game_state_cache[case_index] = render_game_state(rec.eval_case)
        return self._game_state_cache[case_index]

    def format_prompt(self, item: LabelItem) -> str:
        return CONTEXT_LABEL_PROMPT.format(
            game_state=item.context["game_state"],
            golden_situation=item.context["golden_situation"],
            memory_text=item.context["memory_text"],
        )

    def load_items(self, candidates_path: Path) -> list[LabelItem]:
        # Reuse the parent's loading (same pool, same memory formatting / sp_only),
        # then attach the rendered game state to each item's context.
        with open(candidates_path) as f:
            case_ids = {c["case_index"]: c["case_id"] for c in json.load(f)["cases"]}

        items = super().load_items(candidates_path)
        for item in items:
            item.context["game_state"] = self._game_state_for(
                item.case_index, case_ids[item.case_index]
            )
        return items

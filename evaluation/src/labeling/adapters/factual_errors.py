"""Factual-error owner check: does one generated statement contradict what its judge was given?

The hallucination bench scores every statement with one of two judges: the expectation judge
(``judges/golden_expectation``, for cases with a hand-written expectation) or the census reader
(``judges/role_fact_read``, against a fact sheet built from the game record). This adapter shows a
person the statement and exactly the judge's input, never the judge's verdict or reason, and asks
``error`` or ``no_error``. Its model prompt IS the judge's own prompt, so a model labelling these
items is held to the same rubric as the person's guide and the judge.

The candidates file (JSONL of ``JudgedStatement``) is written by
``evaluation/experiments/owner_check_factual_errors.py``; it never holds the verdict.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from evaluation.src.labeling.base import LabelingAdapter, LabelItem, VoteResult

EXPECTATION_JUDGE = "expectation_judge"
CENSUS_READER = "census_reader"

ERROR_LABEL = "error"
NO_ERROR_LABEL = "no_error"

EXPECTATION_JUDGE_LABEL_BY_VERDICT = {
    "violates": ERROR_LABEL,
    "meets": NO_ERROR_LABEL,
    # The bench counts a sample bad only on "violates", so "unclear" is not an error there either.
    "unclear": NO_ERROR_LABEL,
}
"""The expectation judge's verdict mapped to the owner's label (the bench stores it with a
``golden_`` prefix, e.g. ``golden_violates``)."""

CENSUS_READER_LABEL_BY_VERDICT = {
    "hallucination": ERROR_LABEL,
    "consistent": NO_ERROR_LABEL,
    # Neither is counted bad by the bench: "ambiguous" is undecidable, and a deliberate lie about
    # the speaker's own private knowledge is part of the game, counted separately.
    "ambiguous": NO_ERROR_LABEL,
    "deliberate_deception": NO_ERROR_LABEL,
}
"""The census reader's verdict mapped to the owner's label."""


class JudgedStatement(BaseModel):
    """One statement a bench judge read, with exactly the input the judge was given (no verdict)."""

    key: str
    """Unique across the whole corpus, e.g. ``"shared_prefix_luna_2026_10_13:e04:83300b19:luna_today:s0:u1"``
    (run, game, case, arm, sample, unit)."""
    case_index: int
    """The bench case's number in this packet (1-based); items of one case share it."""
    run_label: str
    """The bench run directory the verdict came from, e.g. ``"shared_prefix_luna_2026_10_13"``."""
    game_id: str
    case_id: str
    arm: str
    sample: int
    unit_index: int
    """Position of the statement among the sample's units (message, private note, reads)."""
    unit_kind: str
    """The output field the statement came from: ``"message"``, ``"updated_strategy"`` or ``"reads"``."""
    judge_unit_name: str
    """What the judge was told the statement is: ``"public chat message"`` or ``"private strategy note"``."""
    judge_kind: Literal["expectation_judge", "census_reader"]
    statement_text: str
    expectation: str | None = None
    """The written expectation the expectation judge compared against; None for the census reader."""
    fact_sheet: dict[str, Any] | None = None
    """The census reader's prompt fields (``role_fact_read.build_fact_sheet`` output); None for the
    expectation judge."""


def judge_unit_name(unit_kind: str) -> str:
    """Return the name both judges give a statement of this kind in their prompt.

    Args:
        unit_kind: the output field, e.g. ``"updated_strategy"`` or ``"reads"``.

    Returns:
        ``"private strategy note"`` for ``updated_strategy``; ``"public chat message"`` for
        anything else (the judges name a ``reads`` unit that way too).
    """
    if unit_kind == "updated_strategy":
        return "private strategy note"
    return "public chat message"


def label_for_verdict(judge_kind: str, verdict: str) -> str | None:
    """Return the owner-scale label (``error`` / ``no_error``) for one judge verdict.

    Args:
        judge_kind: ``"expectation_judge"`` or ``"census_reader"``.
        verdict: the judge's verdict word, with or without the bench's ``golden_`` prefix,
            e.g. ``"golden_violates"``, ``"meets"``, ``"hallucination"``.

    Returns:
        The label, or None when the verdict is not one that judge gives (e.g. ``"no_anchor"``:
        the statement was never read, or ``"read_error"``).
    """
    verdict_word = verdict.removeprefix("golden_")
    if judge_kind == EXPECTATION_JUDGE:
        return EXPECTATION_JUDGE_LABEL_BY_VERDICT.get(verdict_word)
    return CENSUS_READER_LABEL_BY_VERDICT.get(verdict_word)


def judge_user_prompt(statement: JudgedStatement) -> str:
    """Return the user message the statement's judge was sent, rebuilt from its own template.

    Args:
        statement: the judged statement, carrying its expectation or fact sheet.

    Returns:
        The filled-in template of ``golden_expectation`` or ``role_fact_read``.
    """
    if statement.judge_kind == EXPECTATION_JUDGE:
        from evaluation.src.judges.golden_expectation import USER_TEMPLATE

        return USER_TEMPLATE.format(
            golden=statement.expectation,
            unit=statement.judge_unit_name,
            text=statement.statement_text,
        )
    from evaluation.src.judges.role_fact_read import USER_TEMPLATE

    return USER_TEMPLATE.format(**statement.fact_sheet)


class FactualErrorAdapter(LabelingAdapter):
    """Owner check of the factual-error judges: ``error`` / ``no_error`` per judged statement."""

    @property
    def label_values(self) -> list[str]:
        """Return the two labels, error first (the positive label)."""
        return [ERROR_LABEL, NO_ERROR_LABEL]

    @property
    def manual_response_field(self) -> str:
        """Return the field the owner fills in per item in a batch's response block."""
        return "error_label"

    def format_prompt(self, item: LabelItem) -> str:
        """Return the prompt the item's judge was given: its system rules, then its user message.

        Laid out as the expectation judge's Message Batch sends it (system text, a blank line, the
        user message). Using the judges' own prompts is the rubric parity: the owner's guide
        restates these rules in plain words.

        Args:
            item: an item from ``load_items``.

        Returns:
            The full prompt text.
        """
        statement: JudgedStatement = item.raw["statement"]
        if statement.judge_kind == EXPECTATION_JUDGE:
            from evaluation.src.judges.golden_expectation import SYSTEM
        else:
            from evaluation.src.judges.role_fact_read import SYSTEM
        return SYSTEM + "\n\n" + judge_user_prompt(statement)

    def response_schema(self, item: LabelItem) -> type:
        """Return the judge's own structured-output schema for the item.

        Args:
            item: an item from ``load_items``.

        Returns:
            ``GoldenVerdict`` for the expectation judge, ``RoleFactVerdict`` for the census reader.
        """
        if item.item_type == EXPECTATION_JUDGE:
            from evaluation.src.judges.golden_expectation import GoldenVerdict

            return GoldenVerdict
        from evaluation.src.judges.role_fact_read import RoleFactVerdict

        return RoleFactVerdict

    def parse_structured(self, item: LabelItem, result: Any) -> tuple[str | None, dict[str, Any]]:
        """Map a structured verdict to the owner's label.

        Args:
            item: the item judged.
            result: a ``GoldenVerdict`` / ``RoleFactVerdict``, or its dict.

        Returns:
            ``(label, detail)``: the label (None for an unknown verdict) and the verdict's fields
            as audit detail.
        """
        if isinstance(result, dict):
            result = self.response_schema(item).model_validate(result)
        verdict_detail = result.model_dump(mode="json")
        return label_for_verdict(item.item_type, result.verdict), verdict_detail

    def parse_response(self, text: str) -> str | None:
        """Read a label from free text: a JSON object's ``verdict``, or the first verdict word.

        Accepts either judge's verdict words (``violates``, ``hallucination``, ...) and the owner's
        own labels (``error`` / ``no_error``).

        Args:
            text: the model's reply, e.g. ``'{"quote": "...", "reason": "...", "verdict": "meets"}'``.

        Returns:
            ``"error"`` or ``"no_error"``, or None if no known verdict is found.
        """
        try:
            reply = json.loads(text)
        except json.JSONDecodeError:
            reply = None
        if isinstance(reply, dict) and isinstance(reply.get("verdict"), str):
            words = [reply["verdict"].strip().lower()]
        else:
            words = text.replace('"', " ").replace(",", " ").lower().split()

        for word in words:
            if word in (ERROR_LABEL, NO_ERROR_LABEL):
                return word
            if word in EXPECTATION_JUDGE_LABEL_BY_VERDICT:
                return EXPECTATION_JUDGE_LABEL_BY_VERDICT[word]
            if word in CENSUS_READER_LABEL_BY_VERDICT:
                return CENSUS_READER_LABEL_BY_VERDICT[word]
        return None

    def item_key(self, item: LabelItem) -> str:
        """Return the item's corpus-wide key."""
        return item.key

    def load_items(self, candidates_path: Path) -> list[LabelItem]:
        """Read the candidates file into label items, in file order.

        Args:
            candidates_path: JSONL, one ``JudgedStatement`` per line.

        Returns:
            One item per statement; ``item_type`` is the judge kind and ``raw["statement"]`` the
            validated record. Raises ValueError if a key repeats.
        """
        items: list[LabelItem] = []
        seen_keys: set[str] = set()
        for line in Path(candidates_path).read_text().splitlines():
            if not line.strip():
                continue
            statement = JudgedStatement.model_validate_json(line)
            if statement.key in seen_keys:
                raise ValueError(f"Key {statement.key!r} appears twice in {candidates_path}")
            seen_keys.add(statement.key)
            items.append(LabelItem(
                case_index=statement.case_index,
                key=statement.key,
                item_type=statement.judge_kind,
                context={"unit_kind": statement.unit_kind, "game_id": statement.game_id},
                raw={"statement": statement},
            ))
        return items

    def load_cases_metadata(self, candidates_path: Path) -> list[dict[str, Any]]:
        """Return one metadata row per bench case in the candidates file.

        Args:
            candidates_path: the JSONL candidates file.

        Returns:
            Rows like ``{"case_index": 3, "game_id": "e04", "case_id": "...", "judge_kind": "..."}``,
            sorted by case index.
        """
        metadata_by_case: dict[int, dict[str, Any]] = {}
        for item in self.load_items(candidates_path):
            statement: JudgedStatement = item.raw["statement"]
            metadata_by_case.setdefault(statement.case_index, {
                "case_index": statement.case_index,
                "game_id": statement.game_id,
                "case_id": statement.case_id,
                "judge_kind": statement.judge_kind,
            })
        return [metadata_by_case[case_index] for case_index in sorted(metadata_by_case)]

    def build_output_entry(self, item: LabelItem, vote: VoteResult) -> dict[str, Any]:
        """Return one merged-results row for the item.

        Args:
            item: the item labelled.
            vote: the voting outcome across labellers.

        Returns:
            ``{"case_index", "key", "item_type", "label", "labeling": {"scores", "confidence"}}``.
        """
        return {
            "case_index": item.case_index,
            "key": item.key,
            "item_type": item.item_type,
            "label": vote.label,
            "labeling": {"scores": vote.scores, "confidence": vote.confidence},
        }

    def format_for_manual(self, item: LabelItem, game_state: str | None = None) -> str:
        """Render one item for the owner: the statement and the judge's input, never its verdict.

        Args:
            item: an item from ``load_items``.
            game_state: unused (the judge saw no game state beyond its input).

        Returns:
            Markdown: the full key, the expectation (or the census reader's whole user message,
            fact sheet included), and the statement.
        """
        statement: JudgedStatement = item.raw["statement"]
        lines = [f"### Item `{statement.key}`", ""]
        source_note = ""
        if statement.unit_kind == "reads":
            source_note = " (it is the player's private reads of the table; judge it as written)"
        lines.append(f"**Statement kind, as the judge was told:** {statement.judge_unit_name}{source_note}")
        lines.append("")

        if statement.judge_kind == EXPECTATION_JUDGE:
            lines.append("**The expectation** (what the judge compared the statement against):")
            lines.append("")
            lines.append(_blockquote(statement.expectation or ""))
            lines.append("")
            lines.append("**The statement:**")
            lines.append("")
            lines.append(_blockquote(statement.statement_text))
        else:
            lines.append("**The facts and the statement, exactly as the census reader received them:**")
            lines.append("")
            lines.append("```text")
            lines.append(judge_user_prompt(statement))
            lines.append("```")
        return "\n".join(lines)


def _blockquote(text: str) -> str:
    """Return the text as a markdown blockquote, keeping its line breaks.

    Args:
        text: any text, possibly multi-line.

    Returns:
        Each line prefixed with ``> `` (empty lines with ``>``).
    """
    quoted_lines = []
    for line in text.splitlines() or [""]:
        quoted_lines.append(f"> {line}" if line else ">")
    return "\n".join(quoted_lines)

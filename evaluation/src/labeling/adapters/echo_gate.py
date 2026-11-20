"""Echo-gate owner check: label one open-floor line as a new fact, a new reading, a question that
moves the game, or a restatement / filler (kinds A–D).

The items are the 65 open-floor lines the silence calibration's blind readers judged and the shipped
echo gate was checked on (evidence/gameplay/data/silence_calibration/). The builder
(`evaluation/experiments/owner_check_echo_gate.py`) writes the candidates file this adapter reads;
the file holds only what the readers saw, so no rendering here can show a reader's kind or the
gate's decision.

The rubric is the readers' own wording (their brief of 2026-10-18), used both for the owner's
export and for ``format_prompt``, so a model could later label the same items on the same terms.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from evaluation.src.labeling.base import LabelingAdapter, LabelItem, VoteResult

KIND_LABELS = ["A", "B", "C", "D"]
"""The four kinds, in the readers' order."""

ITEM_TYPE = "open_floor_line"
"""The one item type of this task."""

KIND_RUBRIC = """Judge only THE LINE, against what the table already had (the earlier days and today's discussion shown):
- "A": it adds a new fact: a role claim or counterclaim, or the speaker's own night action or result that the table has not heard yet.
- "B": it adds a new inference, or a different reading of facts already known: a reason, a consequence, or a point of view nobody has put today.
- "C": it asks a pointed question or proposes a test that would move the game (who to check, what someone must explain), and that ask was not already made today.
- "D": it restates what was already said, agrees without a new reason, asks again for what was already asked, or is filler ("nothing to go on yet", "let's hear claims").
If a line does several things, pick the most valuable kind it really delivers. Judge newness strictly against the context shown: a fact or point already on the table is D, however well put.
Whether the line is true or a good move for the speaker's side does not matter."""
"""The readers' kind definitions, word for word from their brief (the "worth_hearing" question left
out: the owner labels the kind only)."""


class OpenFloorLine(BaseModel):
    """One open-floor line as the readers saw it: the candidates file holds one per item."""

    case_index: int
    """The item's position in the readers' shuffled order (the number in its reader name, ``s012`` → 12)."""
    key: str
    """The turn id, unique across games: ``<game>:<day>:<player>:<turn on that day>``,
    e.g. ``"voices-02.off:4:player_10:2"``."""
    reader_item: str
    """The name the readers saw for this item, e.g. ``"s012"``."""
    speaker: str
    """The seat that wrote the line, e.g. ``"player_10"``."""
    stage: str
    """The stage line the readers saw, e.g. ``"the day's discussion"``."""
    earlier_days: str
    """The most recent part of the earlier days' summary, as the seat saw it."""
    today: str
    """Today's discussion before the line, as the seat saw it."""
    line: str
    """THE LINE being labelled."""


def render_reader_view(line_record: OpenFloorLine) -> str:
    """Return the text of one item exactly as the readers' packet showed it, below its ``###`` heading.

    Args:
        line_record: the open-floor line and its context.

    Returns:
        The speaker line, the earlier days, today's discussion and THE LINE, in the packet's layout.
    """
    return (
        f"Speaker: {line_record.speaker}, during {line_record.stage}.\n\n"
        f"Earlier days (summary, most recent part):\n{line_record.earlier_days}\n\n"
        f"Today's discussion so far, as the speaker saw it:\n{line_record.today}\n\n"
        f"THE LINE:\n{line_record.line}\n"
    )


class EchoGateAdapter(LabelingAdapter):
    """Adapter for labelling open-floor lines with the readers' kinds A–D."""

    @property
    def label_values(self) -> list[str]:
        """Return the allowed labels.

        Returns:
            ``["A", "B", "C", "D"]``.
        """
        return KIND_LABELS

    @property
    def manual_response_field(self) -> str:
        """Return the field the owner fills in per item of the export.

        Returns:
            ``"kind"``.
        """
        return "kind"

    def format_prompt(self, item: LabelItem) -> str:
        """Return a labelling prompt for one line, with the same rubric the readers and the owner have.

        Args:
            item: an item from ``load_items``.

        Returns:
            The prompt text, asking for a JSON object with the kind and a short note.
        """
        line_record = OpenFloorLine(**item.raw)
        return (
            "You are a blind judge for a study of a Werewolf game played by AI players. The item below "
            "shows a speaker, the stage of the day, a summary of earlier days, today's discussion as the "
            "speaker saw it, and THE LINE the speaker would say now.\n\n"
            f"{KIND_RUBRIC}\n\n"
            f"### {line_record.reader_item}\n{render_reader_view(line_record)}\n"
            'Answer with one JSON object: {"kind": "A" | "B" | "C" | "D", '
            '"note": "one short phrase: what is new, or what it repeats"}'
        )

    def parse_response(self, text: str) -> str | None:
        """Return the kind a model gave, read from its JSON answer or, failing that, a lone letter.

        Args:
            text: the model's reply, e.g. ``'{"kind": "B", "note": "new reading of the vote"}'``.

        Returns:
            One of ``"A"``–``"D"``, or None when no kind can be found.
        """
        json_kind = re.search(r'"kind"\s*:\s*"([ABCD])"', text)
        if json_kind:
            return json_kind.group(1)
        lone_letter = re.search(r"\b([ABCD])\b", text.strip().upper())
        if lone_letter:
            return lone_letter.group(1)
        return None

    def item_key(self, item: LabelItem) -> str:
        """Return the item's key, the turn id.

        Args:
            item: an item from ``load_items``.

        Returns:
            e.g. ``"voices-02.off:4:player_10:2"``.
        """
        return item.key

    def load_items(self, candidates_path: Path) -> list[LabelItem]:
        """Read the candidates file the builder writes.

        Args:
            candidates_path: a JSON file ``{"description": "...", "cases": [<OpenFloorLine>, ...]}``.

        Returns:
            One item per line, in the file's order. Raises pydantic.ValidationError if a record
            lacks a field.
        """
        candidates = json.loads(Path(candidates_path).read_text())
        items: list[LabelItem] = []
        for record in candidates["cases"]:
            line_record = OpenFloorLine(**record)
            items.append(
                LabelItem(
                    case_index=line_record.case_index,
                    key=line_record.key,
                    item_type=ITEM_TYPE,
                    context={"speaker": line_record.speaker, "line": line_record.line},
                    raw=line_record.model_dump(),
                )
            )
        return items

    def build_output_entry(self, item: LabelItem, vote: VoteResult) -> dict[str, Any]:
        """Return one merged-output entry for a labelled line.

        Args:
            item: the labelled item.
            vote: the vote across labellers.

        Returns:
            The entry: case index, key, item type, label, and the scores and confidence behind it.
        """
        return {
            "case_index": item.case_index,
            "key": item.key,
            "item_type": item.item_type,
            "label": vote.label,
            "labeling": {"scores": vote.scores, "confidence": vote.confidence},
        }

    def format_for_manual(self, item: LabelItem, game_state: str | None = None) -> str:
        """Return one item for the owner's export: the readers' view of the line and nothing else.

        Args:
            item: an item from ``load_items``.
            game_state: unused; part of the base signature.

        Returns:
            Markdown with the reader name and key as a heading, then the packet text.
        """
        line_record = OpenFloorLine(**item.raw)
        return f"### {line_record.reader_item} (key `{line_record.key}`)\n\n{render_reader_view(line_record)}"

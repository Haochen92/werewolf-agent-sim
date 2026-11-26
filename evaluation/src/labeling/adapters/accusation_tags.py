"""Accusation-tag labelling adapter: whom, if anyone, one day-discussion message accuses.

Each speaker tags its own message with the players it addresses and a stance per player
(``Agents/schemas/game_events.py::AddressedTarget``). The accusation tags pick who gets a closing
defence and open reply obligations, so this task checks them against a person: the label is
``"none"`` or the accused player ids in seat order, comma-joined (``"player_2,player_10"``).

The candidates file (written by ``evaluation/experiments/owner_check_accusation_tags.py``) holds the
message and what the table had heard before it, and never the speaker's tags: the export is blind
by construction. The owner's guide and ``format_prompt`` share ``ACCUSATION_RUBRIC``, so a model
could later label the same items on the same rubric.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from evaluation.src.labeling.base import LabelingAdapter, LabelItem, VoteResult

NO_ACCUSATION = "none"
"""The label of a message that accuses no one."""

PLAYER_ID_PATTERN = re.compile(r"player_(\d+)")

# Built from the stance definitions the speaker was given (AddressedTarget.stance's description),
# so the owner and any model labeller decide on the same words as the speaker did. No example names
# a seat: a model labeller tends to pick a seat an example names.
ACCUSATION_RUBRIC = """\
A message ACCUSES a player when it suspects or blames that player of being evil or of lying.
- Suspicion counts even when hedged ("they are my top suspect, though I'm not certain").
- Saying a player's claim or report is false counts: that blames them of lying.
- It does NOT accuse a player it defends or supports, agrees with, or mentions with no clear
  stance. Passing commentary, such as noting that someone has been quiet, is not an accusation.
- A question accuses only when it plainly casts suspicion; a plain request for information does not.
Judge this message only, reading it in the light of the lines before it: a player it accused
earlier, but not in this message, is not accused here. Dead players can be accused too.

The label is `none`, or the ids of every accused player in seat order (lowest seat number
first), comma-joined with no spaces."""


class ContextLine(BaseModel):
    """One line the table had heard before the labelled message."""

    speaker: str
    """``"game_master"`` for the moderator, else the player id, e.g. ``"player_8"``."""
    text: str
    """What was said, as the table heard it."""


class AccusationCandidate(BaseModel):
    """One spoken agent message to label, with what was heard before it (never its tags)."""

    key: str
    """Unique across the corpus: game, day and transcript position, e.g. ``"f01:d2:s15"``."""
    case_index: int
    """The item's position in the candidates file (one export case per message)."""
    game: str
    """The game's record name, e.g. ``"f01"`` for ``f01.record.json``."""
    day: int
    seq: int
    """The message's position in the day's transcript."""
    day_round: str
    """``opening`` (every living player at once), ``discussion``, ``proactive`` or ``closing``."""
    speaker: str
    """The speaking player's id."""
    message: str
    since_last_discussion: list[ContextLine]
    """The moderator lines that closed the previous day: its vote result and the night that
    followed. Empty on day 1."""
    earlier_today: list[ContextLine]
    """Today's heard lines before this message, in order. For an opening-round message this holds
    no other opening line, since the opening is spoken all at once."""


def accused_label_from_players(accused_players: list[str]) -> str:
    """Return the label for a set of accused players: ``"none"`` or the ids in seat order.

    Args:
        accused_players: player ids, any order, repeats allowed, e.g. ``["player_10", "player_2"]``.

    Returns:
        ``"none"`` for an empty list, else the distinct ids sorted by seat number and joined by
        commas, e.g. ``"player_2,player_10"``. Raises ValueError for an id that is not ``player_<n>``.
    """
    seat_number_by_player: dict[str, int] = {}
    for player in accused_players:
        id_match = PLAYER_ID_PATTERN.fullmatch(player)
        if id_match is None:
            raise ValueError(f"Not a player id: {player!r}")
        seat_number_by_player[player] = int(id_match.group(1))

    if not seat_number_by_player:
        return NO_ACCUSATION
    players_in_seat_order = sorted(seat_number_by_player, key=seat_number_by_player.get)
    return ",".join(players_in_seat_order)


def canonical_accused_label(raw_label: str) -> str:
    """Return a loosely written label in its canonical form.

    Accepts any case, spaces, and ids in any order: ``" Player_10, player_2 "`` becomes
    ``"player_2,player_10"`` and ``"NONE"`` becomes ``"none"``.

    Args:
        raw_label: the label as written, e.g. ``"player_7, player_3"`` or ``"none"``.

    Returns:
        The canonical label. Raises ValueError when the text is neither ``none`` nor a comma
        list of player ids (e.g. ``"p3"``, ``""``, or ``"none,player_3"``).
    """
    label_text = raw_label.strip().lower()
    if label_text == NO_ACCUSATION:
        return NO_ACCUSATION

    accused_players: list[str] = []
    for part in label_text.split(","):
        player = part.strip()
        if PLAYER_ID_PATTERN.fullmatch(player) is None:
            raise ValueError(
                f"Label {raw_label!r}: {player!r} is not a player id; write `none` or ids like "
                "`player_3,player_10`"
            )
        accused_players.append(player)
    return accused_label_from_players(accused_players)


def read_candidates(candidates_path: Path) -> list[AccusationCandidate]:
    """Read the candidates file the owner-check builder writes.

    Args:
        candidates_path: a JSON file ``{"candidates": [<AccusationCandidate fields>, ...]}``.

    Returns:
        The candidates in file order. Raises pydantic.ValidationError on a malformed record.
    """
    file_content = json.loads(Path(candidates_path).read_text())
    candidates: list[AccusationCandidate] = []
    for candidate_record in file_content["candidates"]:
        candidates.append(AccusationCandidate.model_validate(candidate_record))
    return candidates


def _context_bullet(line: ContextLine) -> str:
    """Return one context line as a markdown bullet, ``- **player_8:** text``.

    Args:
        line: the speaker and text.

    Returns:
        The bullet, with any further lines of a multi-line text (a vote result) indented so they
        stay inside it.
    """
    indented_text = line.text.strip().replace("\n", "\n  ")
    return f"- **{line.speaker}:** {indented_text}"


def render_transcript(candidate: AccusationCandidate) -> str:
    """Return the markdown a labeller reads for one message: what was heard before it, then it.

    The same rendering serves the owner (``format_for_manual``) and a model (``format_prompt``).

    Args:
        candidate: the message and its context.

    Returns:
        Markdown with the previous day's closing moderator lines, today's earlier lines and the
        message itself, each line prefixed by its speaker.
    """
    sections = [f"Game {candidate.game}, day {candidate.day}."]

    if candidate.since_last_discussion:
        sections.append("**Since the last discussion:**")
        for line in candidate.since_last_discussion:
            sections.append(_context_bullet(line))

    if candidate.day_round == "opening":
        sections.append(
            f"*Opening round: every player speaks at once, so {candidate.speaker} had heard no "
            "other line today.*"
        )
    elif candidate.earlier_today:
        sections.append("**Today, before this message:**")
        for line in candidate.earlier_today:
            sections.append(_context_bullet(line))
    else:
        sections.append("*No line was heard today before this message.*")

    sections.append(f"**The message — {candidate.speaker} ({candidate.day_round} round):**")
    sections.append("> " + candidate.message.strip().replace("\n", "\n> "))
    return "\n\n".join(sections)


class AccusationTagsAdapter(LabelingAdapter):
    """Adapter for labelling whom each day-discussion message accuses."""

    @property
    def label_values(self) -> list[str]:
        """Return the one fixed label, ``["none"]``.

        Every other label is a comma-joined list of player ids, so the label space is open and
        the calibration config's ``allowed_labels`` stays None.
        """
        return [NO_ACCUSATION]

    @property
    def manual_response_field(self) -> str:
        """Return ``"accused"``, the field the owner fills in for each exported message."""
        return "accused"

    def format_prompt(self, item: LabelItem) -> str:
        """Return the model prompt for one message, on the owner's rubric.

        Args:
            item: a loaded item; ``item.raw`` holds the ``AccusationCandidate`` fields.

        Returns:
            The rubric, the transcript and a one-line answer instruction that ``parse_response``
            reads.
        """
        candidate = AccusationCandidate.model_validate(item.raw)
        return (
            "You are labelling a message from a game of Werewolf.\n\n"
            f"{ACCUSATION_RUBRIC}\n\n---\n\n{render_transcript(candidate)}\n\n---\n\n"
            f"Whom does {candidate.speaker}'s message accuse? Reply with one final line, either "
            "`accused: none` or `accused: ` followed by the accused ids in seat order, comma-joined."
        )

    def parse_response(self, text: str) -> str | None:
        """Return the canonical label from a model reply, or None when it cannot be read.

        Args:
            text: the model's reply; its last line starting ``accused:`` is read.

        Returns:
            The label in canonical form, e.g. ``"player_2,player_10"`` or ``"none"``; None when no
            ``accused:`` line is found or its value is not a valid label.
        """
        answer_value = None
        for reply_line in text.splitlines():
            cleaned_line = reply_line.strip().strip("`*").strip()
            if cleaned_line.lower().startswith("accused:"):
                answer_value = cleaned_line[len("accused:"):].strip().strip("`.").strip()
        if answer_value is None:
            return None
        try:
            return canonical_accused_label(answer_value)
        except ValueError:
            return None

    def item_key(self, item: LabelItem) -> str:
        """Return the item's corpus-unique key, e.g. ``"f01:d2:s15"``."""
        return item.key

    def load_items(self, candidates_path: Path) -> list[LabelItem]:
        """Load every candidate message as a ``LabelItem``.

        Args:
            candidates_path: the candidates file (see ``read_candidates``).

        Returns:
            One item per message, ``item_type`` ``"message"``, ``raw`` holding the candidate's
            fields and ``context`` the fields the owner sees.
        """
        items: list[LabelItem] = []
        for candidate in read_candidates(candidates_path):
            items.append(
                LabelItem(
                    case_index=candidate.case_index,
                    key=candidate.key,
                    item_type="message",
                    context={
                        "game": candidate.game,
                        "day": candidate.day,
                        "speaker": candidate.speaker,
                        "day_round": candidate.day_round,
                    },
                    raw=candidate.model_dump(mode="json"),
                )
            )
        return items

    def build_output_entry(self, item: LabelItem, vote: VoteResult) -> dict[str, Any]:
        """Return the merged-results entry for one message.

        Args:
            item: the labelled item.
            vote: the consensus over the model panel.

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
        """Return the markdown the owner reads for one message, with no model label of any kind.

        Args:
            item: a loaded item; ``item.raw`` holds the ``AccusationCandidate`` fields.
            game_state: unused; the context is already in the candidate.

        Returns:
            The item's key, the transcript and the question to answer.
        """
        candidate = AccusationCandidate.model_validate(item.raw)
        return (
            f"### Item {candidate.key}\n\n{render_transcript(candidate)}\n\n"
            f"**Whom does {candidate.speaker}'s message accuse?** `none`, or the accused ids in seat "
            "order, comma-joined."
        )

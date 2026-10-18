"""Slice 8: the deduction blocks, from items to the text the seat reads (catalogue "Rendering: what
the seat reads"). Pure functions of the items: nothing here reads a payload or draws a conclusion,
and the derivations go to the turn's log, never into the text.

Two blocks, by where they sit in the prompt (Agents/prompts/layout.py):
- the public block, from the public items alone, so it is the same for every seat and sits in the
  shared public record, before the cache boundary: the census and what each player could still be
  (F3, F7), and the standing facts of the public events (the conceals used up, a usable body, the
  Speculator's pick);
- the seat block, after the boundary: the seat's own census and per-player lines where they say
  more than the public's, its own results and the wills joined with the claims (F1, F2: in the
  claimant's entry, or the visitor's for F2), the conditionals on the claims (F4 and a role claim's
  F5 shared, a player's F5 or F6 in its entry), the claims compared (Table E: the role claims' status
  and an evil seat's claimable roles shared, every comparison in the entry of the player it is
  about), and the public working steps raised in today's discussion (raised.py).
The seat's own night results stay beside its records (level 1, format_night_actions).

The fold rules as built (the catalogue's numbering):
1. Conclusion first: a player's entry opens with what it could still be (F7), and the working steps
   about it follow. No reason is added that the item's own sentence does not carry.
2. Nothing is folded away inside a line: an item's sentence, with its premise, source and hedge, is
   shown whole or not at all.
3. A line is left out only when one other shown line states every fact it states, under the same
   premises (compared as facts, never as text; a role holds on every night, any other fact is about
   its night). Across levels too: the seat block leaves out what the public block or the seat's own
   level-1 lines state, and level 1 leaves out a line that another of its lines contains
   (`fold_own_lines`: the Illusionist's A45 beside the pack's A11–A13 or A53 on the same target).
4. The shared lines first (the census, then the standing facts of no one player), then one entry per
   living player in seat order, then the dead in death order; never ordered by content (the
   list-order bias). An entry is one primary sentence and at most two supporting ones: a player
   with more gets a second entry right after the first.
5. A working step (a public event's own line: a visit, a will's night, an absence) is shown only
   when raised today. The seat's own results are always shown, beside its records.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from pydantic_core import to_jsonable_python

from Agents.rules.seats import seat_order
from Agents.schemas.deduction import (
    BodyUsable,
    DeductionBlocks,
    DeductionItem,
    Fact,
    HeldBy,
    NeverPicked,
    NoConcealsLeft,
    OwnResultLine,
    PickMade,
    RenderedBlock,
    RoleIn,
)
from Agents.schemas.game_events import NightActionRecord

PUBLIC_HEADING = "== Worked out from the public record =="
PUBLIC_FRAMING = ("The game computed these lines from the announcements, the dead roster and the wills. "
                  "Each line is certain unless it names what it assumes.")
SEAT_HEADING = "== Worked out for you =="
SEAT_FRAMING = ("The game computed these lines from the public record, your own night results and what players say they did. "
                "Each line is certain unless it names what it assumes.")
RECORD_SEAT_FRAMING = ("The game computed these lines from the public record and your own night results. "
                       "Each line is certain unless it names what it assumes.")
"""Difficulty level 2 (mode "public"): no line reads what players say they did."""

ROLE_FACTS = (RoleIn, HeldBy)
"""Facts about a role, which is the same on every night: compared without their night."""

STANDING_FACTS = (NoConcealsLeft, BodyUsable, PickMade, NeverPicked)
"""Public events whose line is a standing fact about the rest of the game, not a working step: no
death will be hidden again (B6), a body the Necromancer can use (B25), the Speculator's pick (B26)
or its loss (B27)."""

ENTRY_SENTENCES = 3
"""One primary sentence and at most two supporting ones (fold rule 4)."""

Proposition = tuple[frozenset, frozenset]
"""A line's facts, each keyed by its night (None for a role fact), and its premises."""

NO_PROPOSITION: Proposition = (frozenset(), frozenset())


# --- which items a block may show -----------------------------------------------------------------

def is_conclusion(item: DeductionItem) -> bool:
    """A Table F line (the census, what a player could be, the joins with claims) or a Table E
    comparison of claims: always shown."""
    return item.row.startswith(("E", "F"))


def is_standing(item: DeductionItem) -> bool:
    return any(isinstance(fact, STANDING_FACTS) for fact in item.conclusion)


def is_working_step(item: DeductionItem) -> bool:
    return not is_conclusion(item) and not is_standing(item)


def is_raised(item: DeductionItem, raised: frozenset[tuple[str, int]]) -> bool:
    """Today's discussion named the item's night together with its subject or the player its source
    names (the attacked player, a will's holder)."""
    players = {item.subject} if item.subject else set()
    players |= {source.player for source in item.sources if source.player}
    return any((player, item.night) in raised for player in players)


# --- fold rule 3: one proposition, once ----------------------------------------------------------

def proposition(facts: Iterable[Fact], night: int, premises: Iterable[Fact] = ()) -> Proposition:
    facts = [_as_compared(fact) for fact in facts]
    return (frozenset((None if isinstance(fact, ROLE_FACTS) else night, fact) for fact in facts),
            frozenset(_as_compared(fact) for fact in premises))


def _as_compared(fact: Fact) -> Fact:
    """One fact, one form: "the Fortune Teller is held by player_10 alone" (a census line) is
    "player_10 is the Fortune Teller" (F7). Every role of the cast is dealt once and held."""
    if isinstance(fact, HeldBy) and len(fact.players) == 1:
        return RoleIn(fact.players[0], frozenset({fact.role}))
    return fact


def _of(item: DeductionItem) -> Proposition:
    return proposition(item.conclusion, item.night, item.premises)


def _covers(by: Proposition, line: Proposition) -> bool:
    """`by` states every fact of `line`, under the same premises."""
    return bool(line[0]) and line[1] == by[1] and line[0] <= by[0]


def _kept(lines: Sequence[Proposition], already: Sequence[Proposition] = ()) -> list[bool]:
    """Which lines stay: a line goes when a line already shown covers it, or another of these lines
    covers it and says more, or says the same and comes first."""
    kept = []
    for i, line in enumerate(lines):
        covered = any(_covers(shown, line) for shown in already) or any(
            j != i and _covers(other, line) and (other[0] != line[0] or j < i) for j, other in enumerate(lines))
        kept.append(not covered)
    return kept


def fold_own_lines(records: Sequence[NightActionRecord],
                   lines: Sequence[OwnResultLine | None]) -> list[OwnResultLine | None]:
    """Rule 3 on level 1, one entry per record: a line goes when another line of the seat's states
    every fact it states (the Illusionist's A45 and the pack's A11–A13 or A53 on the same target);
    the record's own prose stays. A roleblock line, which stands in for its record's prose, stays."""
    props = [proposition(line.facts, record.day) if line is not None else NO_PROPOSITION
             for record, line in zip(records, lines)]
    kept = _kept(props)
    return [line if keep or (line is not None and line.replaces_outcome) else None
            for line, keep in zip(lines, kept)]


# --- the two blocks ------------------------------------------------------------------------------

def render_public(items: Sequence[DeductionItem], living: Sequence[str], dead: Sequence[str]) -> RenderedBlock:
    """The public block, from the public items only (no seat's role, records or pack), so the same
    for every seat of a game at that moment. Every Table F line and standing fact; no working step,
    since what today's discussion raised changes turn by turn and would break the cached prefix."""
    candidates = [item for item in items if not is_working_step(item)]
    shown = [item for item, keep in zip(candidates, _kept([_of(item) for item in candidates])) if keep]
    return _block(PUBLIC_HEADING, PUBLIC_FRAMING, shown, living, dead)


def render_seat(seat_items: Sequence[DeductionItem], public_items: Sequence[DeductionItem],
                raised: frozenset[tuple[str, int]], living: Sequence[str], dead: Sequence[str],
                public: RenderedBlock, own: Sequence[tuple[int, OwnResultLine]], claims: bool = True) -> RenderedBlock:
    """The seat block: the seat's own items, and the public working steps raised today, less what
    the public block or the seat's own level-1 lines (night, line) already state."""
    already = [_of(item) for item in public.shown] + [proposition(line.facts, night) for night, line in own]
    candidates = [*seat_items, *(item for item in public_items if is_working_step(item) and is_raised(item, raised))]
    shown = [item for item, keep in zip(candidates, _kept([_of(item) for item in candidates], already)) if keep]
    return _block(SEAT_HEADING, SEAT_FRAMING if claims else RECORD_SEAT_FRAMING, shown, living, dead)


def _block(heading: str, framing: str, items: Sequence[DeductionItem], living: Sequence[str],
           dead: Sequence[str]) -> RenderedBlock:
    lines, ordered = _layout(items, living, dead)
    if not lines:
        return RenderedBlock("")
    return RenderedBlock("\n".join([heading, framing, *(f"- {line}" for line in lines)]), tuple(ordered))


def _layout(items: Sequence[DeductionItem], living: Sequence[str],
            dead: Sequence[str]) -> tuple[list[str], list[DeductionItem]]:
    """Rule 4: the lines in order, and the items in the order their sentences appear."""
    shared = [item for item in items if item.subject is None]
    about: dict[str, list[DeductionItem]] = {}
    for item in items:
        if item.subject is not None:
            about.setdefault(item.subject, []).append(item)
    order = [*living, *(player for player in dead if player not in living)]
    order += seat_order(player for player in about if player not in order)

    lines = [item.text for item in shared]
    ordered = list(shared)
    for player in order:
        group = sorted(about.get(player, []), key=lambda item: not is_conclusion(item))
        for start in range(0, len(group), ENTRY_SENTENCES):
            entry = group[start:start + ENTRY_SENTENCES]
            lines.append(" ".join(item.text for item in entry))
            ordered += entry
    return lines, ordered


# --- the log -------------------------------------------------------------------------------------

def deduction_log(blocks: DeductionBlocks | None) -> list[dict[str, Any]]:
    """Every shown item with its premises, sources and full derivation, as plain JSON, for the
    turn's prompt capture (Agents/turn/eval.py `log_prompt`): a live line traced to why it was made."""
    if blocks is None:
        return []
    return [_logged(name, item) for name, block in (("public", blocks.public), ("seat", blocks.seat))
            for item in block.shown]


def _logged(block: str, item: DeductionItem) -> dict[str, Any]:
    return {"block": block, "row": item.row, "subject": item.subject, "night": item.night,
            "grade": item.grade, "text": item.text,
            "conclusion": [_fact(fact) for fact in item.conclusion],
            "premises": [_fact(fact) for fact in item.premises],
            "sources": to_jsonable_python(item.sources),
            "derivation": to_jsonable_python(item.derivation)}


def _fact(fact: Fact) -> dict[str, Any]:
    return {"fact": type(fact).__name__, **to_jsonable_python(fact)}

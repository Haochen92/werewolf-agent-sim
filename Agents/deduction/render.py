"""Turns deduction items into the text a seat reads: the public block and the seat block.

Every function here works on items that are already computed: nothing reads a payload or draws a
conclusion. Each item's derivation (why the engine said it) goes to the turn's log, never into the
text.

The two blocks, by where they sit in the prompt (Agents/prompts/layout.py):
- The public block sits in the part of the prompt every seat shares, before the cache boundary, so
  it is built from public items alone and is the same for every seat. It holds what each player
  could still be, and the public facts that stay true for the rest of the game (no death can be
  hidden again, a body the Necromancer can use, the Speculator's pick).
- The seat block sits after the boundary. It holds what this seat's own knowledge adds: its census
  and its narrower "could still be" lines, its results and the wills read together with the claims,
  what would follow if claims were true, the claims compared with the record and with each other,
  and any public working step today's discussion brought up.
The lines about the seat's own night results are in neither block: they are printed beside the
results themselves (format_night_actions).

Display rules (the catalogue numbers them 1 to 5 and calls them fold rules):
1. Conclusion first: a player's entry opens with what that player could still be, and the steps
   that led there follow.
2. A line is shown whole or not at all: a sentence never loses its premise, its source or its hedge
   ("if player_2's watch is true, ...").
3. No repeats: a line is dropped only when another shown line states every fact it states, under
   the same assumptions. Lines are compared as facts, never as text. This holds across blocks too:
   the seat block drops what the public block or the seat's own result lines already say.
4. A fixed order, never by content, since a model leans toward whatever is listed first: the shared
   lines, then one entry per living player in seat order, then the dead in death order. An entry
   holds at most three sentences; a player with more gets a second entry right after the first.
5. A working step (one public event's own line: a visit, a will's night, a missing protection) is
   shown only when today's discussion named that player and night.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from pydantic_core import to_jsonable_python

from Agents.rules.seats import seat_order
from Agents.schemas.deduction import (
    CONCLUSION_TABLES,
    BodyUsable,
    DeductionBlocks,
    DeductionMode,
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
"""The seat block's framing in "public" mode, which has no line from what players say they did."""

ROLE_FACTS = (RoleIn, HeldBy)
"""Facts about a player's role. A role is the same on every night, so these compare without a night."""

STANDING_FACTS = (NoConcealsLeft, BodyUsable, PickMade, NeverPicked)
"""Public facts that stay true for the rest of the game, so they are shown like conclusions rather
than as working steps: no death can be hidden again, a body the Necromancer can use, the side the
Speculator picked, and a Speculator who never picked."""

ENTRY_SENTENCES = 3
"""An entry is one main sentence and at most two supporting ones (display rule 4)."""

Proposition = tuple[frozenset, frozenset]
"""A line's content in comparable form: its facts, each paired with its night (None for a role
fact), and the premises it assumes."""

NO_PROPOSITION: Proposition = (frozenset(), frozenset())


# --- which items a block may show -----------------------------------------------------------------

def is_conclusion(item: DeductionItem) -> bool:
    """True for a conclusion or a comparison of claims (see CONCLUSION_TABLES): shown whenever it
    applies, never held back as a working step."""
    return item.row.startswith(CONCLUSION_TABLES)


def is_standing(item: DeductionItem) -> bool:
    """True for a public fact that stays true for the rest of the game (STANDING_FACTS)."""
    return any(isinstance(fact, STANDING_FACTS) for fact in item.conclusion)


def is_working_step(item: DeductionItem) -> bool:
    """True for a step toward a conclusion: shown only when today's discussion raises it (rule 5)."""
    return not is_conclusion(item) and not is_standing(item)


def is_raised(item: DeductionItem, raised: frozenset[tuple[str, int]]) -> bool:
    """True when a message today named the item's night together with its player, or with a player
    its source names (the attacked player, a will's holder)."""
    players = {item.subject} if item.subject else set()
    players |= {source.player for source in item.sources if source.player}
    return any((player, item.night) in raised for player in players)


# --- display rule 3: no repeats, compared as facts ------------------------------------------------

def proposition(facts: Iterable[Fact], night: int, premises: Iterable[Fact] = ()) -> Proposition:
    """Returns the line's content as a Proposition, the form two lines are compared in: what it
    states, each fact paired with its night, and what it assumes."""
    stated = set()
    for fact in facts:
        fact = _canonical_form(fact)
        fact_night = None if isinstance(fact, ROLE_FACTS) else night  # a role is the same on every night
        stated.add((fact_night, fact))
    assumed = {_canonical_form(fact) for fact in premises}
    return frozenset(stated), frozenset(assumed)


def _canonical_form(fact: Fact) -> Fact:
    """Rewrites a HeldBy with exactly one player as the matching RoleIn; returns any other fact as is.

    "The Fortune Teller is held by player_10" (a census line) and "player_10 is the Fortune Teller" (a
    could-still-be line) say the same thing, so they must compare equal. It is the only rewrite the
    comparison makes."""
    if isinstance(fact, HeldBy) and len(fact.players) == 1:
        return RoleIn(fact.players[0], frozenset({fact.role}))
    return fact


def _proposition_of(item: DeductionItem) -> Proposition:
    """Returns the item's content as a Proposition."""
    return proposition(item.conclusion, item.night, item.premises)


def _is_repeat_of(candidate: Proposition, other: Proposition) -> bool:
    """True when `candidate` adds nothing to `other`: `other` states every fact `candidate` states,
    under the same premises. A candidate with no facts is never a repeat."""
    candidate_facts, candidate_premises = candidate
    other_facts, other_premises = other
    return bool(candidate_facts) and candidate_premises == other_premises and candidate_facts <= other_facts


def _which_to_keep(lines: Sequence[Proposition], already: Sequence[Proposition] = ()) -> list[bool]:
    """Returns, for each line, whether it stays. A line goes when it is a repeat of a line already
    shown, or of another of these lines that either says more or says the same and comes first."""
    kept = []
    for i, line in enumerate(lines):
        covered = any(_is_repeat_of(line, shown) for shown in already) or any(
            j != i and _is_repeat_of(line, other) and (other[0] != line[0] or j < i) for j, other in enumerate(lines))
        kept.append(not covered)
    return kept


def fold_own_lines(records: Sequence[NightActionRecord],
                   lines: Sequence[OwnResultLine | None]) -> list[OwnResultLine | None]:
    """Returns the seat's own result lines with repeats removed (rule 3), one entry per night record:
    None where a line was dropped or there was none.

    A line goes when another of the seat's lines states every fact it states; the record itself is
    still printed. For example, a wolf Illusionist's line about its conceal and the pack's kill line
    on the same target can state the same fact. A roleblock line always stays: it is printed in
    place of the record's own wording."""
    props = [proposition(line.facts, record.day) if line is not None else NO_PROPOSITION
             for record, line in zip(records, lines)]
    kept = _which_to_keep(props)
    return [line if keep or (line is not None and line.replaces_outcome) else None
            for line, keep in zip(lines, kept)]


# --- the two blocks ------------------------------------------------------------------------------

def render_public(items: Sequence[DeductionItem], living: Sequence[str], dead: Sequence[str]) -> RenderedBlock:
    """Returns the public block: every conclusion and standing fact among the public items, with
    repeats removed. Working steps are left out: whether one is shown depends on today's
    discussion, which changes turn by turn and would break the cached prefix."""
    candidates = [item for item in items if not is_working_step(item)]
    shown = [item for item, keep in zip(candidates, _which_to_keep([_proposition_of(item) for item in candidates])) if keep]
    return _block(PUBLIC_HEADING, PUBLIC_FRAMING, shown, living, dead)


def render_seat(seat_items: Sequence[DeductionItem], public_items: Sequence[DeductionItem],
                raised: frozenset[tuple[str, int]], living: Sequence[str], dead: Sequence[str],
                public: RenderedBlock, own: Sequence[tuple[int, OwnResultLine]],
                mode: DeductionMode = "full") -> RenderedBlock:
    """Returns the seat block: the seat's own items, plus the public working steps today's discussion
    raised, less anything the public block or the seat's own result lines (`own`, as (night, line))
    already say. `mode` "public" only changes the framing sentence, which then does not mention
    claims, since that mode has no line from them."""
    already = [_proposition_of(item) for item in public.shown] + [proposition(line.facts, night) for night, line in own]
    candidates = [*seat_items, *(item for item in public_items if is_working_step(item) and is_raised(item, raised))]
    shown = [item for item, keep in zip(candidates, _which_to_keep([_proposition_of(item) for item in candidates], already)) if keep]
    return _block(SEAT_HEADING, SEAT_FRAMING if mode == "full" else RECORD_SEAT_FRAMING, shown, living, dead)


def _block(heading: str, framing: str, items: Sequence[DeductionItem], living: Sequence[str],
           dead: Sequence[str]) -> RenderedBlock:
    """Returns the block's text (heading, framing sentence, one "- " line per entry) with the items in
    the order shown; an empty block when no line is left."""
    lines, ordered = _layout(items, living, dead)
    if not lines:
        return RenderedBlock("")
    return RenderedBlock("\n".join([heading, framing, *(f"- {line}" for line in lines)]), tuple(ordered))


def _layout(items: Sequence[DeductionItem], living: Sequence[str],
            dead: Sequence[str]) -> tuple[list[str], list[DeductionItem]]:
    """Returns the lines in display order (rule 4), and the items in the order their sentences appear."""
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
    """Returns every shown item with its premises, sources and full derivation, as plain JSON. It is
    saved with the turn's prompt (Agents/turn/eval.py `log_prompt`), so any line a model saw can be
    traced to why the engine wrote it."""
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

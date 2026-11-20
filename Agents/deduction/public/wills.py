"""Catalogue rows B15–B24 and B32: what a read-out will makes public (L11, R8).

From the moment a revealed town player's record is read out, each of its nights is a public fact,
and so is what that night's result implies. The implications are level 1's, run on the will's
records with the dead holder as the seat (Agents/deduction/public/known.py `holder_view`): its role
and records are public now, so every seat gets the same lines, worded with the holder's name
("player_3's will shows …").
- B15–B23: one item per night of the will: protections (B15), shots (B16, B17), checks (B18),
  watches (B19), follows (B20), sigils (B21), roleblocks (B22), held fire (B23).
- B32, B24: records accumulate and a blocked action leaves its own night, so a night the holder
  survived that is missing from its will is a night it made no choice (L11). B24 is a town role
  revealed with nothing on record. A missing night of a role that must act every night (the
  Healer, the Trailseer) is an input error, not a deduction: no line.
A seat reasoning before the reveal never has the will on its payload (time-indexing), so none of
these lines can reach it.
"""

from __future__ import annotations

from Agents.deduction.own_results import own_result_lines
from Agents.deduction.own_results.roleblock import roleblock_line
from Agents.deduction.own_results.sightings import sighting_line
from Agents.deduction.own_results.sigils import sigil_line
from Agents.deduction.public import wording
from Agents.deduction.public.known import holder_view
from Agents.deduction.records import read_record

# The will's own words for a night, so a line quotes the will exactly as it was read out.
from Agents.rules.night_record import _disclosed
from Agents.schemas.deduction import (
    DeductionItem,
    MadeNoChoice,
    NoAttackUnless,
    OwnResultLine,
    PublicRecord,
    SeatView,
    Source,
)
from Agents.schemas.game_events import NightActionRecord, ReadOutWill, WillClause
from Agents.schemas.role_traits import roles_with

MUST_ACT = frozenset(roles_with(must_act=True))
"""Roles with no decline word (catalogue L5): every night they survived is on their record. A will is
a town role's: the Healer's or the Trailseer's."""


def will_items(record: PublicRecord) -> list[DeductionItem]:
    items = []
    for will in record.wills:
        items += _clause_items(will, record)
        items += _missing_nights(will)
    return items


def _b_row(clause: WillClause) -> str:
    if clause.result == "roleblocked":
        return "B22"
    if clause.action == "protect":
        return "B15"
    if clause.action == "shoot":
        return "B16" if clause.result == "immune" else "B17"
    return {"investigate": "B18", "watch": "B19", "follow": "B20", "sigil": "B21", "hold_fire": "B23"}[clause.action]


def _clause_items(will: ReadOutWill, record: PublicRecord) -> list[DeductionItem]:
    """B15–B23: each night's level-1 line, as the public's, from the holder's view."""
    view = holder_view(record, will)
    level_one = own_result_lines(view)
    items = []
    for clause, own_record, line in zip(will.clauses, view.night_records, level_one):
        line = _in_the_holders_name(own_record, view, line, will.holder)
        if line is None:
            continue
        opening = wording.will_shows(will.holder, clause.night, _disclosed(own_record))
        items.append(DeductionItem(
            row=_rows(_b_row(clause), line.row), subject=_subject(clause, will), night=clause.night,
            conclusion=line.facts, text=f"{opening} {line.text}", grade=line.grade,
            sources=(Source("will", clause.night, will.holder),), derivation=(clause, will),
        ))
    return items


def _in_the_holders_name(record: NightActionRecord, view: SeatView, line: OwnResultLine | None,
                         holder: str) -> OwnResultLine | None:
    """The level-1 line, reworded where it speaks to the seat ("your watch", "you were roleblocked")."""
    if record.result == "roleblocked":
        line = roleblock_line(record, view)
        if line is None:
            return None
        text = (wording.holder_blocked_by_living_chanteuse(holder) if line.row == "A6"
                else wording.holder_blocked_through_chanteuse_body(holder))
        return OwnResultLine(text=text, row=line.row, grade=line.grade, facts=line.facts)
    if record.action in ("watch", "follow"):
        return sighting_line(read_record(record, view), view, holder=holder)
    if record.action == "sigil":
        return sigil_line(read_record(record, view), view, holder=holder)
    if record.action == "hold_fire":
        return OwnResultLine(text=wording.holder_held_fire(holder), row="B23",
                             facts=(NoAttackUnless(holder, frozenset()),))
    return line


def _rows(will_row: str, line_row: str) -> str:
    """"B18+A21": the will's row, then the level-1 row(s) whose logic the line ran."""
    return will_row if line_row == will_row else f"{will_row}+{line_row}"


def _subject(clause: WillClause, will: ReadOutWill) -> str:
    """The player the night's line is about: its target, or the holder itself."""
    return clause.target or will.holder


def _missing_nights(will: ReadOutWill) -> list[DeductionItem]:
    """B32, B24: every night before the death that the will leaves out."""
    if will.role in MUST_ACT:
        return []
    on_record = {clause.night for clause in will.clauses}
    items = []
    for night in range(1, will.day):
        if night in on_record:
            continue
        if will.clauses:
            row, text = "B32", wording.will_has_nothing_for(will.holder, night)
        else:
            row, text = "B24", wording.revealed_with_nothing_on_record(will.holder, will.role, night)
        items.append(DeductionItem(row=row, subject=will.holder, night=night, conclusion=(MadeNoChoice(will.holder),),
                                   text=text, sources=(Source("will", night, will.holder),), derivation=(will,)))
    return items

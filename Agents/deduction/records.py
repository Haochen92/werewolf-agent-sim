"""Catalogue L14: a seat's own night records, split into separate fields before any row reads them.

A record's `seen` list is not always a list of observed names. The necromancer's record puts the
body it used first; a check puts its target there; the pack's concealed kill puts the hidden role
there. Every row that reads a watch, a follow or a bet reads it through this module, never `seen`
raw. Only the seat's own records are read, never the night's hidden choices.
"""

from __future__ import annotations

from Agents.rules.night_record import PACK_ACTOR
from Agents.schemas.deduction import ReadRecord, SeatView
from Agents.schemas.game_events import NightActionRecord
from Agents.schemas.role_traits import BODY_USER

SIGHTINGS = ("watch", "follow")
SCORED = ("scored_1", "scored_2")


def _bet_role(record: NightActionRecord) -> str | None:
    """The role a scored bet named (the record's `bet_role`); None for any other record."""
    if record.action != "bet" or record.result not in SCORED:
        return None
    return record.bet_role


def read_record(record: NightActionRecord, view: SeatView) -> ReadRecord:
    """One record, split into its fields. A necromancer acts only through a body, so every record
    of its own starts `seen` with that body's name."""
    seen = list(record.seen)
    body = None
    if view.role == BODY_USER and record.actor == view.player_id and seen:
        body = seen.pop(0)

    observed: tuple[str, ...] = ()
    if record.action in SIGHTINGS and record.result == "seen":
        observed = tuple(seen)

    hidden_role = None
    if record.action == "kill" and record.actor == PACK_ACTOR and seen:
        # The pack's kill names in `seen` the role the living illusionist hid.
        hidden_role = seen[0]
    elif record.action == "kill" and body is not None:
        # The necromancer's kill through the illusionist's body that hid its victim's role.
        hidden_role = record.hidden_role

    return ReadRecord(
        night=record.day,
        actor=record.actor,
        action=record.action,
        target=record.target,
        result=record.result,
        body=body,
        observed=observed,
        hidden_role=hidden_role,
        bet_role=_bet_role(record),
    )

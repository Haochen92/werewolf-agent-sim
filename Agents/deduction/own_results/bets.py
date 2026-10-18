"""Catalogue rows A49, A50: a Fortune Teller's bet that scored on a player whose role was hidden.

A bet scores one point when its target dies, and two when the role it named was right. So a
scored bet on a hidden body tells the Fortune Teller what the public was not told: the body was the
named role (A49), or was not (A50). A bet on a body whose role was announced needs no line.
"""

from __future__ import annotations

from Agents.deduction import wording
from Agents.deduction.self_knowledge import possible_roles
from Agents.schemas.deduction import OwnResultLine, ReadRecord, RoleIn, SeatView


def bet_line(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """What a scored bet on a hidden body shows about its role."""
    target = record.target
    named = record.bet_role
    if named is None or not _hidden_death(target, record.night, view):
        return None
    if record.result == "scored_2":
        return OwnResultLine(text=wording.bet_shows_hidden_role(target, named), row="A49",
                             facts=(RoleIn(target, frozenset({named})),))
    possible = possible_roles(target, view)
    if named not in possible:
        return None  # the seat already knew it (its own role, or a role revealed on someone else)
    return OwnResultLine(text=wording.bet_shows_hidden_role_was_not(target, named), row="A50",
                         facts=(RoleIn(target, possible - {named}),))


def _hidden_death(player: str, night: int, view: SeatView) -> bool:
    return any(death.player == player and death.concealed and death.phase == "night" and death.day == night
               for death in view.dead_roster)

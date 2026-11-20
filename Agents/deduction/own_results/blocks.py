"""Catalogue rows A40–A43: what a block implies about its target, the Chanteuse's own or the
Necromancer's through her dead body.

A block takes on Town players and wolves; the lone killer and the neutral cannot be blocked.
- The living Chanteuse blocks only non-wolves, so a block that took means a Town player (A40), and
  one that did not means the lone killer or the neutral (A41).
- Through her body the Necromancer may block anyone but itself, wolves included: a block that took
  means a Town player or a wolf (A42), and one that did not means the neutral (A43).
"""

from __future__ import annotations

from Agents.deduction import wording
from Agents.deduction.self_knowledge import possible_roles
from Agents.schemas.deduction import OwnResultLine, ReadRecord, RoleIn, SeatView
from Agents.schemas.role_traits import UNBLOCKABLE
from Agents.schemas.roles import TOWN, side_of


def block_line(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """What the block's result implies about its target."""
    if record.body is None:
        if record.result == "blocked":
            return _chanteuse_block_took(record, view)
        return _chanteuse_block_did_not_take(record, view)
    if record.result == "blocked":
        return _block_through_body_took(record, view)
    return _block_through_body_did_not_take(record, view)


def _dealt(roles: tuple[str, ...], view: SeatView) -> list[str]:
    return [role for role in roles if view.cast_role_counts.get(role)]


def _unblockable_but_you(view: SeatView) -> str:
    """Through her body the blocker is the seat itself, so the one other role a block does not take
    on: the neutral."""
    return [role for role in _dealt(UNBLOCKABLE, view) if role != view.role][0]


def _chanteuse_block_took(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """A40."""
    town = frozenset(role for role in possible_roles(record.target, view) if side_of(role) == TOWN)
    if not town:
        return None
    return OwnResultLine(text=wording.your_block_took_so_town(record.target), row="A40",
                         facts=(RoleIn(record.target, town),))


def _chanteuse_block_did_not_take(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """A41: narrowed to one role when the seat knows the target cannot hold the other (it is dead,
    or the pack's attack showed who the Serial Killer is)."""
    unblockable = _dealt(UNBLOCKABLE, view)
    possible = possible_roles(record.target, view)
    still_possible = [role for role in unblockable if role in possible]
    if not still_possible:
        return None
    return OwnResultLine(
        text=wording.only_unblockable_roles(record.target, unblockable, still_possible),
        row="A41",
        facts=(RoleIn(record.target, frozenset(still_possible)),),
    )


def _block_through_body_took(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """A42."""
    neutral = _unblockable_but_you(view)
    not_neutral = possible_roles(record.target, view) - {neutral}
    return OwnResultLine(
        text=wording.block_through_chanteuse_body_took(record.target, neutral),
        row="A42",
        facts=(RoleIn(record.target, not_neutral),),
    )


def _block_through_body_did_not_take(record: ReadRecord, view: SeatView) -> OwnResultLine:
    """A43: the Necromancer cannot block itself, and no other lone killer is dealt with it."""
    neutral = _unblockable_but_you(view)
    return OwnResultLine(
        text=wording.block_through_chanteuse_body_did_not_take(record.target, neutral),
        row="A43",
        facts=(RoleIn(record.target, frozenset({neutral})),),
    )

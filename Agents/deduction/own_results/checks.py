"""What an investigation result tells the seat about its target (catalogue rows A21 to A25, the
`row` tags on the lines below). It covers the Investigator's own checks, and the Necromancer's
checks made through a dead Investigator's body.

A check reads Suspicious on every wolf, and also on the Necromancer on a night it killed through a
body (the Illusionist's or the Vigilante's). So:
- In a game with no Necromancer, and on night 1 in any game, Suspicious means a wolf (A21).
- From night 2 in a game with a Necromancer, Suspicious means a wolf or the Necromancer (A22). It
  narrows to a wolf when the Necromancer cannot have killed through a body that night: no killing
  body had been revealed dead before it, or the morning shows the Necromancer did something else
  (a save or a sigil through a body), or no attack through a body was announced. It narrows to the
  Necromancer when both wolves are known dead.
- Not suspicious means only "not a wolf": the target can still be the Serial Killer, the
  Necromancer or a neutral role (A23, or A24 in a game with a Necromancer).
- A check the Necromancer made through the Investigator's body was its whole night, so it killed no
  one, and its Suspicious means a wolf (A25).
"""

from __future__ import annotations

from Agents.deduction import wording
from Agents.deduction.morning import announcement_of, killed_through_a_body, necromancer_action_other_than_a_kill
from Agents.deduction.night_state import deaths_before_night, revealed_before_night
from Agents.deduction.self_knowledge import possible_roles
from Agents.schemas.deduction import KilledThroughBody, OwnResultLine, ReadRecord, RoleIn, SeatView
from Agents.schemas.role_traits import WOLF_ROLES, the_role
from Agents.schemas.roles import BORROWED_ABILITY, LONE_KILLER_ROLES, NEUTRAL_ROLES

NECROMANCER = the_role(reads_suspicious="when_killing_through_body")
"""The role that reads Suspicious on a night it killed through a body."""
KILLING_BODIES = frozenset(role for role, kind in BORROWED_ABILITY.items() if kind == "kill")
"""The roles whose bodies the Necromancer can kill through: the Illusionist and the Vigilante."""


def check_line(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """Returns the line a check's result implies about its target; None when there is nothing to say."""
    if record.body is not None:
        return _through_investigator_body(record, view)
    if record.result == "suspicious":
        return _suspicious(record, view)
    row = "A24" if view.cast_role_counts.get(NECROMANCER) else "A23"
    return _not_suspicious(record, view, row)


def _a_wolf(record: ReadRecord, view: SeatView, text: str, row: str) -> OwnResultLine | None:
    """Returns the line saying the target is a wolf, as the wolf roles it could still hold; None
    when the seat's other knowledge already rules every wolf role out for it."""
    wolf_roles = possible_roles(record.target, view) & WOLF_ROLES
    if not wolf_roles:
        return None
    return OwnResultLine(text=text, row=row, facts=(RoleIn(record.target, wolf_roles),))


def _suspicious(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """Returns what a Suspicious reading means: a wolf, the Necromancer, or either.

    Each check asks whether the Necromancer could have read Suspicious that night (it does only on a
    night it killed through a body). Rule it out and the target is a wolf; rule the wolves out and it
    is the Necromancer; if neither, the line names both, graded "possible"."""
    target = record.target
    night = record.night
    if not view.cast_role_counts.get(NECROMANCER):
        return _a_wolf(record, view, wording.suspicious_only_wolves_in_this_cast(target), "A21")
    if night == 1:
        return _a_wolf(record, view, wording.suspicious_on_night_one(target), "A21")

    possible = possible_roles(target, view)
    if NECROMANCER not in possible:
        return _a_wolf(record, view, wording.suspicious_and_not_the_necromancer(target), "A22")
    if not possible & WOLF_ROLES:
        return OwnResultLine(
            text=wording.suspicious_with_both_wolves_dead(target),
            row="A22",
            facts=(RoleIn(target, frozenset({NECROMANCER})), KilledThroughBody(target)),
        )

    if not deaths_before_night(view.dead_roster, night):
        return _a_wolf(record, view, wording.suspicious_with_no_one_dead_yet(target), "A22")
    bodies = set(revealed_before_night(view.dead_roster, night).values())
    if not bodies & KILLING_BODIES:
        return _a_wolf(record, view, wording.suspicious_with_no_killing_body(target), "A22")

    morning = announcement_of(view, night)
    if morning is not None and not killed_through_a_body(morning):
        deed = necromancer_action_other_than_a_kill(morning)
        if deed is not None:
            return _a_wolf(record, view, wording.suspicious_when_the_necromancer_did_something_else(target, deed),
                           "A22")
        return _a_wolf(record, view, wording.suspicious_with_no_kill_through_a_body_announced(target), "A22")

    return OwnResultLine(
        text=wording.suspicious_wolf_or_necromancer(target),
        row="A22",
        grade="possible",
        facts=(RoleIn(target, possible & (WOLF_ROLES | {NECROMANCER})),),
    )


def _not_suspicious(record: ReadRecord, view: SeatView, row: str) -> OwnResultLine | None:
    """Returns the "not a wolf" line, naming the killer and neutral roles the target could still
    hold; None when the target can only be a wolf."""
    target = record.target
    possible = possible_roles(target, view)
    not_a_wolf = possible - WOLF_ROLES
    if not not_a_wolf:
        return None
    still_possible = [role for role in LONE_KILLER_ROLES + NEUTRAL_ROLES if role in possible]
    return OwnResultLine(
        text=wording.not_suspicious(target, still_possible),
        row=row,
        facts=(RoleIn(target, not_a_wolf),),
    )


def _through_investigator_body(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """Returns the line for the Necromancer's check through the dead Investigator's body (A25). The
    check was its whole night, so it killed no one, and its target is never itself."""
    if record.result == "suspicious":
        return _a_wolf(record, view, wording.suspicious_through_investigator_body(record.target), "A25")
    return _not_suspicious(record, view, "A25")

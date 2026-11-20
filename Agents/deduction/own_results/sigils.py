"""Catalogue rows A36–A39: what a sigil implies, the Sigilist's own or the Necromancer's through the
dead Sigilist's body.

A sigil strikes back only at a player who attacked under their own name that night: the wolf
carrying the pack's kill, the Serial Killer or the Vigilante (never the Necromancer, whose attacks
are made through bodies).
- Saved from the sigil: the target attacked and could be harmed, so it is a wolf or the Vigilante,
  not the Serial Killer (A37).
- No effect: the target did not attack under its own name, or it is the Serial Killer, whom a sigil
  cannot harm (A38, serial-killer casts); in the necromancer casts it may be the Necromancer (A39).
A sigil that struck its target down needs a line only when the morning hid the role: then the
target is the Vigilante (hidden by the living Illusionist, it was the pack's victim), or a wolf or
the Vigilante (hidden through the Illusionist's body) (A36).
"""

from __future__ import annotations

from Agents.deduction import wording
from Agents.deduction.morning import announcement_of, death_of
from Agents.deduction.night_state import ALWAYS_IMMUNE
from Agents.deduction.self_knowledge import possible_roles
from Agents.schemas.deduction import NoAttackUnless, OwnResultLine, ReadRecord, RoleIn, SeatView
from Agents.schemas.role_traits import BODY_USER, STRUCK_BY_SIGIL, WOLF_ROLES, the_role

VIGILANTE = the_role(attack_announced_as="vigilante")
"""The one role a sigil strikes that is not a wolf."""
NECROMANCER = BODY_USER
"""Its attacks are made through bodies, never in its own name: a sigil never strikes it."""


def sigil_line(record: ReadRecord, view: SeatView, holder: str | None = None) -> OwnResultLine | None:
    """What the sigil's result implies about its target. `holder`: a dead Sigilist's sigil read out
    in its will (catalogue B21), worded with its name instead of "your"."""
    if record.result == "saved":
        return _saved_from_sigil(record, view, holder)
    if record.result == "miss":
        return _no_effect(record, view)
    if record.result == "hit":
        return _struck_down_hidden(record, view)
    return None


def _struck_down_hidden(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """A36, the concealed case: the sigil killed a player who attacked under their own name (a wolf
    carrying the kill, or the Vigilante; the Serial Killer cannot die at night). Hidden by the
    living Illusionist, it was the pack's victim, so not a wolf. A revealed role needs no line."""
    morning = announcement_of(view, record.night)
    death = death_of(morning, record.target) if morning is not None else None
    if death is None or not death.hidden_by:
        return None
    target = record.target
    attackers = possible_roles(target, view) & STRUCK_BY_SIGIL
    if death.hidden_by == "illusionist":
        if VIGILANTE not in attackers:
            return None
        return OwnResultLine(text=wording.sigil_struck_a_hidden_pack_victim(target), row="A36",
                             facts=(RoleIn(target, frozenset({VIGILANTE})),))
    if not attackers:
        return None
    return OwnResultLine(
        text=wording.sigil_struck_a_hidden_player(target, wolf=bool(attackers & WOLF_ROLES),
                                                  vigilante=VIGILANTE in attackers),
        row="A36",
        facts=(RoleIn(target, attackers),),
    )


def _saved_from_sigil(record: ReadRecord, view: SeatView, holder: str | None = None) -> OwnResultLine | None:
    """A37."""
    target = record.target
    possible = possible_roles(target, view)
    attackers = possible & STRUCK_BY_SIGIL
    if not attackers:
        return None
    return OwnResultLine(
        text=wording.sigil_saved_so_attacker(target, wolf=bool(attackers & WOLF_ROLES),
                                             vigilante=VIGILANTE in attackers, holder=holder),
        row="A37",
        facts=(RoleIn(target, attackers),),
    )


def _no_effect(record: ReadRecord, view: SeatView) -> OwnResultLine:
    """A38, A39. The Necromancer does nothing on night 1, so it cannot have attacked then."""
    target = record.target
    possible = possible_roles(target, view)
    row = "A39" if view.cast_role_counts.get(NECROMANCER) else "A38"

    if ALWAYS_IMMUNE in possible:
        return OwnResultLine(
            text=wording.sigil_no_effect_or_immune(target, ALWAYS_IMMUNE),
            row=row,
            grade="possible",
            facts=(NoAttackUnless(target, frozenset({ALWAYS_IMMUNE})),),
        )
    if NECROMANCER in possible and record.night >= 2:
        return OwnResultLine(
            text=wording.sigil_no_effect_unless_necromancer(target),
            row=row,
            facts=(NoAttackUnless(target, frozenset({NECROMANCER})),),
        )
    return OwnResultLine(
        text=wording.sigil_no_effect(target),
        row=row,
        facts=(NoAttackUnless(target, frozenset()),),
    )

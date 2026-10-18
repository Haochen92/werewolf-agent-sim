"""For an evil seat (a wolf, the lone killer): the roles it can still claim (F7's note, owner
2026-10-16), and a hidden body's role its own record shows (L8, owner 2026-10-17).

- The town and neutral roles the public record still allows it, the full list, so it can claim one
  without a public contradiction; and which of them no living player claims now (claiming one that is
  claimed starts a counter-claim). Facts only, no advice. The public's candidate roles for the seat
  are what the public record allows (propagation, checked against every legal deal by the
  brute-force oracle in the tests).
- With it, a hidden body's role the seat's own record shows (a wolf's pack kill, the Necromancer's
  kill through the Illusionist's body), when it is one of those roles and dealt once: no living
  player holds it.
"""

from __future__ import annotations

from Agents.deduction.candidates import public_candidates
from Agents.deduction.comparisons import wording
from Agents.deduction.records import read_record
from Agents.deduction.seat_view import public_record
from Agents.schemas.deduction import DeductionItem, HeldBy, OpenRoles, SeatView, Source
from Agents.schemas.roles import LONE_KILLER, NEUTRAL, ROLE_SPECS, TOWN, WOLVES


def _dealt(view: SeatView) -> list[str]:
    return [role for role in ROLE_SPECS if view.cast_role_counts.get(role)]


def claimable_roles(view: SeatView) -> list[str]:
    """The town and neutral roles the public record still allows an evil seat, in role order."""
    spec = ROLE_SPECS.get(view.role)
    if spec is None or spec.side not in (WOLVES, LONE_KILLER) or not view.living:
        return []
    public = public_candidates(public_record(view))
    if public is None or view.player_id not in public.roles:
        return []
    allowed = public.roles[view.player_id]
    return [role for role in _dealt(view) if role in allowed and ROLE_SPECS[role].side in (TOWN, NEUTRAL)]


def claimable_items(view: SeatView, night: int) -> list[DeductionItem]:
    """An evil seat's own line: the town and neutral roles the public record still allows it."""
    spec = ROLE_SPECS.get(view.role)
    if spec is None or spec.side not in (WOLVES, LONE_KILLER) or not view.living:
        return []
    public = public_candidates(public_record(view))
    if public is None or view.player_id not in public.roles:
        return []
    roles = claimable_roles(view)
    living = set(view.living)
    claimed = {player.current_role for player in view.claims if player.player in living}
    unclaimed = [role for role in roles if role not in claimed]
    return [DeductionItem(row="F7+E15", subject=None, night=night,
                          conclusion=(OpenRoles(view.player_id, frozenset(roles)),),
                          text=wording.claimable(roles, unclaimed),
                          sources=(Source("dead_roster", night), Source("announcement", night)),
                          receiver=view.player_id), *_hidden_roles(view, roles)]


def _hidden_roles(view: SeatView, claimable: list[str]) -> list[DeductionItem]:
    """A hidden body's role the seat's own record shows (L8: the living Illusionist's conceal, on the
    pack's kill record, to every wolf; one through its body, on the Necromancer's kill record, to the
    Necromancer), when it is a role the seat can claim (so the public record does not show it) dealt
    once (so the body was its only holder)."""
    concealed = {death.player for death in view.dead_roster if death.concealed}
    items = []
    for record in view.night_records:
        read = read_record(record, view)
        role = read.hidden_role
        if (not role or read.target not in concealed or role not in claimable
                or view.cast_role_counts.get(role) != 1):
            continue
        source = wording.own_record(read.night) if read.body else wording.pack_kill_record(read.night)
        items.append(DeductionItem(row="F7+L8", subject=None, night=read.night,
                                   conclusion=(HeldBy(role, (read.target,)), OpenRoles(view.player_id, frozenset({role}))),
                                   text=wording.hidden_role_claim(read.target, role, source),
                                   sources=(Source("own_record", read.night, read.target), Source("dead_roster", read.night)),
                                   derivation=(record,), receiver=view.player_id))
    return items

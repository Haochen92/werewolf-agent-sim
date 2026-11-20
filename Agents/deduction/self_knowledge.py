"""Which roles another player can still hold, from what this seat knows for certain about who holds
which role (catalogue, Table A preamble: self-knowledge is target-aware).

A line about another player leaves out the roles that player cannot hold: the seat's own role, a
wolf's packmates' roles, every role announced at a death, and the roles the seat's own records
prove on someone else. A role dealt once and known to be held by one player is ruled out for
everyone else.
"""

from __future__ import annotations

from Agents.deduction.night_state import IMMUNE_WHEN_SELF_BETTING, immune_candidates
from Agents.deduction.records import read_record
from Agents.schemas.deduction import SeatView


def _proved_by_own_records(view: SeatView) -> dict[str, str]:
    """Roles the seat's own records prove: the pack's hidden victim (the pack's record names the
    role) or the necromancer's (its kill through the illusionist's body names it), a target that survived an attack in silence when only one role could (A13), and a
    target saved by its own self-bet (A53, A54)."""
    proved: dict[str, str] = {}
    for record in view.night_records:
        read = read_record(record, view)
        if read.target is None:
            continue
        if read.hidden_role:
            proved[read.target] = read.hidden_role
        elif read.result == "self_bet_saved":
            proved[read.target] = IMMUNE_WHEN_SELF_BETTING
        elif read.action in ("kill", "shoot") and read.result == "immune":
            candidates = immune_candidates(read.target, read.night, view.role, view.cast_role_counts,
                                           view.dead_roster)
            if len(candidates) == 1:
                proved[read.target] = candidates[0]
    return proved


def known_holders(view: SeatView) -> dict[str, str]:
    """Every player whose role this seat knows for certain, with that role."""
    known = _proved_by_own_records(view)
    for death in view.dead_roster:
        if death.role and not death.concealed:
            known[death.player] = death.role
    known.update(view.pack_roles)
    if view.player_id and view.role:
        known[view.player_id] = view.role
    return known


def possible_roles(player: str, view: SeatView) -> frozenset[str]:
    """The dealt roles `player` can still hold, as far as this seat knows."""
    known = known_holders(view)
    if player in known:
        return frozenset({known[player]})
    possible = set()
    for role, dealt in view.cast_role_counts.items():
        held_by_others = sum(1 for holder, held in known.items() if held == role and holder != player)
        if dealt > held_by_others:
            possible.add(role)
    return frozenset(possible)

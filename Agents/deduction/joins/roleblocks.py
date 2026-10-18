"""A roleblock joined with the claims of who came to the blocked player (catalogue F1, F2; A6, A7, L4).

A roleblock is a visit: only the Chanteuse blocks, and while she is alive the block is her own visit
(A6); once she is revealed dead, the Necromancer blocks through her body and the visit shows her
name (A7). The blocked player is the seat, or a will's holder (B22).
- The Chanteuse known (her role pinned on one player): a claimed sighting of her at the door is
  true. Certain (F1, AC2 line 2).
- The block through her body: a claimed sighting of her dead name at the door is true in name (F1).
- The Chanteuse not known: a claim that some living player came to the door, taken as true, leaves
  two explanations, and only two: that player is the Chanteuse, or a second visitor came beside
  her. Never "that player is the Chanteuse" (F2, AC1 line 2): any visiting role could also have come.
"""

from __future__ import annotations

from collections.abc import Callable

from Agents.deduction.joins import wording
from Agents.deduction.joins.reports import claimed_role
from Agents.deduction.night_state import deaths_before_night
from Agents.deduction.own_results.roleblock import roleblock_line
from Agents.deduction.public.known import holder_view
from Agents.rules.night_record import PACK_ACTOR
from Agents.schemas.deduction import (
    AnyOf,
    BlockedBy,
    DeductionItem,
    PublicRecord,
    RoleIn,
    SeatView,
    Source,
    VisitAsClaimed,
    VisitClaim,
    Visited,
    WentTo,
)
from Agents.schemas.game_events import NightActionRecord
from Agents.schemas.role_traits import BLOCKER

CHANTEUSE = BLOCKER

Possible = Callable[[str], frozenset[str]]
"""The roles a player can still hold, as the seat knows (its candidate roles)."""


def roleblock_items(view: SeatView, record: PublicRecord, claimed: list[VisitClaim],
                    possible: Possible) -> list[DeductionItem]:
    """The seat's own roleblocks first, then each will's."""
    blocks = [(own, view, None) for own in view.night_records
              if own.actor == view.player_id and own.actor != PACK_ACTOR and own.result == "roleblocked"]
    for will in record.wills:
        holder = holder_view(record, will)
        blocks += [(own, holder, will.holder) for own in holder.night_records if own.result == "roleblocked"]
    items = []
    for own, blocked_view, holder in blocks:
        items += _joins(own, blocked_view, holder, view, claimed, possible)
    return items


def _joins(own: NightActionRecord, blocked_view: SeatView, holder: str | None, view: SeatView,
           claimed: list[VisitClaim], possible: Possible) -> list[DeductionItem]:
    line = roleblock_line(own, blocked_view)
    if line is None:
        return []
    blocked = blocked_view.player_id
    night = own.day
    reports = [r for r in claimed if r.night == night and r.target == blocked and r.went_ahead
               and r.claim.claimant not in (view.player_id, holder)]
    if line.row == "A7":
        return _through_body(own, holder, view, reports)
    dead_before = {death.player for death in deaths_before_night(view.dead_roster, night)}
    # The visitor's own word counts only as a bare visit ("I went to player_8"): a claimed action, taken
    # as true, would also claim a role, a premise for the conditionals (F5), not for this line.
    reports = [r for r in reports if r.visitor not in dead_before and (r.sighting or r.claim.action == "visit")]
    chanteuse = _pinned(possible, view)
    if chanteuse == view.player_id:
        return []  # the seat's own block: its own action's line says it
    if chanteuse is not None:
        return [_known(own, holder, view, r, chanteuse) for r in reports
                if r.visitor == chanteuse and r.sighting and r.claim.claimant != chanteuse]
    return _explanations(own, holder, view, reports, possible)


def _pinned(possible: Possible, view: SeatView) -> str | None:
    """The player the Chanteuse's role is pinned on, living or dead, if the seat knows one."""
    for player in [*view.living, *(death.player for death in view.dead_roster)]:
        if possible(player) == frozenset({CHANTEUSE}):
            return player
    return None


def _sources(own: NightActionRecord, holder: str | None, claimants: list[str]) -> tuple[Source, ...]:
    first = Source("own_record", own.day) if holder is None else Source("will", own.day, holder)
    return (first, *(Source("claim", own.day, claimant) for claimant in claimants))


def _known(own: NightActionRecord, holder: str | None, view: SeatView, report: VisitClaim,
           chanteuse: str) -> DeductionItem:
    """F1: a sighting of the known Chanteuse at the blocked player's door is true."""
    claimant = report.claim.claimant
    blocked = holder or view.player_id
    dead = any(death.player == chanteuse for death in view.dead_roster)
    text = wording.chanteuse_as_reported(claimant, chanteuse, own.day, dead,
                                         claimed_role(report.claim, view.claims), holder)
    return DeductionItem(
        row="F1", subject=claimant, night=own.day,
        conclusion=(BlockedBy(blocked, through_body=False), RoleIn(chanteuse, frozenset({CHANTEUSE})),
                    VisitAsClaimed(claimant, chanteuse, blocked, shown=True)),
        text=text, sources=_sources(own, holder, [claimant]), derivation=(own, report.claim),
        receiver=view.player_id,
    )


def _through_body(own: NightActionRecord, holder: str | None, view: SeatView,
                  reports: list[VisitClaim]) -> list[DeductionItem]:
    """F1: a sighting of the dead Chanteuse's name at the door, when the block came through her body."""
    bodies = [death.player for death in deaths_before_night(view.dead_roster, own.day)
              if death.role == CHANTEUSE and not death.concealed]
    blocked = holder or view.player_id
    items = []
    for report in reports:
        claimant = report.claim.claimant
        if not report.sighting or report.visitor not in bodies:
            continue
        text = wording.body_as_reported(claimant, report.visitor, own.day,
                                        claimed_role(report.claim, view.claims), holder)
        items.append(DeductionItem(
            row="F1", subject=claimant, night=own.day,
            conclusion=(BlockedBy(blocked, through_body=True),
                        VisitAsClaimed(claimant, report.visitor, blocked, shown=True)),
            text=text, sources=_sources(own, holder, [claimant]), derivation=(own, report.claim),
            receiver=view.player_id,
        ))
    return items


def _explanations(own: NightActionRecord, holder: str | None, view: SeatView, reports: list[VisitClaim],
                  possible: Possible) -> list[DeductionItem]:
    """F2, one line per claimed visitor who could be the Chanteuse, on at most two named claims."""
    blocked = holder or view.player_id
    visitors = []
    for report in reports:
        if report.visitor not in visitors and CHANTEUSE in possible(report.visitor):
            visitors.append(report.visitor)
    items = []
    for visitor in visitors:
        about = [r for r in reports if r.visitor == visitor]
        reporters = []
        for r in about:
            if r.sighting and r.claim.claimant != visitor and r.claim.claimant not in reporters:
                reporters.append(r.claim.claimant)
        agreement = next((r for r in about if not r.sighting), None)
        named = reporters[:1] if agreement is not None else reporters[:2]
        used = [next(r for r in about if r.sighting and r.claim.claimant == name) for name in named]
        if agreement is not None:
            used.append(agreement)
        premise = wording.claimed_visitor(named, visitor, agreement is not None, own.day, holder)
        others = possible(visitor) - {CHANTEUSE}
        items.append(DeductionItem(
            row="F2", subject=visitor, night=own.day,
            conclusion=(AnyOf(((RoleIn(visitor, frozenset({CHANTEUSE})),),
                               (RoleIn(visitor, others), WentTo(visitor, blocked),
                                Visited(frozenset({CHANTEUSE}), blocked, shown=None)))),),
            text=wording.chanteuse_or_both(premise, visitor, holder), grade="follows_if_claims",
            premises=(WentTo(visitor, blocked),),
            sources=_sources(own, holder, [r.claim.claimant for r in used]),
            derivation=(own, *(r.claim for r in used)), receiver=view.player_id,
        ))
    return items

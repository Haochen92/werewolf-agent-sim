"""The visits the claims and the engine sources state, and the whole accounts that rule visits out
(catalogue Table E's preamble; L4, L12, L13): what the comparisons set against each other.

A statement says a visit went ahead (VisitStatement):
- a claimed sighting (a watch saw the visitor come, a follow saw the followed player go): one a watch
  or a follow could report;
- a claimant's own action that the claim says went ahead (an outcome stated, or a bare visit): it may
  be one the living Illusionist's conceal hid, when the target was that night's concealed victim;
- a claimed roleblock: the Chanteuse came to the claimant, or the Necromancer through her body (the
  names that could have made the block, from the seat's candidate roles);
- the same from an engine source: the seat's own action, a visitor its watch or follow saw, its own
  roleblock, and the same in every read-out will.
An account rules visits out (VisitList), and only a whole one does (L12): an engine watch (every
visitor but the watcher) or follow (every place the followed player went that a watch could see), a
claimed sighting of "no one", a player's own "I visited no one" or "I did not go to X", a claimed
roleblock (a blocked player goes nowhere), and the seat's own movements (it knows every visit it made;
a wolf's pack kill and the Necromancer's bodies are left out).
Only the latest version of a claim, on a night said, and never the seat's own claims: it knows them.
"""

from __future__ import annotations

from collections.abc import Callable

from Agents.deduction.joins.known_visits import VISITING_ACTIONS, known_visits
from Agents.deduction.joins.reports import visits_of
from Agents.deduction.morning import announcement_of
from Agents.deduction.night_state import deaths_before_night, revealed_before_night
from Agents.deduction.public.known import holder_view
from Agents.deduction.records import read_record
from Agents.rules.night_record import PACK_ACTOR
from Agents.schemas.deduction import (
    ActionClaim,
    AnyOf,
    BlockedBy,
    Fact,
    NoShownVisitBy,
    NoShownVisitTo,
    NotAllTrue,
    NoVisitBy,
    PublicRecord,
    SeatView,
    VisitAsClaimed,
    VisitList,
    VisitStatement,
    WentTo,
)
from Agents.schemas.game_events import NightActionRecord
from Agents.schemas.role_traits import BLOCKER, BODY_USER
from Agents.schemas.roles import BORROWED_ABILITY, ROLE_SPECS

CHANTEUSE = BLOCKER
NECROMANCER = BODY_USER

Possible = Callable[[str], frozenset[str]]
"""The roles a player can still hold, as the seat knows (its candidate roles)."""


def blocked_fact(player: str) -> AnyOf:
    """`player`'s action that night was cancelled by a block (the living Chanteuse's, or through her body)."""
    return AnyOf(((BlockedBy(player, through_body=False),), (BlockedBy(player, through_body=True),)))


def latest_claims(view: SeatView) -> list[ActionClaim]:
    """Every other player's current claimed actions, on a night said, in the claims' order. A player
    who claims the Necromancer is left out: its actions go through bodies, under their names, so what
    its words say of its own visits is not what they say of anyone else's."""
    return [claim for player in view.claims if player.player != view.player_id and player.current_role != NECROMANCER
            for claim in player.actions if claim.latest and claim.night > 0]


# --- the night's public facts -------------------------------------------------------------------

def concealed_victim(view: SeatView, night: int) -> str | None:
    """The pack's victim whose role the living Illusionist hid that night: every visit of the pack's
    carrier to it is hidden from every watch and follow (L4)."""
    announcement = announcement_of(view, night)
    if announcement is None:
        return None
    return next((death.player for death in announcement.deaths if death.hidden_by == "illusionist"), None)


def maybe_hidden(view: SeatView, night: int, target: str) -> bool:
    """A visit to `target` that night may be hidden: `target` was the concealed victim, or the morning
    is not on the payload."""
    if announcement_of(view, night) is None:
        return True
    return concealed_victim(view, night) == target


def blockers(view: SeatView, night: int, possible: Possible) -> tuple[str, ...]:
    """The names a roleblock on `night` could show (L2): the Chanteuse's possible holders alive when
    the night began, or, once she was revealed dead, her body's name (the Necromancer's block, from
    night 2). Empty when no one could block."""
    if not view.cast_role_counts.get(CHANTEUSE):
        return ()
    revealed = revealed_before_night(view.dead_roster, night)
    body = next((player for player, role in revealed.items() if role == CHANTEUSE), None)
    if body is not None:
        usable = night >= 2 and view.cast_role_counts.get(NECROMANCER) and CHANTEUSE in BORROWED_ABILITY
        return (body,) if usable else ()
    gone = {death.player for death in deaths_before_night(view.dead_roster, night)}
    players = [*view.living, *(death.player for death in view.dead_roster)]
    return tuple(player for player in players if player not in gone and CHANTEUSE in possible(player))


# --- statements ---------------------------------------------------------------------------------

def claim_statements(view: SeatView, possible: Possible) -> list[VisitStatement]:
    statements = []
    for claim in latest_claims(view):
        if claim.blocked:
            names = blockers(view, claim.night, possible)
            if names:
                statements.append(VisitStatement(claim.night, names, claim.claimant, shown=True, source="claim",
                                                 claim=claim, block=True, facts=(blocked_fact(claim.claimant),)))
            continue
        for visit in visits_of(claim):
            if visit.sighting:
                facts: tuple[Fact, ...] = (VisitAsClaimed(claim.claimant, visit.visitor, visit.target, shown=True),)
                statements.append(VisitStatement(claim.night, (visit.visitor,), visit.target, shown=True,
                                                 source="claim", claim=claim, facts=facts))
            elif visit.went_ahead:
                facts = (VisitAsClaimed(claim.claimant, claim.claimant, visit.target, shown=False),)
                statements.append(VisitStatement(claim.night, (claim.claimant,), visit.target,
                                                 shown=not maybe_hidden(view, claim.night, visit.target),
                                                 source="claim", claim=claim, facts=facts))
    return statements


def engine_statements(view: SeatView, record: PublicRecord, possible: Possible) -> list[VisitStatement]:
    """The seat's own visits and those its watch or follow saw, then each will's (known_visits), and
    every roleblock the seat or a will received."""
    statements = [VisitStatement(visit.night, (visit.visitor,), visit.target, shown=True,
                                 source="own_record" if visit.holder is None else "will", known=visit)
                  for visit in known_visits(view, record)]
    for own, blocked, holder in _roleblocks(view, record):
        names = blockers(view, own.day, possible)
        if names:
            statements.append(VisitStatement(own.day, names, blocked, shown=True,
                                             source="own_record" if holder is None else "will", block=True))
    return statements


def _roleblocks(view: SeatView, record: PublicRecord) -> list[tuple[NightActionRecord, str, str | None]]:
    blocks = [(own, view.player_id, None) for own in view.night_records
              if own.actor == view.player_id and own.actor != PACK_ACTOR and own.result == "roleblocked"]
    for will in record.wills:
        blocks += [(own, will.holder, will.holder) for own in holder_view(record, will).night_records
                   if own.result == "roleblocked"]
    return blocks


# --- whole accounts -----------------------------------------------------------------------------

def claim_lists(view: SeatView) -> list[VisitList]:
    lists = []
    for claim in latest_claims(view):
        if claim.blocked:
            lists.append(VisitList(claim.night, "none_by", claim.claimant, (), None, "claim", claim=claim,
                                   facts=(blocked_fact(claim.claimant),)))
        elif claim.action == "no_action" and not claim.target:
            lists.append(VisitList(claim.night, "none_by", claim.claimant, (), None, "claim", claim=claim,
                                   facts=(NoVisitBy(claim.claimant),)))
        elif claim.action == "no_action":
            lists.append(VisitList(claim.night, "not_to", claim.claimant, (claim.target,), None, "claim", claim=claim,
                                   facts=(NotAllTrue((WentTo(claim.claimant, claim.target),)),)))
        elif claim.seen_complete and claim.action == "watch" and claim.target:
            lists.append(VisitList(claim.night, "to", claim.target, (), claim.claimant, "claim", claim=claim,
                                   facts=(NoShownVisitTo(claim.target, claim.claimant),)))
        elif claim.seen_complete and claim.action == "follow" and claim.target:
            lists.append(VisitList(claim.night, "by", claim.target, (), None, "claim", claim=claim,
                                   facts=(NoShownVisitBy(claim.target),)))
    return lists


def engine_lists(view: SeatView, record: PublicRecord) -> list[VisitList]:
    """The seat's own watches and follows, its own movements, then each will's watches and follows."""
    lists = []
    if view.role != NECROMANCER:
        lists += _sightings(view, None)
        if not ROLE_SPECS[view.role].pack:
            lists += _movements(view)
    for will in record.wills:
        lists += _sightings(holder_view(record, will), will.holder)
    return lists


def _sightings(view: SeatView, holder: str | None) -> list[VisitList]:
    lists = []
    for own in view.night_records:
        if own.actor != view.player_id or own.action not in ("watch", "follow") or own.result != "seen":
            continue
        observed = read_record(own, view).observed
        kind = "to" if own.action == "watch" else "by"
        watcher = view.player_id if own.action == "watch" else None
        lists.append(VisitList(own.day, kind, own.target, tuple(observed), watcher,
                               "own_record" if holder is None else "will", record=own, holder=holder))
    return lists


def _movements(view: SeatView) -> list[VisitList]:
    """Every visit the seat made, night by night, from its own records: a town or neutral seat, or the
    Serial Killer, makes no visit its records do not show (none of its visits is hidden)."""
    nights = sorted({announcement.night for announcement in view.announcements})
    lists = []
    for night in nights:
        places = tuple(own.target for own in view.night_records
                       if own.day == night and own.actor == view.player_id and own.action in VISITING_ACTIONS
                       and own.result != "roleblocked" and own.target)
        lists.append(VisitList(night, "by", view.player_id, places, None, "own_record"))
    return lists

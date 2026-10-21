"""The premises of the conditional lines, and what each adds to the propagation (catalogue Table F,
"How the engine derives them": a claim as premise adds the claimant's role and treats the claimed
facts as verified for that run only).

Premises, from the typed claims (SeatView.claims), never the seat's own:
- the current role claims (F4): the latest, not withdrawn, role claim of every player whose role the
  seat cannot check (living, or a hidden body). A claim it can check is left out: a true one adds
  nothing, and a false one (its own bluff, a packmate's, a revealed player's, a role not dealt) makes
  the line assume only the claims it cannot check. When one claim is left, the line names it (F5,
  "player_9's claim").
- one claimed night action (F5, "player_2's watch"): its claimant's role (the role claimed, or the
  role the action implies), and what it states as verified: each visit it says went ahead (its own,
  and those a watch or a follow saw), a check's reading, a roleblock. Skipped: a claim whose role
  claim and action disagree, an action whose role was withdrawn, a night not said, a claimed visit by
  the seat that its own records do not show or its own role could not have made (the seat knows that
  claim is false).
What a premise adds, as role constraints: each assumed role; a check's reading as the roles it
allows (Suspicious: a wolf, or from night 2 in Necromancer casts the Necromancer; Not suspicious: not
a wolf); a roleblock as the level-1 rows read one (a role that can be blocked, the blocker alive);
each visit as the roles that could have made it (visits.py). None when the premise cannot hold with
what the seat knows (a visit to a player already dead, a body nothing could act through): no line.
"""

from __future__ import annotations

from Agents.deduction.candidates.constraints import NECROMANCER, WOLF_ROLES, Provenance, fact_constraints
from Agents.deduction.conditionals.visits import CHANTEUSE, roles_that_could_visit, visited_twice
from Agents.deduction.joins.reports import ACTION_ROLE, visits_of
from Agents.deduction.morning import announcement_of
from Agents.deduction.night_state import deaths_before_night, revealed_before_night
from Agents.schemas.deduction import (
    ActedThroughBody,
    ActionClaim,
    BlockedBy,
    Candidates,
    KnownVisit,
    OnlyRoles,
    Premise,
    RoleConstraint,
    RoleIn,
    SeatView,
    Source,
    VisitAsClaimed,
)
from Agents.schemas.role_traits import BLOCKER, ROLE_TRAITS, SUSPICIOUS_THROUGH_A_BODY
from Agents.schemas.roles import BORROWED_ABILITY, ROLE_SPECS

PREMISE_ACTIONS = frozenset({*ACTION_ROLE, "kill", "visit"})
"""Claimed actions that can be a premise: those that imply a role, an attack, a bare visit."""
CHECK_READINGS = frozenset({"suspicious", "not_suspicious"})
RULE = "premise"


def _dealt(view: SeatView) -> frozenset[str]:
    return frozenset(role for role, count in view.cast_role_counts.items() if count > 0)


# --- the current role claims (F4) ----------------------------------------------------------------

def role_claims_premise(view: SeatView, base: Candidates) -> Premise | None:
    """The role claims the seat cannot check, together; one claim named alone; None when none is left."""
    dealt = _dealt(view)
    assumed: list[tuple[str, str]] = []
    unchecked_only = False
    for player in view.claims:
        role = player.current_role
        if role is None:
            continue
        if player.player == view.player_id:
            unchecked_only |= role != view.role
            continue
        possible = base.roles.get(player.player, frozenset())
        if role not in dealt or role not in possible:
            unchecked_only = True  # a claim the seat knows is false
        elif len(possible) > 1:
            assumed.append((player.player, role))
    if not assumed:
        return None
    facts = tuple(RoleIn(player, frozenset({role})) for player, role in assumed)
    if len(assumed) == 1:
        return Premise(kind="role_claim", claimant=assumed[0][0], roles=tuple(assumed), facts=facts)
    return Premise(kind="role_claims", claimant=None, roles=tuple(assumed), facts=facts, unchecked_only=unchecked_only)


# --- one claimed night action (F5) ----------------------------------------------------------------

def action_premises(view: SeatView, own_visits: list[KnownVisit]) -> list[Premise]:
    """One premise per latest claimed action of another player, in the claims' order."""
    premises = []
    for player in view.claims:
        if player.player == view.player_id:
            continue
        for claim in player.actions:
            if not claim.latest or claim.night <= 0 or claim.action not in PREMISE_ACTIONS:
                continue
            role = _role_of(claim, player.current_role, player.withdrawn_roles)
            if role is False:
                continue
            premise = _action_premise(claim, role, view, own_visits)
            if premise is not None:
                premises.append(premise)
    return premises


def _role_of(claim: ActionClaim, current: str | None, withdrawn: tuple[str, ...]) -> str | None | bool:
    """The role the claim stands on; None when it names none (a bare visit, an attack); False when
    it cannot be a premise (its role claim and its action disagree, or that role was withdrawn)."""
    implied = ACTION_ROLE.get(claim.action)
    if current is not None and current not in ROLE_TRAITS:
        current = None  # a retired role an old summary may name: no role
    if implied is not None and current is not None and current != implied:
        return False
    if implied is not None and current is None and implied in withdrawn:
        return False
    return current or implied


def _action_premise(claim: ActionClaim, role: str | None, view: SeatView,
                    own_visits: list[KnownVisit]) -> Premise | None:
    claimant, night = claim.claimant, claim.night
    facts = [RoleIn(claimant, frozenset({role}))] if role else []
    visits = tuple(visit for visit in visits_of(claim) if visit.went_ahead)
    for visit in visits:
        if visit.visitor == view.player_id and not _seat_went(view, night, visit.target, own_visits):
            return None  # the seat's own records do not show that visit: it knows the claim is false
        facts.append(VisitAsClaimed(claimant, visit.visitor, visit.target, shown=visit.sighting))
    if claim.action == "investigate" and claim.result in CHECK_READINGS and claim.target:
        facts.append(RoleIn(claim.target, _reading_roles(claim.result, night, _dealt(view))))
    if claim.blocked:
        chanteuse_dead = BLOCKER in revealed_before_night(view.dead_roster, night).values()
        facts.append(BlockedBy(claimant, through_body=chanteuse_dead))
    if len(facts) == (1 if role else 0):
        return None  # nothing beyond the role: the role claim's own premise
    return Premise(kind="action", claimant=claimant, roles=((claimant, role),) if role else (), claim=claim,
                   visits=visits, facts=tuple(facts), night=night)


def _seat_went(view: SeatView, night: int, target: str, own_visits: list[KnownVisit]) -> bool:
    """Whether the seat's records show it went to `target` that night. A wolf's visit as the pack's
    carrier is not in its records: for a wolf, nothing rules the claim out."""
    if ROLE_SPECS[view.role].pack:
        return True
    return any(visit.night == night and visit.visitor == view.player_id and visit.target == target
               and visit.holder is None for visit in own_visits)


def _reading_roles(result: str, night: int, dealt: frozenset[str]) -> frozenset[str]:
    """The roles a check's reading allows (A21 to A25): Suspicious is a wolf, or from night 2 the
    Necromancer (a kill through a body); Not suspicious is anyone but a wolf."""
    if result == "suspicious":
        by_a_body_kill = {SUSPICIOUS_THROUGH_A_BODY} if SUSPICIOUS_THROUGH_A_BODY in dealt and night >= 2 else set()
        return frozenset(WOLF_ROLES | by_a_body_kill)
    return dealt - WOLF_ROLES


# --- what a premise adds to the propagation --------------------------------------------------------

def premise_constraints(premise: Premise, view: SeatView, base: Candidates,
                        engine_visits: list[KnownVisit]) -> list[RoleConstraint] | None:
    """The premise as role constraints; None when it cannot hold with what the seat knows.
    `engine_visits`: the visits the seat's records and the wills show went ahead (with the
    premise's own, two on one night make the visitor the Chanteuse)."""
    dealt = _dealt(view)
    where = Provenance(RULE, tuple(Source("claim", premise.night, player) for player in _claimants(premise)), ())
    constraints: list[RoleConstraint] = []
    visits: list[tuple[str, str]] = []
    for fact in premise.facts:
        if isinstance(fact, RoleIn):
            if not fact.roles & dealt:
                return None
            constraints.append(OnlyRoles(fact.player, fact.roles, RULE, where.sources))
        elif isinstance(fact, BlockedBy):
            if fact.through_body and NECROMANCER not in dealt:
                return None
            constraints += fact_constraints(fact, premise.night, where, view.dead_roster, dealt)
        elif isinstance(fact, VisitAsClaimed):
            added = _visit(fact, premise.night, view, base, dealt, where)
            if added is None:
                return None
            constraints += added
            visits.append((fact.visitor, fact.target))
    dead_before = {death.player for death in deaths_before_night(view.dead_roster, premise.night)}
    known = [(visit.visitor, visit.target) for visit in engine_visits if visit.night == premise.night]
    for visitor in visited_twice([*known, *visits]):
        if visitor not in dead_before and visitor in base.roles:
            constraints.append(OnlyRoles(visitor, frozenset({CHANTEUSE}), RULE, where.sources))
    return constraints


def _claimants(premise: Premise) -> list[str]:
    return [premise.claimant] if premise.claimant else [player for player, _ in premise.roles]


def _visit(fact: VisitAsClaimed, night: int, view: SeatView, base: Candidates, dealt: frozenset[str],
           where: Provenance) -> list[RoleConstraint] | None:
    dead_before = {death.player: death for death in deaths_before_night(view.dead_roster, night)}
    if fact.target in dead_before:
        return None  # no visit goes to the dead
    if fact.visitor == view.player_id:
        # A wolf's carrier visit is not in its records (action_premises), so the morning must still
        # let the seat's known role make it (the Illusionist goes only to the pack's victim).
        return [] if view.role in visit_roles(fact, night, view, base) else None
    if fact.visitor in dead_before:
        body = dead_before[fact.visitor]
        if night == 1 or body.concealed or body.role not in BORROWED_ABILITY or NECROMANCER not in dealt:
            return None  # no body the Necromancer could act through
        return fact_constraints(ActedThroughBody(fact.visitor, fact.target), night, where, view.dead_roster, dealt)
    target_roles = base.roles.get(fact.target, dealt)
    roles = roles_that_could_visit(fact.target, night, announcement_of(view, night), dealt, target_roles,
                                   view.cast_role_counts)
    return [OnlyRoles(fact.visitor, roles, f"{RULE}+visit", where.sources)]


def visit_roles(fact: VisitAsClaimed, night: int, view: SeatView, base: Candidates) -> frozenset[str]:
    """The roles that could have made a living visitor's visit (the line's reason)."""
    dealt = _dealt(view)
    return roles_that_could_visit(fact.target, night, announcement_of(view, night), dealt,
                                  base.roles.get(fact.target, dealt), view.cast_role_counts)

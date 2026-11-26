"""The claims, read as the visits they state (catalogue Table E's preamble: typed claims, never text).

A claim states a visit in two ways: a sighting (the claimant's watch saw the visitor come to the
target, or its follow saw the visitor go there) or the visitor's own claimed action on the target.
Only the claimant's latest version counts, a night not said joins nothing (E16), and a claim that
says it was roleblocked states no visit (L13). A sighting names only what was seen: it is never
read as the whole list unless it says "no one" (L12), and these joins use only the names in it.
"""

from __future__ import annotations

from Agents.deduction.claim_view import ACTION_ROLE  # noqa: F401 (re-exported: its users import it from here)
from Agents.schemas.deduction import ActionClaim, PlayerClaimView, VisitClaim
from Agents.schemas.role_traits import ROLE_TRAITS

SIGHTINGS = ("watch", "follow")
NOT_A_VISIT = frozenset({"", "no_action", "bet", "pick", "conceal", "hold_fire"})
"""Claimed actions that are no visit to their target: a denial, the neutrals' bet and pick, the
conceal (its visit is to the pack's victim, which the claim does not name), held fire."""



def visit_claims(claims: list[PlayerClaimView]) -> list[VisitClaim]:
    """Every visit the current claims state, in the claims' order."""
    visits = []
    for player in claims:
        for claim in player.actions:
            if claim.latest and not claim.blocked and claim.night > 0:
                visits += visits_of(claim)
    return visits


def visits_of(claim: ActionClaim) -> list[VisitClaim]:
    """The visits one claim states: those it saw, and the claimant's own (only tried, when the claim
    gives no outcome: `went_ahead` False)."""
    visits = []
    if claim.action == "watch":
        visits += [VisitClaim(claim.night, seen, claim.target, claim, sighting=True, went_ahead=True)
                   for seen in claim.seen if seen not in (claim.claimant, claim.target)]
    if claim.action == "follow":
        # The followed player may have gone to the follower itself ("player_3 visited player_4", said by player_4).
        visits += [VisitClaim(claim.night, claim.target, seen, claim, sighting=True, went_ahead=True)
                   for seen in claim.seen if seen != claim.target]
    if claim.action not in NOT_A_VISIT and claim.target and claim.target != claim.claimant:
        went_ahead = claim.completed or bool(claim.seen)  # a sighting shows the watch or follow went ahead
        visits.append(VisitClaim(claim.night, claim.claimant, claim.target, claim, sighting=False,
                                 went_ahead=went_ahead))
    return visits


def claimed_role(claim: ActionClaim, claims: list[PlayerClaimView]) -> str | None:
    """The role the claimant stands on for this claim: its current role claim, else the role its
    action implies (a watch, the Sentinel); None for a visit or a kill with no role claimed. A retired
    role an old game's summary may name (the plain wolf, the villager) counts as none."""
    for player in claims:
        if player.player == claim.claimant and player.current_role in ROLE_TRAITS:
            return player.current_role
    return ACTION_ROLE.get(claim.action)

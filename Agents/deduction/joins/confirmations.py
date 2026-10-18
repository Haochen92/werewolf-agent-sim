"""Catalogue F1 (E13 extended to the seat's own actions and results, and to the wills, E12): an engine
source shows a visit that a claim also states, so that part of the claim is true, and only that part.

Joined on the night, the visitor and the target:
- the seat's own action (or a will's holder's) and another player's sighting of it: "player_9 says
  you came to player_6 on night 2. You did: …" (AC3, line 2), "player_4's will shows …, as
  player_9's watch reported" (AC4, line 2);
- a visitor the seat's watch or follow saw (or a will's), and another player's sighting of it, or
  the visitor's own claimed action on that target.
The line is certain about the visit alone: a visit shows neither the action nor the role, so the
line always says what it does not show (fold rule 2). The seat's own claims and a dead holder's
own claims are not confirmed here.
"""

from __future__ import annotations

from Agents.deduction.joins import wording
from Agents.deduction.joins.reports import claimed_role
from Agents.schemas.deduction import (
    DeductionItem,
    KnownVisit,
    PlayerClaimView,
    Source,
    VisitAsClaimed,
    VisitClaim,
)


def confirmation_items(known: list[KnownVisit], claimed: list[VisitClaim], claims: list[PlayerClaimView],
                       seat: str) -> list[DeductionItem]:
    items = []
    said = set()
    for visit in known:
        for report in claimed:
            if (report.night, report.visitor, report.target) != (visit.night, visit.visitor, visit.target):
                continue
            claimant = report.claim.claimant
            if claimant in (seat, visit.holder) or (visit.holder is not None and visit.visitor == seat):
                continue  # its own word, or a visit the seat's own record already shows
            key = (claimant, visit.night, visit.visitor, visit.target)
            if key in said:
                continue
            text = _text(visit, report, claims)
            if text is None:
                continue
            said.add(key)
            items.append(_item(visit, report, text, seat))
    return items


def _text(visit: KnownVisit, report: VisitClaim, claims: list[PlayerClaimView]) -> str | None:
    claim = report.claim
    role = claimed_role(claim, claims)
    if visit.how == "own_action":
        if not report.sighting:
            return None
        if visit.holder is None:
            return wording.you_did_as_reported(claim.claimant, claim.action, visit.target, visit.night, visit.action,
                                               role)
        return wording.holder_did_as_reported(visit.holder, visit.target, visit.night, visit.action, claim.claimant,
                                              claim.action, role)
    evidence = wording.seen_by_you(visit.how, visit.visitor, visit.target, visit.holder)
    if report.sighting:
        return wording.sighting_as_reported(claim.claimant, claim.action, visit.visitor, visit.target, visit.night,
                                            evidence, role)
    return wording.own_claim_as_reported(visit.visitor, claim.action, visit.target, visit.night, evidence, role)


def _item(visit: KnownVisit, report: VisitClaim, text: str, seat: str) -> DeductionItem:
    claimant = report.claim.claimant
    own = Source("own_record", visit.night) if visit.holder is None else Source("will", visit.night, visit.holder)
    return DeductionItem(
        row="F1", subject=claimant, night=visit.night,
        conclusion=(VisitAsClaimed(claimant, visit.visitor, visit.target, shown=report.sighting),),
        text=text, sources=(own, Source("claim", visit.night, claimant)),
        derivation=(visit.record, report.claim), receiver=seat,
    )

"""Two statements about one player's night that are about different things, or the same thing
(catalogue E1, E2a, E17).

- E2a, two places: a sighting of a player at X (a claim, or an engine watch or follow) and the
  player's own claim of an action on Y the same night. A role that acts once a night (a check, a
  protection, a watch, a follow, a shot, a sigil) goes nowhere else: the two cannot both be true
  (against an engine sighting, the claim is false). An attack, a block or a bare visit: both can be
  true only if the player is the Chanteuse carrying the pack's kill (follows if both claims are
  true); not at all when the seat knows the player is not the Chanteuse. A claimed action against
  an engine sighting with the Chanteuse possible is the conditionals' line (F5), not this one.
- E1, agreement: a claimed sighting of a player at X and the player's own claim of going to X. They
  agree, and neither shows the action. Against an engine source it is F1 (the joins).
- E17, direction, only where a careless reader could see a conflict: a player's own denial of a night
  ("I visited no one", "I did not go to X") and a watch on it that saw someone come never conflict
  (AC3, line 3); a watch on a player that saw no one says nothing about whether that player acted
  (AC4, line 5), said when the player has not denied acting that night. A claimed action beside a watch
  on its claimant is not such a pair: no line.
Only latest claims on a night said, no claim of the seat's, the player in question living.
"""

from __future__ import annotations

from Agents.deduction.comparisons import wording
from Agents.deduction.comparisons.statements import Possible, latest_claims
from Agents.deduction.night_state import deaths_before_night
from Agents.schemas.deduction import (
    ActionClaim,
    CarriedPackKill,
    ChoseAction,
    Compatible,
    DeductionItem,
    Fact,
    NoShownVisitTo,
    NotAllTrue,
    NoVisitBy,
    RoleIn,
    SeatView,
    Source,
    VisitAsClaimed,
    VisitList,
    VisitStatement,
    WentTo,
)
from Agents.schemas.role_traits import VISITS_TWO

CHANTEUSE = VISITS_TWO
ONE_VISIT_ACTIONS = frozenset({"investigate", "protect", "watch", "follow", "shoot", "sigil"})
"""Actions of a role that makes one choice a night: whoever made one went nowhere else."""
TWO_VISIT_ACTIONS = frozenset({"kill", "block", "visit"})
"""An attack, a block or a bare visit: the Chanteuse carrying the pack's kill makes two."""
OWN_ACTIONS = ONE_VISIT_ACTIONS | TWO_VISIT_ACTIONS


def own_facts(claim: ActionClaim) -> tuple[Fact, ...]:
    """A claimant's own action on its target, as facts: went ahead (an outcome said, or a bare
    visit), or only chosen (L13)."""
    if claim.action == "visit" or (claim.completed and claim.action not in ("block",)):
        return (VisitAsClaimed(claim.claimant, claim.claimant, claim.target, shown=False),)
    return (ChoseAction(claim.claimant, claim.action, claim.target, went_ahead=False),)


def _own_claims(view: SeatView, living: set[str]) -> list[ActionClaim]:
    return [claim for claim in latest_claims(view) if claim.action in OWN_ACTIONS and not claim.blocked
            and claim.target and claim.target != claim.claimant and claim.claimant in living]


def _dead_before(view: SeatView, night: int) -> set[str]:
    return {death.player for death in deaths_before_night(view.dead_roster, night)}


# --- E2a and E1 ---------------------------------------------------------------------------------

def place_items(view: SeatView, statements: list[VisitStatement], possible: Possible) -> list[DeductionItem]:
    """E2a, then E1, per sighting and the visitor's own claim."""
    n = wording.Names(view.player_id)
    living = set(view.living)
    items, said = [], set()
    for own in _own_claims(view, living):
        gone = _dead_before(view, own.night)
        if own.target in gone:
            continue
        for seen in statements:
            if (seen.night != own.night or seen.block or len(seen.visitors) != 1 or seen.visitors[0] != own.claimant
                    or seen.target in gone):
                continue
            if seen.claim is not None and (seen.claim.claimant in (own.claimant, view.player_id)
                                           or seen.claim.action not in ("watch", "follow")):
                continue
            key = (own, seen.claim or (seen.known.how, seen.known.holder, seen.visitors, seen.target))
            if key in said:
                continue
            item = (_two_places(view, n, own, seen, possible) if seen.target != own.target
                    else _agree(view, n, own, seen))
            if item is not None:
                said.add(key)
                items.append(item)
    return items


def _sighting_clause(n: wording.Names, seen: VisitStatement, first: bool) -> str:
    words = wording.when(seen.night, first)
    return wording.sighting(n, seen.claim.claimant, seen.claim.action, seen.visitors[0], seen.target, words)


def _engine_sighting(n: wording.Names, seen: VisitStatement) -> str:
    """"Your watch saw player_7 come to player_5 on night 1"."""
    known = seen.known
    text = wording.you_saw(n, known.holder, known.how, known.visitor, known.target)
    text = text.removesuffix(" that night") + f" on night {seen.night}"
    return text[0].upper() + text[1:]


def _two_places(view: SeatView, n: wording.Names, own: ActionClaim, seen: VisitStatement,
                possible: Possible) -> DeductionItem | None:
    player = own.claimant
    claim_clause = wording.own_visit(n, player, own.action, own.target, "that night")
    facts = own_facts(own)
    chanteuse = CHANTEUSE in possible(player)
    if own.action in ONE_VISIT_ACTIONS:
        reason = wording.one_visit_a_night(own.action)
        facts = (ChoseAction(player, own.action, own.target, went_ahead=False),)
    elif not chanteuse:
        reason = wording.not_the_chanteuse(player)
    elif seen.claim is None:
        return None  # the conditionals' line (F5): the claimed visits, with the seat's, make two
    else:
        text = f"{_sighting_clause(n, seen, True)}, and {claim_clause}. {wording.only_if_chanteuse(player)}"
        return _item(view, "E2a", player, own, seen, text, (RoleIn(player, frozenset({CHANTEUSE})),
                                                              CarriedPackKill(player)),
                     grade="follows_if_claims", premises=(*seen.facts, *facts))
    if seen.claim is None:
        text = wording.two_places_false(_engine_sighting(n, seen), claim_clause, reason)
        return _item(view, "E2a", player, own, seen, text, (NotAllTrue(facts),))
    text = wording.cannot_both(_sighting_clause(n, seen, True), claim_clause, reason)
    return _item(view, "E2a", player, own, seen, text, (NotAllTrue((*seen.facts, *facts)),))


def _agree(view: SeatView, n: wording.Names, own: ActionClaim, seen: VisitStatement) -> DeductionItem | None:
    if seen.claim is None:
        return None  # an engine source: the joins' line (F1)
    player = own.claimant
    text = wording.agree(_sighting_clause(n, seen, True), wording.own_visit(n, player, own.action, own.target, "that night"),
                         player, bare=own.action == "visit")
    return _item(view, "E1", player, own, seen, text, (Compatible(seen.facts, own_facts(own)),))


def _item(view: SeatView, row: str, subject: str, own: ActionClaim, seen: VisitStatement, text: str,
          conclusion: tuple[Fact, ...], grade: str = "certain", premises: tuple[Fact, ...] = ()) -> DeductionItem:
    if seen.claim is not None:
        other = Source("claim", own.night, seen.claim.claimant)
    elif seen.known.holder is not None:
        other = Source("will", own.night, seen.known.holder)
    else:
        other = Source("own_record", own.night)
    derivation = (own, seen.claim or seen.known.record)
    return DeductionItem(row=row, subject=subject, night=own.night, conclusion=conclusion, text=text, grade=grade,
                         premises=premises, sources=(Source("claim", own.night, own.claimant), other),
                         derivation=derivation, receiver=view.player_id)


# --- E17 ----------------------------------------------------------------------------------------

def direction_items(view: SeatView, lists: list[VisitList]) -> list[DeductionItem]:
    """Per watch on a living player: the player's own denial of that night against a watch that saw
    someone come, or, for a watch that saw no one and no denial, the single form."""
    n = wording.Names(view.player_id)
    living = set(view.living)
    claims = latest_claims(view)
    items = []
    for incoming in _watches(view, claims, lists):
        night, player = incoming["night"], incoming["player"]
        if player not in living or player == view.player_id:
            continue
        outgoing = _outgoing(view, n, claims, night, player)
        for out in outgoing if incoming["saw"] else ():
            if out["claim"] is not None and incoming["claim"] is not None \
                    and out["claim"].claimant == incoming["claim"].claimant:
                continue
            source = wording.incoming_source(n, incoming["claim"].claimant if incoming["claim"] else None,
                                             incoming["holder"])
            if _watched_more_than_once(claims, lists, incoming, player):
                source += f" on night {night}"
            text = wording.directions(out["text"], n(player), source)
            items.append(_direction_item(view, player, night, text, (Compatible(out["facts"], incoming["facts"]),),
                                         [out, incoming]))
        if not outgoing and incoming["claim"] is not None and incoming["claim"].seen_complete:
            claim = incoming["claim"]
            text = wording.no_one_came_is_not_inaction(
                wording.saw_no_one_come(n, claim.claimant, player, wording.when(night, True)), player)
            items.append(_direction_item(view, player, night, text, (), [incoming]))
    return items


def _watched_more_than_once(claims: list[ActionClaim], lists: list[VisitList], incoming: dict, player: str) -> bool:
    """The same watcher watched the player on more than one night: the line names which watch."""
    if incoming["claim"] is not None:
        watcher = incoming["claim"].claimant
        return len({c.night for c in claims if c.claimant == watcher and c.action == "watch" and c.target == player}) > 1
    return len({a.night for a in lists if a.kind == "to" and a.source != "claim" and a.subject == player
                and a.holder == incoming["holder"]}) > 1


def _watches(view: SeatView, claims: list[ActionClaim], lists: list[VisitList]) -> list[dict]:
    """Every watch on a player: claimed (any list), or an engine watch (the seat's, a will's)."""
    out = []
    for claim in claims:
        if claim.action == "watch" and claim.target and not claim.blocked and (claim.seen or claim.seen_complete):
            facts = ((NoShownVisitTo(claim.target, claim.claimant),) if claim.seen_complete else
                     tuple(VisitAsClaimed(claim.claimant, seen, claim.target, shown=True) for seen in claim.seen
                           if seen not in (claim.claimant, claim.target)))
            out.append({"night": claim.night, "player": claim.target, "claim": claim, "holder": None, "facts": facts,
                        "record": None, "saw": bool(facts) and not claim.seen_complete})
    for account in lists:
        if account.kind == "to" and account.source != "claim":
            out.append({"night": account.night, "player": account.subject, "claim": None, "holder": account.holder,
                        "facts": (), "record": account.record, "saw": bool(account.names)})
    return out


def _outgoing(view: SeatView, n: wording.Names, claims: list[ActionClaim], night: int, player: str) -> list[dict]:
    """The player's own denial of that night ("I visited no one", "I did not go to X"): what a careless
    reader sets against a sighting of who came to it (AC3). An action it claims is no such pair."""
    out = []
    first = wording.when(night, True)
    for claim in claims:
        if claim.night != night or claim.blocked or claim.claimant != player or claim.action != "no_action":
            continue
        if not claim.target:
            out.append({"claim": claim, "text": wording.visited_no_one(player, first), "facts": (NoVisitBy(player),)})
        else:
            out.append({"claim": claim, "text": wording.did_not_go_to(n, player, claim.target, first),
                        "facts": (NotAllTrue((WentTo(player, claim.target),)),)})
    return out


def _direction_item(view: SeatView, player: str, night: int, text: str, conclusion: tuple[Fact, ...],
                    parts: list[dict]) -> DeductionItem:
    sources, derivation = [], []
    for part in parts:
        if part.get("claim") is not None:
            sources.append(Source("claim", night, part["claim"].claimant))
            derivation.append(part["claim"])
        else:
            holder = part.get("holder")
            sources.append(Source("own_record", night) if holder is None else Source("will", night, holder))
            if part.get("record") is not None:
                derivation.append(part["record"])
    return DeductionItem(row="E17", subject=player, night=night, conclusion=conclusion, text=text,
                         sources=tuple(sources), derivation=tuple(derivation), receiver=view.player_id)

"""Level 6 of the deduction engine (slice 11): the claims against the record and against each other
(catalogue Table E; F3's claim status, E15; F7's note for an evil seat).

Comparisons are typed: they read the claims view (SeatView.claims: claimant, night, action, target,
result, sighting, attempt or completed, a whole sighting, the latest version) and the engine
sources (the morning, the roster, the wills, the seat's own records), never text. Each comparison
reads only the fields it needs: an unsaid night stops only the comparisons that join on a night
(E6 needs none), a partial sighting still names the visits it saw, and only a deduction from a name
left out needs a whole list (L12).
- statements.py: the visits each claim and each engine source states, and the whole accounts;
- conflicts.py: a stated visit against a whole account that leaves it out (E2b, E2c, E3a, E3b, E6b,
  E12, and the seat's own movements);
- pairs.py: two places in one night (E2a), a sighting and the visitor's own word (E1; E19 for a
  follow onto a watcher's target), and the two directions of a visit (E17);
- record.py: claims against the morning, the roster and the rules (E4, E6, E7, E8, E9, E11, E14, E18);
- status.py: the role claims' status (F3, E15) and role claims the seat knows are false;
- an evil seat's own lines (the claimable roles, a hidden body's role, its own visits, its covers)
  are Agents/deduction/evil/, drawn in here;
- block_visits.py: a sighting of the known Chanteuse at a player who was not the pack's victim, her
  block, against that player's roleblock claim (AC2 line 3).
The possible explanations of a claim the morning leaves open (F8, slice 12:
Agents/deduction/explanations/branches.py) are drawn here too, with the same candidate roles; they
replace Table E's conditional forms of the same claims (E4a, E8a, E8b with a branch left).
What a comparison may say (Table E): two claims that disagree cannot both be true, never which; a
claim is called false only against an engine source or what the seat knows for certain; a false
claim proves no role; a missing or withdrawn claim reserves no role. Every item goes in the seat block
(claims change with every message): the shared lines (the status, an evil seat's roles) after the
census and the role claims' conditional, the rest in the entry of the player it is about.

Left out: E5 (a save "by a reanimated healer" means the Healer was revealed dead before that night,
so any claim to be the living Healer is already false on the census: the role-claim line says it),
E10 (a claim names no side), E16 (an "insufficient information" line tells the seat only that the
engine could not check: no line), E13 (built as F1, slice 9b).
"""

from __future__ import annotations

from Agents.deduction.candidates import seat_candidates
from Agents.deduction.comparisons.block_visits import chanteuse_block_items
from Agents.deduction.comparisons.conflicts import conflict_items
from Agents.deduction.comparisons.pairs import direction_items, place_items
from Agents.deduction.comparisons.record import record_items
from Agents.deduction.comparisons.statements import claim_lists, claim_statements, engine_lists, engine_statements
from Agents.deduction.comparisons.status import role_claim_items, status_items
from Agents.deduction.evil.claimable import claimable_items
from Agents.deduction.evil.own_visits import own_visit_items
from Agents.deduction.seat_view import public_record
from Agents.deduction.self_knowledge import possible_roles
from Agents.schemas.deduction import ActionClaim, Candidates, DeductionItem, SeatView


def comparison_items(view: SeatView, today: int) -> list[DeductionItem]:
    """The shared lines first (the status, an evil seat's roles), then the comparisons."""
    if not view.living:
        return []
    candidates = seat_candidates(view)
    if candidates is None:
        return []
    items = compare(view, today, candidates)
    from Agents.deduction.evil.covers import cover_items  # it runs `compare` as a public observer

    return items[:_shared_end(items)] + cover_items(view, today) + items[_shared_end(items):]


def _shared_end(items: list[DeductionItem]) -> int:
    """Where the shared lines end: the covers go after an evil seat's roles and own-visit lines."""
    return sum(1 for item in items if item.subject is None and item.row in SHARED_ROWS)


SHARED_ROWS = frozenset({"F3+E15", "F7+E15", "F7+L8", "E2a+own", "E4b+own", "E14+own"})


def compare(view: SeatView, today: int, candidates: Candidates) -> list[DeductionItem]:
    """The comparisons on `view` with these candidate roles: the seat's own, or (covers.py) the
    public's, for an observer who knows only the public record and the claims."""

    def possible(player: str) -> frozenset[str]:
        return candidates.roles.get(player, possible_roles(player, view))

    night = _last_night(view)
    shared = status_items(view, today, night) + claimable_items(view, night) + own_visit_items(view, today, possible)
    record = public_record(view)
    if not view.claims:
        return shared + chanteuse_block_items(view, record, possible)
    statements = claim_statements(view, possible) + engine_statements(view, record, possible)
    lists = engine_lists(view, record) + claim_lists(view)
    against_record = record_items(view, today, possible)
    impossible = {item.derivation[0] for item in against_record if item.row == "E14"}
    conflicts = conflict_items(view, statements, lists)
    false = {claims[0] for item in conflicts if len(claims := _claims(item)) == 1}
    false |= {item.derivation[0] for item in against_record if item.row == "E18"}  # no "either…or" beside it
    from Agents.deduction.explanations.branches import explanation_items  # it reads this package's statements

    explanations = [item for item in explanation_items(view, possible) if not false & set(_claims(item))]
    false |= {item.derivation[0] for item in explanations if item.grade == "certain"}
    entries = [*role_claim_items(view, today, night, possible), *against_record, *explanations, *conflicts,
               *place_items(view, statements, possible), *direction_items(view, lists),
               *chanteuse_block_items(view, record, possible)]
    kept = []
    for item in entries:
        claims = _claims(item)
        if item.row != "E14" and impossible & set(claims):
            continue  # an action that could not happen: its own line says so
        if item.row == "E17" and not item.conclusion and false & set(claims):
            continue  # a watch shown false needs no reading
        if item.row == "E19" and false & set(claims):
            continue  # nor does its fit with a follow
        kept.append(item)
    return shared + kept


def _claims(item: DeductionItem) -> list[ActionClaim]:
    return [source for source in item.derivation if isinstance(source, ActionClaim)]


def _last_night(view: SeatView) -> int:
    nights = [announcement.night for announcement in view.announcements]
    nights += [death.day if death.phase == "night" else death.day - 1 for death in view.dead_roster]
    return max(nights, default=0)


__all__ = ["comparison_items"]

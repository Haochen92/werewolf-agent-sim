"""Level 3 of the deduction engine, the core: which roles each player could still hold (catalogue
Table F, "How the engine derives them"; Table C), and the census and per-player lines it gives (F3,
F7). Claims (the rest of F3, and F4 to F6) are slices 9 to 11; rendering is slice 8.

Two views, kept apart:
- the public's: the census, the public record and the public items (Agents/deduction/public/),
  nothing else, so it is the same for every seat (it will sit in the prompt's shared, cached prefix);
- one seat's: the public's, plus its own role, its own records' lines (level 1) and, for a wolf, its
  pack's roles.
Modules: constraints.py (facts and the census as role constraints), solver.py (propagation),
continuation.py (the game went on past every check), items.py (F3, F7), wording.py (the sentences).
"""

from __future__ import annotations

from Agents.deduction.candidates.constraints import Provenance, census_constraints, fact_constraints
from Agents.deduction.candidates.items import candidate_items
from Agents.deduction.candidates.solver import solve
from Agents.deduction.own_results import own_result_lines
from Agents.deduction.public import public_items
from Agents.deduction.public.known import public_view
from Agents.deduction.seat_view import public_record
from Agents.deduction.self_knowledge import known_holders
from Agents.schemas.deduction import (
    Candidates,
    DeductionItem,
    OnlyRoles,
    PublicRecord,
    RoleConstraint,
    SeatView,
    Source,
)
from Agents.schemas.game_events import DeathRecord


def public_candidates(record: PublicRecord) -> Candidates | None:
    """Every player's candidate roles as the public knows them; None when the record names no
    living players, or no legal game agrees with it."""
    if not record.living:
        return None
    return solve(record.living, record.dead_roster, record.cast_role_counts, _revealed(record.dead_roster),
                 _public_constraints(record))


def seat_candidates(view: SeatView, premise: list[RoleConstraint] = ()) -> Candidates | None:
    """Every player's candidate roles as this seat knows them. `premise`: what a conditional line
    assumes (Agents/deduction/conditionals/), added for this run only; None when no legal game
    agrees with the view and the premise together."""
    if not view.living:
        return None
    known, constraints = seat_constraints(view)
    return solve_seat(view, known, constraints + list(premise))


def seat_constraints(view: SeatView) -> tuple[dict[str, str], list[RoleConstraint]]:
    """What the seat knows outright (the revealed dead, its own role, its pack) and every constraint
    its view gives: built once, then solved with each premise in turn (the conditionals)."""
    known = {**_revealed(view.dead_roster), **view.pack_roles, view.player_id: view.role}
    return known, _public_constraints(public_record(view)) + _own_constraints(view, known)


def solve_seat(view: SeatView, known: dict[str, str], constraints: list[RoleConstraint]) -> Candidates | None:
    return solve(view.living, view.dead_roster, view.cast_role_counts, known, constraints, receiver=view.player_id)


def public_candidate_items(record: PublicRecord, informative: bool = False) -> list[DeductionItem]:
    """The public's F3 and F7 items: the same for every seat. `informative` (the deduction blocks):
    without the census clauses that name every unknown player (items.py `candidate_items`)."""
    candidates = public_candidates(record)
    if candidates is None:
        return []
    return candidate_items(candidates, record.dead_roster, _last_night(record.dead_roster, record), informative)


def seat_candidate_items(view: SeatView, informative: bool = False) -> list[DeductionItem]:
    """One seat's F3 and F7 items, from everything it knows. `informative` (the seat block): also
    without what is only the public's line less the seat and its pack."""
    candidates = seat_candidates(view)
    if candidates is None:
        return []
    record = public_record(view)
    public = public_candidates(record) if informative else None
    return candidate_items(candidates, view.dead_roster, _last_night(view.dead_roster, record), informative, public)


def _revealed(dead_roster: list[DeathRecord]) -> dict[str, str]:
    return {death.player: death.role for death in dead_roster if not death.concealed and death.role}


def _dealt(counts: dict[str, int]) -> frozenset[str]:
    return frozenset(role for role, count in counts.items() if count > 0)


def _public_constraints(record: PublicRecord) -> list[RoleConstraint]:
    """C1 and L8 on the hidden bodies, and every fact of every public item (a conditional item's
    conclusion assumes its premises, so it is not read)."""
    dealt = _dealt(record.cast_role_counts)
    constraints: list[RoleConstraint] = list(census_constraints(record.dead_roster, public_view(record), dealt))
    for item in public_items(record):
        if item.grade == "follows_if_claims":
            continue
        where = Provenance(item.row, item.sources, item.derivation)
        for fact in item.conclusion:
            constraints += fact_constraints(fact, item.night, where, record.dead_roster, dealt)
    return constraints


def _own_constraints(view: SeatView, known: dict[str, str]) -> list[RoleConstraint]:
    """Every fact on the seat's own level-1 lines, and the roles its own records prove (the pack's
    hidden victim, a target only one role could have survived as)."""
    dealt = _dealt(view.cast_role_counts)
    constraints: list[RoleConstraint] = []
    for record, line in zip(view.night_records, own_result_lines(view)):
        if line is None:
            continue
        where = Provenance(line.row, (Source("own_record", record.day, view.player_id),), (record,))
        for fact in line.facts:
            constraints += fact_constraints(fact, record.day, where, view.dead_roster, dealt)
    for player, role in known_holders(view).items():
        if player in known:
            continue
        nights = [record.day for record in view.night_records if record.target == player]
        source = Source("own_record", nights[0] if nights else 0, view.player_id)
        constraints.append(OnlyRoles(player, frozenset({role}), "own record", (source,)))
    return constraints


def _last_night(dead_roster: list[DeathRecord], record: PublicRecord) -> int:
    """The last night the record covers: the night every role-level fact is dated with."""
    nights = [announcement.night for announcement in record.announcements]
    nights += [death.day if death.phase == "night" else death.day - 1 for death in dead_roster]
    return max(nights, default=0)


__all__ = ["public_candidate_items", "public_candidates", "seat_candidate_items", "seat_candidates", "seat_constraints",
           "solve_seat"]

"""Level 2 of the deduction engine (slice 9b): the seat's own results joined with the players' claims
(catalogue Table F, F1 and F2; "Rendering", level 2).

- F1 (certain, about that part only): the seat's own record or action, or a read-out will, shows a
  visit a claim also states (confirmations.py; the roleblock cases in roleblocks.py).
- F2 (follows if the claim is true): the seat's own roleblock (or a will's) and a claim of who came
  to the door, as a complete list of explanations (roleblocks.py).
The claims are the typed claims of the seat's view (SeatView.claims, Agents/deduction/claim_view.py),
never the text. Claims change with every message, so every item here goes in the seat block, never
the cached public block, even one built from a will and a claim alone. A claim is never the premise
of a certain line: an F1 line is certain because of the engine source, and says only what that
source shows.
"""

from __future__ import annotations

from Agents.deduction.candidates import seat_candidates
from Agents.deduction.joins.confirmations import confirmation_items
from Agents.deduction.joins.known_visits import known_visits
from Agents.deduction.joins.reports import visit_claims
from Agents.deduction.joins.roleblocks import Possible, roleblock_items
from Agents.deduction.seat_view import public_record
from Agents.deduction.self_knowledge import possible_roles
from Agents.schemas.deduction import DeductionItem, SeatView


def join_items(view: SeatView) -> list[DeductionItem]:
    """The F1 and F2 items of one seat's turn: its own records first, then the wills."""
    if not view.claims:
        return []
    record = public_record(view)
    claimed = visit_claims(view.claims)
    if not claimed:
        return []
    items = confirmation_items(known_visits(view, record), claimed, view.claims, view.player_id)
    return items + roleblock_items(view, record, claimed, _possible(view))


def _possible(view: SeatView) -> Possible:
    """The seat's candidate roles per player; without the living list (a bare payload), the roles
    its own knowledge leaves (Agents/deduction/self_knowledge.py)."""
    candidates = seat_candidates(view)
    if candidates is None:
        return lambda player: possible_roles(player, view)
    return lambda player: candidates.roles.get(player, possible_roles(player, view))

"""The deduction engine: lines computed by code from what one seat knows, so that a weak model is
handed the conclusions a careful human would draw instead of having to draw them itself.

Specification, build order and status: evidence/reasoning_failures/deduction_catalogue.md.
- Every line holds in every legal game that agrees with what the seat knows, or names the claims it
  assumes, or lists every explanation. Nothing rests on hidden state: the engine reads only a
  SeatView (seat_view.py), built from the seat's own payload.
- Level 1 (own_results/) is built: what the seat's own night records imply, read with the public
  morning announcement (morning.py), shown beside them.
- Level 5 (public/) is built: what the public events and the read-out wills imply, as items
  (DeductionItem), the same for every seat.
- Level 3's core (candidates/) is built: which roles each player and hidden body could still hold,
  the public's and each seat's, and the census (F3) and per-player (F7) items.
- The blocks (blocks.py, render.py) are built: the items as two blocks, the public one before the
  prompt's cache boundary and the seat's own after it, folded by the catalogue's rules; what
  today's discussion raised is raised.py.
- The claims, typed (claim_view.py, slice 9a): every role claim, withdrawal and claimed night action
  so far, today's from the speakers' own fields, on SeatView.claims and PublicRecord.claims.
- Level 2 (joins/, slice 9b) is built: the seat's own results, and the wills, joined with the claims
  (F1, F2), in the seat block.
- Level 4 (conditionals/, slice 10) is built: the seat's propagation rerun with a premise (the
  current role claims, or one claimed night action), F4 to F6, in the seat block.
- Level 6 (comparisons/, slice 11) is built: the claims against the record and against each other
  (Table E), the role claims' status (F3, E15) and an evil seat's claimable roles, in the seat block.
- Level 7 (explanations/, slice 12) is built: a claim the morning leaves open, with every branch
  (F8, in the seat block, drawn with the comparisons), and the budgets the public counts across
  nights (F9, in the public block).

The rows read what a role is from its traits (Agents/schemas/role_traits.py: night immunity, whether
a block takes on it, whose name its visits show, whether it reads Suspicious, ...), never from its
name, except where a row is about one role and its wording names it. To add a role:
1. Give it a RoleSpec (Agents/schemas/roles.py) and a row of traits (ROLE_TRAITS).
2. Run tests/engine/deduction/test_role_traits.py: it resolves real nights and fails on any trait
   the engine disagrees with, and on a second role with a trait a row assumes only one role has
   ("only the Chanteuse blocks"); such a role needs new rows first.
3. Add catalogue rows (evidence/reasoning_failures/deduction_catalogue.md) and code only for what
   is new in its behaviour; what its traits already describe, the rows already cover.
4. Run the deduction tests and oracles with it dealt, then add it to VERIFIED_ROLES (verified.py).
   Until then a game that deals it gets no deduction.
"""

from Agents.deduction.blocks import deduction_blocks
from Agents.deduction.candidates import public_candidate_items, seat_candidate_items
from Agents.deduction.comparisons import comparison_items
from Agents.deduction.conditionals import conditional_items
from Agents.deduction.joins import join_items
from Agents.deduction.own_results import own_result_lines
from Agents.deduction.public import public_items
from Agents.deduction.render import deduction_log, fold_own_lines
from Agents.deduction.seat_view import (
    deduction_mode_for,
    deduction_placement_for,
    public_record,
    seat_view_from_payload,
)

__all__ = ["comparison_items", "conditional_items", "deduction_blocks", "deduction_log", "deduction_mode_for", "deduction_placement_for",
           "fold_own_lines", "join_items", "own_result_lines", "public_candidate_items", "public_items", "public_record", "seat_candidate_items",
           "seat_view_from_payload"]

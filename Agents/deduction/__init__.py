"""The deduction engine: lines computed by code from what one seat knows, so that a weak model is
handed the conclusions a careful human would draw instead of having to draw them itself.

Specification, build order and status: evidence/reasoning_failures/deduction_catalogue.md.
- Every line holds in every legal game that agrees with what the seat knows, or names the claims it
  assumes, or lists every explanation. Nothing rests on hidden state: the engine reads only a
  SeatView (seat_view.py), built from the seat's own payload.
- Level 1 (own_results/) is built: what the seat's own night records imply, shown beside them.
- Levels 2 to 7 (the deduction block) are not built yet.
"""

from Agents.deduction.own_results import own_result_lines
from Agents.deduction.seat_view import deduction_mode_for, seat_view_from_payload

__all__ = ["deduction_mode_for", "own_result_lines", "seat_view_from_payload"]

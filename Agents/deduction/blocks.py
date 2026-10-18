"""One turn's deduction blocks (slice 8): which engine items go to which block, from one seat's view.

The public block reads only the public record (PublicRecord), so it is the same for every seat: what
each player could still be (F7), the standing facts and the used-up budgets (F9). The seat block adds the seat's own view (its
candidate roles, which know its role, records and pack): the census (F3), its own F7 lines, its own
results joined with the claims (F1, F2: claims change with every message, so never the public block),
the conditionals on the claims (F4 to F6, one form of each fact a turn), the claims compared with the
record and with each other (Table E, the role claims' status, an evil seat's claimable roles) with the
possible explanations of a claim the morning leaves open (F8), and what today's discussion raised. The text itself is render.py's.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from Agents.deduction.candidates import public_candidate_items, seat_candidate_items
from Agents.deduction.comparisons import comparison_items
from Agents.deduction.conditionals import conditional_items, for_turn
from Agents.deduction.explanations import budget_items
from Agents.deduction.joins import join_items
from Agents.deduction.public import public_items
from Agents.deduction.raised import raised_today
from Agents.deduction.render import render_public, render_seat
from Agents.deduction.seat_view import public_record
from Agents.schemas.deduction import DeductionBlocks, DeductionItem, OwnResultLine, SeatView
from Agents.schemas.game_events import DayChannel


def deduction_blocks(view: SeatView, own_lines: Sequence[OwnResultLine | None],
                     day_channel: Iterable[DayChannel], current_day: int, vote: bool = False,
                     claims: bool = True) -> DeductionBlocks:
    """The public block and the seat block of a turn. `own_lines` are the level-1 lines shown beside
    the seat's records (one entry per record), which the seat block does not repeat. `vote`: a vote
    turn, which reads a conditional about a player as its contrapositive (fold rule 3). `claims`
    False (difficulty level 2, mode "public"): the seat block keeps only the census and the seat's
    candidate roles, what the record alone works out."""
    record = public_record(view)
    events = public_items(record)
    dead = [death.player for death in view.dead_roster]
    # The census (F3) is the seat's alone (coordinator, 2026-10-17): its version leaves out the seat and
    # its pack, so the public block keeps only what each player could be (F7) and the standing facts.
    roles_left = [item for item in public_candidate_items(record, informative=True) if item.row != "F3"]
    public = render_public([*roles_left, *events, *budget_items(record, events)], record.living, dead)
    own = [(night.day, line) for night, line in zip(view.night_records, own_lines) if line is not None]
    seat_items = seat_candidate_items(view, informative=True)
    if claims:
        joins = join_items(view)
        seat_items = [*seat_items, *joins, *for_turn(conditional_items(view), vote),
                      *_not_joined(comparison_items(view, current_day), joins)]
    seat = render_seat(seat_items, events, raised_today(day_channel, current_day), view.living, dead, public, own,
                       claims=claims)
    return DeductionBlocks(public=public, seat=seat)


def _not_joined(comparisons: list[DeductionItem], joins: list[DeductionItem]) -> list[DeductionItem]:
    """An agreement of two claims (E1) that a join already reads together (F2: "…, and player_7
    agrees. If that is true, …") is that join's to say."""
    joined = [set(map(id, item.derivation)) for item in joins]
    return [item for item in comparisons
            if item.row != "E1" or not any(set(map(id, item.derivation)) <= ids for ids in joined)]

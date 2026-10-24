"""Builds one turn's two deduction blocks for one seat: the public block and the seat block.

The public block sits in the part of the prompt every seat shares, before the cache boundary, so it
must come out the same for every seat. It is built from the public record alone: what each player
could still be, the facts the public events prove, and the abilities the record shows are used up.

The seat block sits after the boundary and belongs to this seat. It adds what only this seat can
work out from its own role and night results, and, in "full" mode, what follows from the players'
claims: the seat's own results read together with a claim, what would follow if a claim were true,
and where claims contradict the record or each other. Claims change with every message, which is the
second reason they never go in the public block.

This module only decides which items go in which block; render.py turns them into text.
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
from Agents.schemas.deduction import (
    AGREEMENT_ROWS,
    CENSUS_ROW,
    DeductionBlocks,
    DeductionItem,
    DeductionMode,
    OwnResultLine,
    SeatView,
)
from Agents.schemas.game_events import DayChannel


def deduction_blocks(view: SeatView, own_lines: Sequence[OwnResultLine | None],
                     day_channel: Iterable[DayChannel], current_day: int, vote: bool = False,
                     mode: DeductionMode = "full") -> DeductionBlocks:
    """Returns the turn's public block and seat block, each as its text and the items it shows.

    `own_lines` are the lines already printed beside the seat's own night results, one entry per
    result (None where a result has no line); the seat block does not repeat them. `day_channel` is
    the transcript: a public reasoning step is added to the seat block when a message today names
    its player and night together.

    `vote`: on a vote turn, a line like "if player_2's watch is true, player_8 is the Healer" is
    shown the other way round, "for player_8 not to be the Healer, player_2's watch must be false",
    since the vote is a decision about player_8.

    `mode` "public" leaves out every line that rests on a claim, so the seat block keeps only what
    the record alone proves; "full" includes them.
    """
    claims = mode == "full"
    record = public_record(view)
    events = public_items(record)
    dead = [death.player for death in view.dead_roster]
    
    roles_left = [item for item in public_candidate_items(record, informative=True) if item.row != CENSUS_ROW]
    public = render_public([*roles_left, *events, *budget_items(record, events)], record.living, dead)

    own = [(night.day, line) for night, line in zip(view.night_records, own_lines) if line is not None]
    seat_items = seat_candidate_items(view, informative=True)
    if claims:
        joins = join_items(view)
        seat_items = [*seat_items, *joins, *for_turn(conditional_items(view), vote),
                      *_not_joined(comparison_items(view, current_day), joins)]
    seat = render_seat(seat_items, events, raised_today(day_channel, current_day), view.living, dead, public, own,
                       mode=mode)
    return DeductionBlocks(public=public, seat=seat)


def _not_joined(comparisons: list[DeductionItem], joins: list[DeductionItem]) -> list[DeductionItem]:
    """Returns the comparisons, less any line saying two claims agree that a join already says.

    A join reads the seat's own result together with a claim, and may end "…, and player_7 agrees".
    The separate agreement line about the same two claims would repeat it. The test: every event the
    agreement line was derived from is also one the join was derived from.
    """
    joined = [set(map(id, item.derivation)) for item in joins]
    return [item for item in comparisons
            if item.row not in AGREEMENT_ROWS or not any(set(map(id, item.derivation)) <= ids for ids in joined)]

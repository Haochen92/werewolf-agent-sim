"""Level 1 of the deduction engine: what each of a seat's own night records implies.

One line per record at most, shown beside that record (or in its place, for the roleblock). Rows:
evidence/reasoning_failures/deduction_catalogue.md, Table A. Each module here covers one kind of
result and names its rows.
"""

from __future__ import annotations

from Agents.deduction.own_results.attacks import (
    immune_target_line,
    no_attack_announced_line,
    saved_from_your_attack_line,
    self_bet_saved_line,
    your_protection_saved_line,
)
from Agents.deduction.own_results.roleblock import roleblock_line
from Agents.schemas.deduction import OwnResultLine, SeatView
from Agents.schemas.game_events import NightActionRecord

ATTACKS = ("kill", "shoot")


def _line_for(record: NightActionRecord, view: SeatView) -> OwnResultLine | None:
    if record.result == "roleblocked":
        return roleblock_line(record, view)
    if record.action in ATTACKS and record.result == "immune":
        return immune_target_line(record, view)
    if record.result == "self_bet_saved":
        return self_bet_saved_line(record, view)
    if record.action in ATTACKS and record.result == "saved":
        return saved_from_your_attack_line(record, view)
    if record.action == "protect" and record.result == "saved":
        return your_protection_saved_line(record, view)
    if record.action == "protect" and record.result == "no_attack":
        return no_attack_announced_line(record, view)
    return None


def own_result_lines(view: SeatView) -> list[OwnResultLine | None]:
    """One entry per night record, in the records' order: the line it implies, or None."""
    return [_line_for(record, view) for record in view.night_records]

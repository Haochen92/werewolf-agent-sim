"""The leak boundary: what the engine may read about one seat, taken from that seat's own payload.

Every level of the engine works from a SeatView and nothing else. The payload builders already give
each seat only what it may know (Agents/nodes/day/flow.py `_private_fields`, Agents/nodes/night/solo.py
`night_turn_payload`); this module picks the fields the engine uses and puts them in one typed form.
"""

from __future__ import annotations

from typing import Any

from Agents.schemas.deduction import DeductionMode, SeatView
from Agents.schemas.game_events import DeathRecord, NightActionRecord

DEFAULT_DEDUCTION_MODE: DeductionMode = "full"
"""What a payload with no mode on it gets: a bare test, or a replay that does not set one."""


def deduction_mode_for(payload: dict[str, Any]) -> DeductionMode:
    """How much of the engine this seat gets. A human seat gets nothing, whatever the game's
    setting (owner, 2026-10-16: the human plays without machine deduction, and so does the draft
    its assistant writes)."""
    if payload.get("human_player"):
        return "off"
    return payload.get("deduction_mode") or DEFAULT_DEDUCTION_MODE


def seat_view_from_payload(payload: dict[str, Any]) -> SeatView:
    """The seat's view, from its payload. Stored games and frozen replays carry the dead roster and
    the records as plain dicts, a live game as models; both become models here."""
    dead_roster = []
    for death in payload.get("dead_roster", []):
        if isinstance(death, dict):
            death = DeathRecord.model_validate(death)
        dead_roster.append(death)

    night_records = []
    for record in payload.get("night_actions", []):
        if isinstance(record, dict):
            record = NightActionRecord.model_validate(record)
        night_records.append(record)

    return SeatView(
        player_id=payload.get("player_id", ""),
        role=payload.get("player_role", ""),
        cast_role_counts=dict(payload.get("cast_role_counts", {})),
        dead_roster=dead_roster,
        night_records=night_records,
    )

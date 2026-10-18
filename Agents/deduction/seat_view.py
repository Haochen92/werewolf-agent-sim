"""The leak boundary: what the engine may read about one seat, taken from that seat's own payload.

Every level of the engine works from a SeatView and nothing else. The payload builders already give
each seat only what it may know (Agents/nodes/day/flow.py `_private_fields`, Agents/nodes/night/solo.py
`night_turn_payload`); this module picks the fields the engine uses and puts them in one typed form.
"""

from __future__ import annotations

from typing import Any

from Agents.deduction.claim_view import claims_from_payload
from Agents.deduction.verified import roles_verified
from Agents.rules.public_prose import public_data_from_summaries
from Agents.rules.seats import seat_order
from Agents.schemas.deduction import DeductionMode, DeductionPlacement, PublicRecord, SeatView
from Agents.schemas.game_events import DeathRecord, NightActionRecord, NightAnnouncement, ReadOutWill

DEFAULT_DEDUCTION_MODE: DeductionMode = "full"
"""What a payload with no mode on it gets: a bare test, or a replay that does not set one."""


DEFAULT_DEDUCTION_PLACEMENT: DeductionPlacement = "before_note"
"""Where a payload with no placement on it puts the seat block: before the strategy note, the
cache-friendly side (the block changes at a morning or a vote, the note every turn)."""


def deduction_placement_for(payload: dict[str, Any]) -> DeductionPlacement:
    """Where this seat's own block sits, relative to its strategy note (catalogue OQ21)."""
    return payload.get("deduction_placement") or DEFAULT_DEDUCTION_PLACEMENT


def deduction_mode_for(payload: dict[str, Any]) -> DeductionMode:
    """How much of the engine this seat gets. A human seat gets nothing, whatever the game's
    setting (owner, 2026-10-16: the human plays without machine deduction, and so does the draft
    its assistant writes)."""
    if payload.get("human_player"):
        return "off"
    # A cast the engine was not verified for gets nothing rather than a possibly false line.
    if payload.get("lineup") and not roles_verified(payload["lineup"]):
        return "off"
    return payload.get("deduction_mode") or DEFAULT_DEDUCTION_MODE


def seat_view_from_payload(payload: dict[str, Any]) -> SeatView:
    """The seat's view, from its payload. Stored games and frozen replays carry the dead roster,
    the records, the mornings and the wills as plain dicts, a live game as models; all become
    models here."""
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

    # A payload from before the mornings and the wills were kept as data (a frozen replay, a stored
    # game) has neither key: both are rebuilt from the game-master prose it does carry.
    mornings_from_prose, wills_from_prose = [], []
    if "night_announcements" not in payload or "read_out_wills" not in payload:
        mornings_from_prose, wills_from_prose = public_data_from_summaries(payload.get("day_summaries", []))

    announcements = []
    for announcement in payload.get("night_announcements", mornings_from_prose):
        if isinstance(announcement, dict):
            announcement = NightAnnouncement.model_validate(announcement)
        announcements.append(announcement)

    wills = []
    for will in payload.get("read_out_wills", wills_from_prose):
        if isinstance(will, dict):
            will = ReadOutWill.model_validate(will)
        wills.append(will)

    return SeatView(
        player_id=payload.get("player_id", ""),
        role=payload.get("player_role", ""),
        cast_role_counts=dict(payload.get("cast_role_counts", {})),
        dead_roster=dead_roster,
        night_records=night_records,
        pack_roles=dict(payload.get("pack_roles", {})),
        announcements=announcements,
        wills=wills,
        living=_living(payload, dead_roster),
        claims=claims_from_payload(payload),
    )


def _living(payload: dict[str, Any], dead_roster: list[DeathRecord]) -> list[str]:
    """Every living player, the seat included, in seat order. A night turn's list leaves out the
    acting seat, a day turn's does not; a payload with no list gives none."""
    if "surviving_players" not in payload:
        return []
    dead = {death.player for death in dead_roster}
    players = set(payload["surviving_players"])
    if payload.get("player_id"):
        players.add(payload["player_id"])
    return seat_order(players - dead)


def public_record(view: SeatView) -> PublicRecord:
    """The public part of a seat's view: what every seat knows alike. The public rows read only
    this, so their items are the same whoever's payload they came from."""
    return PublicRecord(
        cast_role_counts=dict(view.cast_role_counts),
        dead_roster=list(view.dead_roster),
        announcements=list(view.announcements),
        wills=list(view.wills),
        living=list(view.living),
        claims=list(view.claims),
    )

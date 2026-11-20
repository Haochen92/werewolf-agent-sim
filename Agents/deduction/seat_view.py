"""Builds a SeatView: everything the deduction engine may know about one seat, from that seat's own payload.

This is the engine's leak boundary. Every part of the engine reads a SeatView and nothing else, so no
line it writes can rest on something the seat was not told. The payload builders already give each
seat only what it may know (Agents/nodes/day/flow.py `_private_fields`, Agents/nodes/night/solo.py
`night_turn_payload`); this module picks out the fields the engine uses and puts them in one typed
object.
"""

from __future__ import annotations

from typing import Any

from Agents.deduction.claim_view import claims_from_payload
from Agents.deduction.verified import roles_verified
from Agents.rules.public_prose import public_data_from_summaries
from Agents.rules.seats import seat_order
from Agents.schemas.deduction import DeductionMode, PublicRecord, SeatView
from Agents.schemas.game_events import DeathRecord, NightActionRecord, NightAnnouncement, ReadOutWill

DEFAULT_DEDUCTION_MODE: DeductionMode = "full"
"""What a payload with no mode on it gets: a bare test, or a replay that does not set one."""


def deduction_mode_for(payload: dict[str, Any]) -> DeductionMode:
    """Returns how much of the engine this seat gets: "off", "record", "public" or "full".

    A human seat gets "off" whatever the game's setting: the human plays on their own reasoning, and
    so does the draft message their assistant writes for them."""
    if payload.get("human_player"):
        return "off"
    # A cast the engine was not verified for gets nothing rather than a possibly false line.
    if payload.get("lineup") and not roles_verified(payload["lineup"]):
        return "off"
    return payload.get("deduction_mode") or DEFAULT_DEDUCTION_MODE


def seat_view_from_payload(payload: dict[str, Any]) -> SeatView:
    """Returns the seat's view, built from its payload alone.

    Stored games and frozen replays carry the dead roster, the night records, the mornings and the
    wills as plain dicts; a live game carries them as models. All of them come out as models."""
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

    # fallback for old games where night_announcements and wills are not part of the structured output
    # parse from day summaries instead
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
    """Returns every living player, the seat included, in seat order; [] when the payload has no list.
    A night turn's list leaves out the acting seat and a day turn's does not, so the seat is added."""
    if "surviving_players" not in payload:
        return []
    dead = {death.player for death in dead_roster}
    players = set(payload["surviving_players"])
    if payload.get("player_id"):
        players.add(payload["player_id"])
    return seat_order(players - dead)


def public_record(view: SeatView) -> PublicRecord:
    """Returns the public half of a seat's view: the fields every seat knows alike.

    The public rows read only this, so what they work out is the same whichever seat's payload it
    came from, and can go in the prompt's shared, cached prefix."""
    return PublicRecord(
        cast_role_counts=dict(view.cast_role_counts),
        dead_roster=list(view.dead_roster),
        announcements=list(view.announcements),
        wills=list(view.wills),
        living=list(view.living),
        claims=list(view.claims),
    )

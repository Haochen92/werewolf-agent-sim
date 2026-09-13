"""Who may see which event. Every durable event carries a tier (public, wolves only, one
seat, or observer), assigned in the event schema. This is the one rule that turns a tier
and a viewer's seat into yes or no. The stream route asks it per event, per viewer, at the
moment of sending, so a seat dealt after the stream opened still gets the right answer.

At game over everyone becomes an observer: the events that were held back from a viewer
during the game are sent to them then. The game_over event carries no reveal of its own;
it only flips this rule.
"""

from __future__ import annotations

from server.schemas import events as ev


def entitled(event: ev.DurableEvent, seat: str, roles: dict[str, str],
             game_over: bool) -> bool:
    """May this viewer receive this event live? ``seat`` is "" for a spectator."""
    if game_over:
        return True
    tier = ev.EVENT_TIERS[event.type]
    if tier is ev.Tier.PUBLIC:
        return True
    if tier is ev.Tier.FACTION:
        return bool(seat) and roles.get(seat) == "wolf"
    if tier is ev.Tier.SEAT:
        return bool(seat) and getattr(event, "player", None) == seat
    return False  # observer tier: in the log only, until game over unlocks it

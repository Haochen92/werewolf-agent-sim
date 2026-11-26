"""The visits an engine source shows went ahead, for the seat to set against the claims (catalogue
F1): its own actions, the visitors its own watch saw and the destinations its own follow saw, and
the same in every read-out will (L11: public from its reveal on).

- An action that went ahead on a player is a visit (L4); a roleblocked one is not (L13).
- A watch or a follow lists every visit that went ahead, under the visitor's name (L12, read through
  the L14 adapter); a dead name on it is a body the Necromancer used, not that player: left out.
- A wolf's own visit to the victim the living Illusionist concealed may be hidden from every watch
  (L4): left out, so no line confirms a sighting no watch could have made.
- The Necromancer's records show a body's name, never its own: not read here.
"""

from __future__ import annotations

from Agents.deduction.night_state import revealed_before_night
from Agents.deduction.public.known import holder_view
from Agents.deduction.records import read_record
from Agents.rules.night_record import PACK_ACTOR
from Agents.schemas.deduction import KnownVisit, PublicRecord, SeatView
from Agents.schemas.game_events import NightActionRecord
from Agents.schemas.role_traits import BODY_USER
from Agents.schemas.roles import ROLE_SPECS

VISITING_ACTIONS = frozenset({"investigate", "protect", "watch", "follow", "shoot", "kill", "sigil", "block"})
"""Actions on a player that are a visit when they go ahead (a bet, a pick, a conceal and held fire
are not, or name no player)."""


def known_visits(view: SeatView, record: PublicRecord) -> list[KnownVisit]:
    """The seat's own visits first, then each will's, in record order."""
    visits = []
    if view.role != BODY_USER:
        for own in view.night_records:
            if own.actor == view.player_id:
                visits += _visits_on_record(own, view, holder=None)
    for will in record.wills:
        holder = holder_view(record, will)
        for own in holder.night_records:
            visits += _visits_on_record(own, holder, holder=will.holder)
    return visits


def _visits_on_record(own: NightActionRecord, view: SeatView, holder: str | None) -> list[KnownVisit]:
    if own.result == "roleblocked" or own.target is None:
        return []
    visits = []
    if own.action in VISITING_ACTIONS and not _maybe_hidden(own, view):
        visits.append(KnownVisit(own.day, view.player_id, own.target, "own_action", holder, own.action, own))
    if own.action in ("watch", "follow"):
        bodies = revealed_before_night(view.dead_roster, own.day)
        for name in read_record(own, view).observed:
            if name in bodies:
                continue
            visitor, target = (name, own.target) if own.action == "watch" else (own.target, name)
            visits.append(KnownVisit(own.day, visitor, target, own.action, holder, own.action, own))
    return visits


def _maybe_hidden(own: NightActionRecord, view: SeatView) -> bool:
    """A wolf's visit to the pack's victim, when the living Illusionist concealed that victim."""
    if own.actor == PACK_ACTOR or not ROLE_SPECS[view.role].pack:
        return False
    for announcement in view.announcements:
        if announcement.night == own.day:
            return any(death.player == own.target and death.hidden_by == "illusionist"
                       for death in announcement.deaths)
    return True  # no morning on the payload: the conceal cannot be ruled out

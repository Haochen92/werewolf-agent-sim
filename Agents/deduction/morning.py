"""The public morning announcement of a given night, as the rows read it (catalogue Table B).

The engine reads the structured announcement from the seat's payload (SeatView.announcements),
never the moderator's prose. A payload from before the announcements were kept has none: every
helper here then returns None or nothing, and the rows that need the morning stay silent.
"""

from __future__ import annotations

from Agents.schemas.deduction import SeatView
from Agents.schemas.game_events import AnnouncedDeath, AnnouncedSave, NightAnnouncement
from Agents.schemas.role_traits import BODY_OF_ATTACK_TYPE, OWN_ATTACK_TYPES, announced_as, roles_acting
from Agents.schemas.roles import BORROWED_ABILITY

KILLS_THROUGH_A_BODY = frozenset(kind for kind, body in BODY_OF_ATTACK_TYPE.items() if BORROWED_ABILITY[body] == "kill")
"""The Necromancer's kills through a body: through the Illusionist's, or the Vigilante's."""


def announcement_of(view: SeatView, night: int) -> NightAnnouncement | None:
    """The morning after night `night`, or None if the seat's payload does not carry it."""
    for announcement in view.announcements:
        if announcement.night == night:
            return announcement
    return None


def death_of(announcement: NightAnnouncement, player: str) -> AnnouncedDeath | None:
    for death in announcement.deaths:
        if death.player == player:
            return death
    return None


def save_of(announcement: NightAnnouncement, player: str) -> AnnouncedSave | None:
    for save in announcement.saves:
        if save.player == player:
            return save
    return None


def attack_types(announcement: NightAnnouncement) -> set[str]:
    """Every attack type the morning named, on anyone."""
    types: set[str] = set()
    for event in [*announcement.deaths, *announcement.saves]:
        types.update(event.attacker_types)
    return types


def killed_through_a_body(announcement: NightAnnouncement) -> bool:
    """Whether the morning named an attack the Necromancer made through a body."""
    return bool(attack_types(announcement) & KILLS_THROUGH_A_BODY)


def necromancer_action_other_than_a_kill(announcement: NightAnnouncement) -> str | None:
    """The Necromancer's announced action that night when it was not a kill: a save through the
    Healer's body ("reanimated_healer") or a sigil through the Sigilist's ("reanimated_sigilist").
    It acts once a night (catalogue L10), so either one means it made no kill."""
    if any(save.saver == "reanimated_healer" for save in announcement.saves):
        return "reanimated_healer"
    if "reanimated_sigilist" in attack_types(announcement):
        return "reanimated_sigilist"
    return None


# --- where the morning places a role's one visit (shared by the conditionals' premises, the
# comparisons' E18 and the covers: one rule, so the tiers cannot disagree on it) ------------------

PLACED_BY_ATTACK = {kind: announced_as(kind) for kind in OWN_ATTACK_TYPES}
"""Whose visit an announced attack type places at its target. A wolves' attack places the carrier's
(a wolf), and the Illusionist's whether or not it carried: both its visits go to the pack's victim."""
HEALER = roles_acting("protect")[0]


def placed_visits(announcement: NightAnnouncement) -> dict[str, set[str]]:
    """Per role, the players the morning shows its visit went to that night."""
    placed: dict[str, set[str]] = {}
    for event in [*announcement.deaths, *announcement.saves]:
        for kind in event.attacker_types:
            for role in PLACED_BY_ATTACK.get(kind, ()):
                placed.setdefault(role, set()).add(event.player)
    for save in announcement.saves:
        if save.saver == "healer":
            placed.setdefault(HEALER, set()).add(save.player)
    return placed

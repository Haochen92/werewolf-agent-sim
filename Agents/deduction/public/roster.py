"""Catalogue rows B25–B27: what the dead roster and the Speculator's pick imply.

- B25: a lynch reveals the role, never hidden. In the Necromancer's casts a lynched role with an
  ability to give is a body the Necromancer can use from that night on (the day-n lynch comes
  before night n).
- B26: a pick is announced the morning after it was made: the Speculator was alive at the start of
  that night, and it picks once.
- B27: the Speculator revealed dead with no pick announced on any night it was alive (every one of
  those mornings on the payload) never picked, and has lost.
B28–B30 give no line: a bet is never announced, the census line is the candidates' level (slice
7), and a vote shows no role.
"""

from __future__ import annotations

from Agents.deduction.public import wording
from Agents.schemas.deduction import BodyUsable, DeductionItem, NeverPicked, PickMade, PublicRecord, Source
from Agents.schemas.role_traits import BODY_USER, roles_acting
from Agents.schemas.roles import BORROWED_ABILITY

SPECULATOR = roles_acting("pick")[0]
"""The role whose pick of a side the morning announces."""


def roster_items(record: PublicRecord) -> list[DeductionItem]:
    return _bodies_from_lynches(record) + _picks(record) + _never_picked(record)


def _bodies_from_lynches(record: PublicRecord) -> list[DeductionItem]:
    """B25."""
    if not record.cast_role_counts.get(BODY_USER):
        return []
    items = []
    for death in record.dead_roster:
        if death.phase != "day" or death.role not in BORROWED_ABILITY:
            continue
        items.append(DeductionItem(row="B25", subject=death.player, night=death.day,
                                   conclusion=(BodyUsable(death.player),),
                                   text=wording.body_usable_from(death.player, death.day, death.role),
                                   sources=(Source("dead_roster", death.day, death.player),), derivation=(death,)))
    return items


def _picks(record: PublicRecord) -> list[DeductionItem]:
    """B26."""
    items = []
    for announcement in record.announcements:
        if announcement.pick:
            items.append(DeductionItem(row="B26", subject=None, night=announcement.night,
                                       conclusion=(PickMade(announcement.pick),),
                                       text=wording.speculator_picked(announcement.pick, announcement.night),
                                       sources=(Source("announcement", announcement.night),),
                                       derivation=(announcement,)))
    return items


def _never_picked(record: PublicRecord) -> list[DeductionItem]:
    """B27: needs every morning up to the last night the Speculator was alive at the start of (its
    own night of death included: a pick that night is announced the same morning)."""
    death = next((d for d in record.dead_roster if d.role == SPECULATOR and not d.concealed), None)
    if death is None:
        return []
    last_night = death.day if death.phase == "night" else death.day - 1
    mornings = {announcement.night: announcement for announcement in record.announcements}
    if any(night not in mornings or mornings[night].pick for night in range(1, last_night + 1)):
        return []
    return [DeductionItem(row="B27", subject=death.player, night=max(last_night, 1),
                          conclusion=(NeverPicked(death.player),),
                          text=wording.speculator_never_picked(death.player),
                          sources=(Source("dead_roster", death.day, death.player),
                                   *(Source("announcement", night) for night in range(1, last_night + 1))),
                          derivation=(death, *(mornings[night] for night in range(1, last_night + 1))))]

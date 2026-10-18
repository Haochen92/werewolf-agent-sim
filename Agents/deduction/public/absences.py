"""Catalogue rows B13 and B14: what a morning that does not name an attack implies.

An absence proves something only when the actor was certainly alive at the start of the night and
the morning is complete (review M5): a payload with no morning for that night says nothing here.
- B13: the wolves must attack every night a wolf is alive (catalogue L5), and since R10 every
  outcome of an attack is announced except an immune target's. So with no attack by the wolves
  announced, their target was immune (the Serial Killer; the Necromancer on night 1), or, from
  night 2 in the Necromancer's casts, the Necromancer blocked the carrier through the dead
  Chanteuse's body. The Serial Killer's own attack is never silent in a legal game (it cannot hit
  an immune player), so its absence gives no line.
- B14: "No one died" (and no save) means every attack that went ahead was on an immune player.
"""

from __future__ import annotations

from Agents.deduction.night_state import revealed_before_night
from Agents.deduction.public import wording
from Agents.deduction.public.known import immune_on, types_announced, wolf_alive_at_start
from Agents.rules.night_record import PACK_ACTOR
from Agents.schemas.deduction import AttacksOnlyOn, BlockedBy, DeductionItem, PublicRecord, SilentAttack, Source
from Agents.schemas.role_traits import BLOCKER, BODY_USER


def absence_items(record: PublicRecord) -> list[DeductionItem]:
    items = []
    for announcement in record.announcements:
        night = announcement.night
        source = (Source("announcement", night),)
        if announcement.no_one_died:
            immune = immune_on(night, record)
            items.append(DeductionItem(row="B14", subject=None, night=night,
                                       conclusion=(AttacksOnlyOn(frozenset(immune)),),
                                       text=wording.no_one_died(night, immune), sources=source,
                                       derivation=(announcement,)))
        pack_item = _pack_attack_not_announced(night, record)
        if pack_item is not None:
            items.append(DeductionItem(row="B13", subject=None, night=night, conclusion=(pack_item[0],),
                                       text=pack_item[1], sources=source, derivation=(announcement,)))
    return items


def _pack_attack_not_announced(night: int, record: PublicRecord):
    """B13, the pack's clause: (fact, sentence), or None when the wolves' attack was announced, no
    wolf was certainly alive, or no legal game explains the absence."""
    announced = types_announced(night, record)
    if announced is None or "wolves" in announced or not wolf_alive_at_start(night, record):
        return None
    immune = immune_on(night, record)
    if immune:
        return SilentAttack("wolves", frozenset(immune)), wording.pack_attack_silent(night, immune)
    revealed = set(revealed_before_night(record.dead_roster, night).values())
    if record.cast_role_counts.get(BODY_USER) and BLOCKER in revealed and BODY_USER not in revealed:
        return BlockedBy(PACK_ACTOR, through_body=True), wording.pack_carrier_blocked_through_body(night)
    return None

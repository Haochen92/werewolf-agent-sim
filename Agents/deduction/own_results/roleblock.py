"""Catalogue rows A6, A7, A8: a seat that was roleblocked learns who came to it.

Only the Chanteuse blocks. While she is alive the block is hers; once she has been revealed dead,
the Necromancer can block through her body (NE casts only). A concealed Chanteuse's body cannot be
used, so a block then could not have happened at all.
"""

from __future__ import annotations

from Agents.deduction import wording
from Agents.deduction.night_state import revealed_before_night
from Agents.rules.night_record import PACK_ACTOR
from Agents.schemas.deduction import BlockedBy, OwnResultLine, SeatView
from Agents.schemas.game_events import NightActionRecord


def roleblock_line(record: NightActionRecord, view: SeatView) -> OwnResultLine | None:
    """What a "roleblocked" record implies. It replaces the record's own sentence."""
    if not view.cast_role_counts.get("chanteuse"):
        return None

    is_pack_record = record.actor == PACK_ACTOR
    chanteuse_was_dead = "chanteuse" in revealed_before_night(view.dead_roster, record.day).values()

    if chanteuse_was_dead:
        if not view.cast_role_counts.get("necromancer"):
            return None
        if is_pack_record:
            return OwnResultLine(
                text=wording.pack_carrier_blocked_through_chanteuse_body(),
                row="A8",
                replaces_outcome=True,
                facts=(BlockedBy(PACK_ACTOR, through_body=True),),
            )
        return OwnResultLine(
            text=wording.blocked_through_chanteuse_body(),
            row="A7",
            replaces_outcome=True,
            facts=(BlockedBy(view.player_id, through_body=True),),
        )

    if is_pack_record:
        # The living Chanteuse cannot block her own pack: no legal game reaches this.
        return None
    return OwnResultLine(
        text=wording.blocked_by_living_chanteuse(),
        row="A6",
        replaces_outcome=True,
        facts=(BlockedBy(view.player_id, through_body=False),),
    )

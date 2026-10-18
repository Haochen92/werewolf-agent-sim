"""Catalogue row A45: the Illusionist's conceal found no body.

A conceal hides the pack's victim only if that victim died, so "no body" means the pack's target
survived. The morning says why: a save (by the Healer, or by the Necromancer through the Healer's
body), the target's own self-bet (so it is the Fortune Teller), or nothing at all, and then the
target could not be killed that night (the Serial Killer, or the Necromancer on night 1). The
pack's target comes from the pack's own kill record that night, which every wolf holds.
"""

from __future__ import annotations

from Agents.deduction import wording
from Agents.deduction.morning import announcement_of, save_of
from Agents.deduction.night_state import IMMUNE_WHEN_SELF_BETTING, immune_candidates
from Agents.rules.night_record import PACK_ACTOR
from Agents.schemas.deduction import AttackOutcome, OwnResultLine, ProtectedBy, ReadRecord, RoleIn, SeatView


def conceal_line(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """What a conceal that found no body shows about the pack's target."""
    if record.result != "no_body":
        return None
    morning = announcement_of(view, record.night)
    target = _pack_target(record.night, view)
    if morning is None or target is None:
        return None

    save = save_of(morning, target)
    if save is not None and save.saver == "self_bet":
        return OwnResultLine(
            text=wording.pack_target_self_bet_conceal_kept(target),
            row="A45",
            facts=(RoleIn(target, frozenset({IMMUNE_WHEN_SELF_BETTING})),
                   AttackOutcome(target, frozenset({"self_bet"}))),
        )
    if save is not None:
        return OwnResultLine(
            text=wording.pack_target_saved_conceal_kept(target, save.saver),
            row="A45",
            facts=(ProtectedBy(target, through_body=save.saver == "reanimated_healer"),),
        )

    # Nothing announced: the attack failed in silence (catalogue L1).
    candidates = immune_candidates(target, record.night, view.role, view.cast_role_counts, view.dead_roster)
    if len(candidates) != 1:
        return None
    role = candidates[0]
    return OwnResultLine(
        text=wording.pack_target_immune_conceal_kept(target, role),
        row="A45",
        facts=(AttackOutcome(target, frozenset({role})), RoleIn(target, frozenset({role}))),
    )


def _pack_target(night: int, view: SeatView) -> str | None:
    """The player the pack attacked that night, from the pack's kill record; None if the pack made
    no kill that went ahead."""
    for record in view.night_records:
        if record.actor == PACK_ACTOR and record.day == night and record.action == "kill":
            if record.result == "roleblocked":
                return None
            return record.target
    return None

"""Catalogue rows A1–A5, A11–A19, A48, A53 and A54: what an attacker or a protector learns about its
target.

- An attack that went ahead and failed in silence means the target was immune: the serial killer,
  or the necromancer on nights 1 and 2 (A13–A19).
- An attack the fortune teller's self-bet stopped is announced, and names the fortune teller to the
  attacker and to a protector alike (A53, A54; R10, 2026-10-17).
- An attack stopped by a save means the target can be killed at night (A11, A12).
- A protector whose target was saved learns who attacked it (A1, with B11's attack types).
- A protector told "no attack was announced" learns that no attack reached its target, unless
  the target could have been immune (A2–A5, A48).
"""

from __future__ import annotations

from Agents.deduction import wording
from Agents.deduction.morning import announcement_of, save_of
from Agents.deduction.night_state import IMMUNE_WHEN_SELF_BETTING, immune_candidates, roles_always_immune
from Agents.schemas.deduction import AttackOutcome, OwnResultLine, ProtectedBy, RoleIn, SeatView
from Agents.schemas.game_events import NightActionRecord
from Agents.schemas.role_traits import STRUCK_BY_SIGIL, WOLF_ROLES

SIGILS = frozenset({"sigilist", "reanimated_sigilist"})
"""A sigil's attack, placed by the living Sigilist or through its body: either strikes only a
player who attacked in their own name."""


def _always_immune_other_than(own_role: str, night: int, cast_role_counts: dict[str, int]) -> list[str]:
    """The roles a saved target cannot hold, leaving out the seat's own (the serial killer knows
    its target is not itself)."""
    roles = roles_always_immune(night, cast_role_counts)
    roles.discard(own_role)
    return sorted(roles)


def immune_target_line(record: NightActionRecord, view: SeatView) -> OwnResultLine | None:
    """A13–A19: the attack went ahead and the target was unharmed, in silence. Since R10 every
    cast leaves one explanation at most (the serial killer, or the necromancer on nights 1 and 2), so the
    line names it; the "either … or" form of A14 is retired."""
    target = record.target
    candidates = immune_candidates(target, record.day, view.role, view.cast_role_counts, view.dead_roster)
    if len(candidates) != 1:
        return None

    role = candidates[0]
    return OwnResultLine(
        text=wording.target_is_the_only_immune_role(target, role),
        row="A13",
        facts=(AttackOutcome(target, frozenset({role})), RoleIn(target, frozenset({role}))),
    )


def self_bet_saved_line(record: NightActionRecord, view: SeatView) -> OwnResultLine:
    """A53 (an attacker's record), A54 (a protector's): the target survived on its own self-bet.
    Only the fortune teller can bet on itself, so the target is the fortune teller; for a
    protector, its protection saved nothing (the record says so)."""
    target = record.target
    return OwnResultLine(
        text=wording.saved_by_own_self_bet_so_fortune_teller(target),
        row="A54" if record.action == "protect" else "A53",
        facts=(RoleIn(target, frozenset({IMMUNE_WHEN_SELF_BETTING})),
               AttackOutcome(target, frozenset({"self_bet"}))),
    )


def saved_from_your_attack_line(record: NightActionRecord, view: SeatView) -> OwnResultLine | None:
    """A11, A12: the attacker's target survived because someone protected it. Who protected it
    (the living Healer, or the Necromancer through the Healer's body) is the morning's word; a
    payload with no morning leaves the protector unnamed."""
    target = record.target
    sentences = []
    facts = []

    morning = announcement_of(view, record.day)
    save = save_of(morning, target) if morning is not None else None
    saved_through_body = save is not None and save.saver == "reanimated_healer"
    if saved_through_body:
        sentences.append(wording.saved_by_necromancer_through_healer_body(target))
    if save is not None:
        facts.append(ProtectedBy(target, through_body=saved_through_body))

    ruled_out = _always_immune_other_than(view.role, record.day, view.cast_role_counts)
    if ruled_out:
        sentences.append(wording.saved_target_can_be_killed(target, ruled_out))
        facts.append(RoleIn(target, frozenset(view.cast_role_counts) - set(ruled_out)))

    if not sentences:
        return None
    return OwnResultLine(
        text=" ".join(sentences),
        row="A12" if saved_through_body else "A11",
        facts=tuple(facts),
    )


def your_protection_saved_line(record: NightActionRecord, view: SeatView) -> OwnResultLine | None:
    """A1 with B11: the protector learns its target was attacked, and by whom (the record's
    `attacker_types`; a record from before they were kept names none)."""
    target = record.target
    attacked_by_wolves = "wolves" in record.attacker_types
    struck_by_sigil = bool(SIGILS & set(record.attacker_types))

    possible_roles = set(view.cast_role_counts) - {view.role}
    sentences = []

    ruled_out = _always_immune_other_than(view.role, record.day, view.cast_role_counts)
    if ruled_out:
        sentences.append(wording.saved_target_can_be_killed(target, ruled_out))
        possible_roles -= set(ruled_out)

    if attacked_by_wolves and struck_by_sigil:
        sentences.append(wording.attacked_by_wolves_and_sigil_so_vigilante(target))
        possible_roles &= STRUCK_BY_SIGIL - WOLF_ROLES
    elif attacked_by_wolves:
        sentences.append(wording.attacked_by_wolves_so_not_a_wolf(target))
        possible_roles -= WOLF_ROLES
    elif struck_by_sigil:
        sentences.append(wording.struck_by_sigil_so_attacked_in_own_name(target))
        possible_roles &= STRUCK_BY_SIGIL

    if not sentences:
        return None
    return OwnResultLine(
        text=" ".join(sentences),
        row="A1",
        facts=(RoleIn(target, frozenset(possible_roles)),),
    )


def no_attack_announced_line(record: NightActionRecord, view: SeatView) -> OwnResultLine:
    """A2–A5, A48: no attack on the protected player was announced."""
    target = record.target
    candidates = immune_candidates(target, record.day, view.role, view.cast_role_counts, view.dead_roster)
    fact = AttackOutcome(target, frozenset(candidates))
    if not candidates:
        return OwnResultLine(text=wording.no_attack_reached(target), row="A4", facts=(fact,))
    return OwnResultLine(
        text=wording.no_attack_reached_or_immune(target, candidates),
        row="A2",
        grade="possible",
        facts=(fact,),
    )

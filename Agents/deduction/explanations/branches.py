"""Catalogue F8 (level 7): a claim that agrees with the record only on some branches, with every branch
(§0 grade 3: a complete list, the claim being false always one of them).

A claimed action leaves a trace in the morning when it goes ahead. When the trace is missing, the ways
the action could have ended are read off the engine's rules, never written per case (the tables
below), and kept when the morning, the claim's own words and the seat's knowledge all leave them open:
- a shot: roleblocked (no attack at all, catalogue L13); gone ahead on a target that cannot be killed
  that night (silent: the Serial Killer, the Necromancer on night 1; L1 since R10); or gone ahead and
  killed, or saved by the Healer, a reanimated healer or the target's own self-bet, each announced
  with the shot's type (B4, B11, B12, B33), so shut when the morning names no shot at the target;
- a protection of a player who died that night: roleblocked; or gone ahead, which stops every attack
  (A1), so shut by the death;
- a watch that saw no one, against the visits the morning shows came to the watched player: each
  attack under its maker's name, the living Healer's save, the Necromancer's under a body's name (B1,
  B3–B9, B11, B12), every one on a watch's list but the pack's killer at a victim the living
  Illusionist hid, and the Illusionist's own visit there when it carried the kill itself (L4, R5).
A branch the claim's words rule out goes (a shot it says went ahead was not roleblocked), and so does
one the seat knows cannot be (no one could roleblock that night; the target cannot hold an immune
role; the claimant cannot hold the role that makes the action). One branch or more left: the list,
the claim being false last. None left: the claim is false, a certain line.

These replace Table E's conditional forms of the same claims (E4a, E8a, E8b with a branch left): "If
player_4 shot at player_9, either A or B" and "either A, or B, or player_4's claim is false" are one
proposition, so the engine says it once, as the list, which names the claim-false branch a weak
reader does not derive from a conditional (fold rule 3). E4b and E8b's certain forms stay Table E's.
The claimant's own record is its own certain line (level 1): its own claims are never read here.
"""

from __future__ import annotations

from Agents.deduction.comparisons import wording as claim_wording
from Agents.deduction.comparisons.statements import Possible, blocked_fact, blockers, latest_claims
from Agents.deduction.explanations import wording
from Agents.deduction.joins.reports import ACTION_ROLE
from Agents.deduction.morning import announcement_of, death_of, save_of
from Agents.deduction.night_state import deaths_before_night, roles_always_immune
from Agents.deduction.public.known import body_of
from Agents.deduction.seat_view import public_record
from Agents.schemas.deduction import (
    ActionClaim,
    AnyOf,
    Branch,
    CarriedOrAmong,
    ChoseAction,
    DeductionItem,
    Fact,
    NoShownVisitTo,
    NotAllTrue,
    RoleIn,
    SeatView,
    Source,
)
from Agents.schemas.game_events import NightAnnouncement
from Agents.schemas.role_traits import BODY_OF_ATTACK_TYPE, roles_acting
from Agents.schemas.roles import ROLE_SPECS

HEALER = roles_acting("protect")[0]
ILLUSIONIST = roles_acting("conceal")[0]
MAKER = {action: ACTION_ROLE[action] for action in ("shoot", "protect", "watch")}
"""The one role whose own action the claim states (under its own name, not through a body)."""
SHOT_TYPES = frozenset({"vigilante", "reanimated_vigilante"})
"""The attack types a shot is announced as (a reanimated vigilante's is the Necromancer's, through
the body; the claim ledger and E8 read either as the shot's trace)."""
SAVE_RESULTS = frozenset({"saved_from_attack", "no_attack"})
"""A protection's results that say it went ahead (E4b's)."""
BODY_OF_TYPE = {**BODY_OF_ATTACK_TYPE, "reanimated_healer": HEALER}
"""The role whose body each reanimated attack, or a save through a body, was made through."""

ATTACK_ENDINGS = (
    # (ending, announced with the attack's type, the attack went ahead)
    ("roleblocked", False, False),
    ("immune", False, True),
    ("killed", True, True),
    ("saved_by_the_healer", True, True),
    ("saved_by_a_reanimated_healer", True, True),
    ("saved_by_its_own_self_bet", True, True),
)
"""Every way an attack someone chose can end (catalogue L1, L13, A1, B11, B12, B33)."""
PROTECTION_ENDINGS = (
    # (ending, the protected player can die that night)
    ("roleblocked", True),
    ("went_ahead", False),
)
"""Every way a protection someone chose can end: a protection that goes ahead beats every attack."""


def explanation_items(view: SeatView, possible: Possible) -> list[DeductionItem]:
    """One line per claim of another living player, on a night said, that the morning leaves open
    or shows false; nothing for a claim the record shows (a shot announced at its target) or says
    nothing about."""
    items = []
    living = set(view.living)
    for claim in latest_claims(view):
        if claim.claimant not in living or claim.blocked or not claim.target or claim.target == claim.claimant:
            continue
        announcement = announcement_of(view, claim.night)
        if announcement is None or claim.target in _dead_before(view, claim.night):
            continue  # no morning to read, or a target already dead (E14 says so)
        reader = {"shoot": _shot, "protect": _protection, "watch": _no_one_came}.get(claim.action)
        item = reader(view, claim, announcement, possible) if reader else None
        if item is not None:
            items.append(item)
    return items


def _dead_before(view: SeatView, night: int) -> set[str]:
    return {death.player for death in deaths_before_night(view.dead_roster, night)}


def _could_be_blocked(view: SeatView, claim: ActionClaim, possible: Possible) -> bool:
    """Someone other than the claimant could have roleblocked it that night (the Chanteuse never blocks
    herself, and is never blocked)."""
    return any(name != claim.claimant for name in blockers(view, claim.night, possible))


def _types_on(announcement: NightAnnouncement, player: str) -> set[str]:
    return {kind for event in (death_of(announcement, player), save_of(announcement, player)) if event
            for kind in event.attacker_types}


# --- the shot --------------------------------------------------------------------------------------

def _shot(view: SeatView, claim: ActionClaim, announcement: NightAnnouncement, possible: Possible) -> DeductionItem | None:
    target, night = claim.target, claim.night
    if SHOT_TYPES & _types_on(announcement, target) or claim.result == "died":
        return None  # the morning shows the shot, or it says the target died: Table E's (E8b)
    went = claim.result == "survived"
    silent = [role for role in ROLE_SPECS if role in roles_always_immune(night, view.cast_role_counts)]
    immune = [role for role in silent if role in possible(target)]
    if target == view.player_id and immune:
        return None  # the seat cannot be killed that night: the claim fits what it knows
    if went and not immune:
        return None  # gone ahead, with nothing to fail on in silence: E8b says it is false
    branches, shut = [], []
    for ending, announced, went_ahead in ATTACK_ENDINGS:
        if announced or (went and not went_ahead):
            continue  # the morning names no shot at the target; the claim says it went ahead
        if ending == "roleblocked":
            if _could_be_blocked(view, claim, possible):
                branches.append(Branch(wording.roleblocked(claim.claimant), (blocked_fact(claim.claimant),)))
            else:
                shut.append(wording.no_blocker())
        elif ending == "immune":
            if immune:
                branches.append(Branch(wording.immune_holder(target, immune), (RoleIn(target, frozenset(immune)),)))
            else:
                shut.append(wording.not_immune(target, silent))
    n = claim_wording.Names(view.player_id)
    clause = (f"{claim.claimant} says its shot at {n(target)} went ahead on night {night}" if went
              else claim_wording.own_visit(n, claim.claimant, "shoot", target, claim_wording.when(night, True)))
    chosen = (ChoseAction(claim.claimant, "shoot", target, went_ahead=went),)
    return _line(view, claim, announcement, clause, wording.no_shot_announced(n(target)), branches, shut,
                 chosen, "claim", possible)


# --- the protection --------------------------------------------------------------------------------

def _protection(view: SeatView, claim: ActionClaim, announcement: NightAnnouncement,
                possible: Possible) -> DeductionItem | None:
    target, night = claim.target, claim.night
    if death_of(announcement, target) is None or claim.result in SAVE_RESULTS:
        return None  # the protected player lived (the claim fits), or the claim says it went ahead (E4b)
    branches, shut = [], []
    for ending, can_die in PROTECTION_ENDINGS:
        if not can_die:
            continue  # the death shuts it
        if _could_be_blocked(view, claim, possible):
            branches.append(Branch(wording.roleblocked(claim.claimant), (blocked_fact(claim.claimant),)))
        else:
            shut.append(wording.no_blocker())
    n = claim_wording.Names(view.player_id)
    clause = claim_wording.own_visit(n, claim.claimant, "protect", target, claim_wording.when(night, True))
    return _line(view, claim, announcement, clause, wording.died_despite_protection(n(target)), branches, shut,
                 (ChoseAction(claim.claimant, "protect", target),), "claim", possible)


# --- the watch that saw no one ---------------------------------------------------------------------

def _no_one_came(view: SeatView, claim: ActionClaim, announcement: NightAnnouncement,
                 possible: Possible) -> DeductionItem | None:
    if not claim.seen_complete or claim.seen:
        return None  # a named list is partial (L12): it rules no visitor out
    n = claim_wording.Names(view.player_id)
    target, night = claim.target, claim.night
    visits = _shown_visits(view, announcement, n(target), target)
    if not visits:
        return None  # the morning shows no visit to the watched player
    clause = claim_wording.saw_no_one_come(n, claim.claimant, target, claim_wording.when(night, True))
    claimed = (ChoseAction(claim.claimant, "watch", target, went_ahead=True), NoShownVisitTo(target, claim.claimant))
    certain = next((text for text, hidden in visits if hidden is None), None)
    if certain is not None:
        return _line(view, claim, announcement, clause, certain, [], [], claimed, "report", possible)
    text, hidden = visits[0]
    return _line(view, claim, announcement, clause, text, [hidden], [], claimed, "report", possible)


def _shown_visits(view: SeatView, announcement: NightAnnouncement, name: str,
                  target: str) -> list[tuple[str, Branch | None]]:
    """Each visit the morning shows came to `target` that night, with the one way a watch could miss
    it (None: it is on every watch's list)."""
    record = public_record(view)
    night = announcement.night
    visits: list[tuple[str, Branch | None]] = []
    death, save = death_of(announcement, target), save_of(announcement, target)
    for event in (death, save):
        if event is None:
            continue
        concealed = event is death and death.hidden_by == "illusionist"
        for kind in event.attacker_types:
            if kind == "wolves" and concealed:
                # The killer's visit is hidden; the Illusionist's conceal is not, unless it is the killer.
                visits.append((wording.conceal_visit(name), Branch(wording.illusionist_carried(),
                                                                   (CarriedOrAmong(ILLUSIONIST, ()),))))
            elif kind in wording.VISITOR:
                visits.append((wording.came_and_shows(wording.VISITOR[kind], name), None))
            elif kind in BODY_OF_TYPE and (body := body_of(BODY_OF_TYPE[kind], night, record)):
                visits.append((wording.came_through_body(body, name), None))
    if save is not None and save.saver == "healer":
        visits.append((wording.came_and_shows(wording.VISITOR["healer"], name), None))
    elif save is not None and save.saver == "reanimated_healer" and (body := body_of(HEALER, night, record)):
        visits.append((wording.came_through_body(body, name), None))
    return visits


# --- the line --------------------------------------------------------------------------------------

def _line(view: SeatView, claim: ActionClaim, announcement: NightAnnouncement, clause: str, observation: str,
          branches: list[Branch], shut: list[str], claimed: tuple[Fact, ...], kind: str,
          possible: Possible) -> DeductionItem:
    role = MAKER[claim.action]
    if branches and role not in possible(claim.claimant):
        branches, shut = [], [wording.cannot_be(claim.claimant, role, claim.action, view.role == role)]
    false = NotAllTrue(claimed)
    if branches:
        text = wording.explained(clause, observation, [branch.text for branch in branches], claim.claimant, kind)
        conclusion: tuple[Fact, ...] = (AnyOf((*(branch.facts for branch in branches), (false,))),)
        grade = "possible"
    else:
        text = wording.is_false(clause, observation, shut, kind)
        conclusion, grade = (false,), "certain"
    sources = (Source("claim", claim.night, claim.claimant), Source("announcement", claim.night, claim.target))
    return DeductionItem(row="F8", subject=claim.claimant, night=claim.night, conclusion=conclusion, text=text,
                         grade=grade, sources=sources, derivation=(claim, announcement), receiver=view.player_id)

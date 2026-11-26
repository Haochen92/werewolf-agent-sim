"""Claims against the record and the rules (catalogue E4, E6, E7, E8, E9, E11, E14).

- E14, an action that could not happen: on a player already dead when the night began; a sighting of
  a dead name the Necromancer could not have used; a roleblock after the Chanteuse died, in a cast
  with no Necromancer to block through her body; the Healer protecting itself.
- E4, a protection of a player who died that night: a protection that goes ahead stops every attack
  (immunity over protection over death). Said to have gone ahead: false (E4b). Only chosen: the
  possible explanations (F8, slice 12: Agents/deduction/explanations/branches.py, which replaced E4a).
- E6, a roleblock and a claimed role that cannot be roleblocked (the Serial Killer, the Necromancer,
  the neutrals, and the Chanteuse, who is never blocked in a legal game: L3).
- E7, a claimed check against the target's role as the seat knows it (revealed, its own, its
  pack's, or every role left to the target): one reading is impossible. The Necromancer reads
  Suspicious only on a night it killed through a body, which the morning shows (no silent immune
  target in a Necromancer cast since R10).
- E8, a claimed shot with no shot at its target announced that night: a claimed kill is false, and so
  is a shot said to have gone ahead at a target that cannot fail one in silence (E8b). Only chosen,
  or gone ahead at a target that could be immune: the possible explanations (F8, which replaced E8a
  and E8b's conditional form).
- E9, a sigil said to have struck its target down, with no sigil attack on that death.
- E11, more completed checks, watches or sigils than the role has.
- E18 (owner, 2026-10-18), a claimed protection, sigil or shot on a player other than the one the
  morning places that role's one visit at: the Healer's save, the Sigilist's strike, the Vigilante's
  shot (morning.py `placed_visits`, the rule the conditionals' premises use). The role is dealt once
  and acts once a night, so the claim is false. Before it the town's lines said nothing to "I'm the
  Healer, I protected player_2" on a night the Healer's save was announced on player_5.
What the claim ledger already checks for a claim it shows (a claim said before today: the ledger in
the prompt covers the days before today) is left to it: a check against a revealed role, a claimed
save with no save announced, a claimed kill of a player who did not die, a self-protection.
"""

from __future__ import annotations

from Agents.deduction.comparisons import wording
from Agents.deduction.comparisons.statements import Possible, blocked_fact, latest_claims
from Agents.deduction.joins.reports import ACTION_ROLE
from Agents.deduction.morning import announcement_of, death_of, killed_through_a_body, placed_visits, save_of
from Agents.deduction.night_state import deaths_before_night, roles_always_immune
from Agents.schemas.deduction import (
    ActionClaim,
    CheckRead,
    ChoseAction,
    DeductionItem,
    DiedBy,
    Fact,
    NotAllTrue,
    OnNight,
    RoleIn,
    SeatView,
    Source,
    VisitAsClaimed,
)
from Agents.schemas.game_events import DeathRecord
from Agents.schemas.role_traits import BLOCKER, BODY_USER, SUSPICIOUS_THROUGH_A_BODY, UNBLOCKABLE, WOLF_ROLES
from Agents.schemas.roles import BORROWED_ABILITY, ROLE_SPECS

CHANTEUSE = BLOCKER
NECROMANCER = BODY_USER
TARGETED = frozenset({"investigate", "protect", "watch", "follow", "shoot", "kill", "sigil", "block", "visit"})
"""Claimed actions on a living player."""
LIMITED = {action: ACTION_ROLE[action] for action in ("investigate", "watch", "sigil")}
"""Actions whose uses the cards state (catalogue §0, configuration scope), by the role that has them."""
SAVE_RESULTS = frozenset({"saved_from_attack", "no_attack"})
"""A protection's results that say it went ahead."""


def record_items(view: SeatView, today: int, possible: Possible) -> list[DeductionItem]:
    items: list[DeductionItem] = []
    living = set(view.living)
    for claim in latest_claims(view):
        if claim.claimant in living:
            items += claim_items(view, claim, today, possible)
    items += _unblockable(view, living)
    items += _too_many(view, living)
    return items


def claim_items(view: SeatView, claim: ActionClaim, today: int, possible: Possible) -> list[DeductionItem]:
    """One claimed action against the morning, the roster and the rules: an action that could not
    happen (E14) says only that. Also run on an evil seat's own visits, as claims it might make
    (Agents/deduction/evil/own_visits.py)."""
    impossible = _impossible(view, claim, _dead_before(view, claim.night), today)
    if impossible:
        return impossible
    if claim.action == "protect" and not claim.blocked:
        items = _protection(view, claim, today, possible)
    elif claim.action == "investigate" and claim.result in ("suspicious", "not_suspicious"):
        items = _check(view, claim, today, possible)
    elif claim.action == "shoot" and not claim.blocked:
        items = _shot(view, claim, today, possible)
    elif claim.action == "sigil" and claim.result == "died":
        items = _sigil(view, claim)
    else:
        items = []
    certain = [item for item in items if item.grade == "certain"]
    # E18 only where no row already calls the claim false (E4b keeps a protection of the dead); it
    # replaces an open "either…or" (F8, drawn later) the morning settles.
    return certain or _placed_elsewhere(view, claim) or items


def _dead_before(view: SeatView, night: int) -> dict[str, DeathRecord]:
    return {death.player: death for death in deaths_before_night(view.dead_roster, night)}


def _died_that_night(view: SeatView, night: int) -> set[str]:
    return {death.player for death in view.dead_roster if death.phase == "night" and death.day == night}


def _item(view: SeatView, row: str, claim: ActionClaim, text: str, conclusion: tuple[Fact, ...],
          grade: str = "certain", premises: tuple[Fact, ...] = (), kind: str = "announcement") -> DeductionItem:
    sources = (Source("claim", claim.night, claim.claimant), Source(kind, claim.night))
    return DeductionItem(row=row, subject=claim.claimant, night=claim.night, conclusion=conclusion, text=text,
                         grade=grade, premises=premises, sources=sources, derivation=(claim,), receiver=view.player_id)


def _claim_clause(n: wording.Names, claim: ActionClaim) -> str:
    words = wording.when(claim.night, True)
    if claim.blocked:
        return wording.roleblocked(claim.claimant, words)
    return wording.own_visit(n, claim.claimant, claim.action, claim.target, words)


def _chosen(claim: ActionClaim) -> Fact:
    if claim.action == "visit":
        return VisitAsClaimed(claim.claimant, claim.claimant, claim.target, shown=False)
    return ChoseAction(claim.claimant, claim.action, claim.target)


# --- E14 ----------------------------------------------------------------------------------------

def _impossible(view: SeatView, claim: ActionClaim, dead: dict[str, DeathRecord], today: int) -> list[DeductionItem]:
    n = wording.Names(view.player_id)
    if claim.blocked:
        return _no_blocker(view, n, claim, dead)
    if claim.action in TARGETED and claim.target in dead:
        death = dead[claim.target]
        text = wording.target_already_dead(_claim_clause(n, claim), claim.target, wording.death_words(death.phase, death.day))
        return [_item(view, "E14", claim, text, (NotAllTrue((_chosen(claim),)),), kind="dead_roster")]
    if claim.action == "protect" and claim.target == claim.claimant and claim.day >= today:
        return [_item(view, "E14", claim, wording.self_protection(claim.claimant, claim.night),
                      (NotAllTrue((ChoseAction(claim.claimant, "protect", claim.claimant),)),), kind="claim")]
    items = []
    if claim.action in ("watch", "follow"):
        for seen in claim.seen:
            if seen in (claim.claimant, claim.target):
                continue
            visitor, target = (seen, claim.target) if claim.action == "watch" else (claim.target, seen)
            dead_name = visitor if claim.action == "watch" else target
            if dead_name not in dead or (claim.action == "watch" and _body_usable(view, dead[dead_name], claim.night)):
                continue
            death = dead[dead_name]
            clause = wording.sighting(n, claim.claimant, claim.action, visitor, target, wording.when(claim.night, True))
            how = wording.death_words(death.phase, death.day)
            text = (wording.visitor_already_dead(clause, dead_name, how, bool(view.cast_role_counts.get(NECROMANCER)))
                    if claim.action == "watch"
                    else wording.target_already_dead(clause, dead_name, how).replace("that claim", "that report"))
            items.append(_item(view, "E14", claim, text,
                               (NotAllTrue((VisitAsClaimed(claim.claimant, visitor, target, shown=True),)),),
                               kind="dead_roster"))
            break
    return items


def _body_usable(view: SeatView, death: DeathRecord, night: int) -> bool:
    return (night >= 2 and bool(view.cast_role_counts.get(NECROMANCER)) and not death.concealed
            and death.role in BORROWED_ABILITY)


def _no_blocker(view: SeatView, n: wording.Names, claim: ActionClaim, dead: dict[str, DeathRecord]) -> list[DeductionItem]:
    """A roleblock claimed after the Chanteuse was revealed dead, in a cast with no Necromancer."""
    if view.cast_role_counts.get(NECROMANCER) or not view.cast_role_counts.get(CHANTEUSE):
        return []
    chanteuse = next((death for death in dead.values() if death.role == CHANTEUSE and not death.concealed), None)
    if chanteuse is None:
        return []
    text = wording.no_blocker_left(_claim_clause(n, claim), chanteuse.player,
                                   wording.death_words(chanteuse.phase, chanteuse.day))
    return [_item(view, "E14", claim, text, (NotAllTrue((blocked_fact(claim.claimant),)),), kind="dead_roster")]


# --- E4 -----------------------------------------------------------------------------------------

def _protection(view: SeatView, claim: ActionClaim, today: int, possible: Possible) -> list[DeductionItem]:
    if not claim.target or claim.target == claim.claimant or claim.target not in _died_that_night(view, claim.night):
        return []
    if claim.result in SAVE_RESULTS:
        if claim.result == "saved_from_attack" and claim.day < today:
            return []  # the ledger: "no save of the target was announced that night"
        text = wording.protection_went_ahead_but_died(claim.claimant, claim.target, claim.night)
        return [_item(view, "E4b", claim, text,
                      (NotAllTrue((ChoseAction(claim.claimant, "protect", claim.target, went_ahead=True),)),),
                      kind="dead_roster")]
    return []  # only chosen: F8's list (Agents/deduction/explanations/branches.py)


# --- E18 ----------------------------------------------------------------------------------------

PLACED_ACTIONS = {"protect": "healer", "sigil": "sigilist", "shoot": "vigilante"}
"""The actions whose one visit a night the morning can place: the save, the strike, the shot."""


def _placed_elsewhere(view: SeatView, claim: ActionClaim) -> list[DeductionItem]:
    role = PLACED_ACTIONS.get(claim.action)
    announcement = announcement_of(view, claim.night)
    if role is None or claim.blocked or not claim.target or announcement is None or view.cast_role_counts.get(role) != 1:
        return []
    placed = placed_visits(announcement).get(role, set())
    if not placed or claim.target in placed:
        return []
    n = wording.Names(view.player_id)
    text = wording.placed_elsewhere(n, claim.claimant, claim.action, claim.target, claim.night, role, sorted(placed))
    return [_item(view, "E18", claim, text,
                  (NotAllTrue((OnNight(claim.night, ChoseAction(claim.claimant, claim.action, claim.target)),)),))]


# --- E7 -----------------------------------------------------------------------------------------

def _check(view: SeatView, claim: ActionClaim, today: int, possible: Possible) -> list[DeductionItem]:
    target, night = claim.target, claim.night
    if not target or target == claim.claimant:
        return []
    revealed = next((death for death in view.dead_roster if death.player == target and death.role
                     and not death.concealed), None)
    if revealed is not None and (claim.day < today or revealed.role == SUSPICIOUS_THROUGH_A_BODY):
        return []  # the ledger checks a check against a revealed role
    roles = possible(target)
    suspicious_roles = set(WOLF_ROLES)
    if SUSPICIOUS_THROUGH_A_BODY in roles:
        announcement = announcement_of(view, night)
        if announcement is None:
            return []
        if killed_through_a_body(announcement):
            suspicious_roles.add(SUSPICIOUS_THROUGH_A_BODY)
    said = claim.result == "suspicious"
    if said and roles & suspicious_roles or not said and not roles <= suspicious_roles:
        return []
    n = wording.Names(view.player_id)
    if target == view.player_id:
        reason = wording.you_read(view.role, not said)
    elif target in view.pack_roles:
        reason = wording.packmate_reads(target, view.pack_roles[target])
    elif revealed is not None:
        reason = wording.revealed_reads(target, revealed.role, not said)
    else:
        reason = wording.can_only_be_reads(target, [role for role in ROLE_SPECS if role in roles], said)
    text = wording.check_reading_false(n, claim.claimant, target, night, said, reason)
    return [_item(view, "E7", claim, text, (NotAllTrue((CheckRead(claim.claimant, target, said),)),),
                  kind="own_record")]


# --- E8 -----------------------------------------------------------------------------------------

def _shot(view: SeatView, claim: ActionClaim, today: int, possible: Possible) -> list[DeductionItem]:
    target, night = claim.target, claim.night
    announcement = announcement_of(view, night)
    if not target or target == claim.claimant or announcement is None:
        return []
    announced = [event for event in (death_of(announcement, target), save_of(announcement, target)) if event]
    if any({"vigilante", "reanimated_vigilante"} & set(event.attacker_types) for event in announced):
        return []
    immune = [role for role in ROLE_SPECS if role in roles_always_immune(night, view.cast_role_counts)
              and role in possible(target)]
    went_ahead = ChoseAction(claim.claimant, "shoot", target, went_ahead=True)
    if claim.result == "died":
        if claim.day < today and death_of(announcement, target) is None:
            return []  # the ledger: "the target did not die that night"
        text = wording.shot_went_ahead_false(claim.claimant, target, night, killed=True)
        return [_item(view, "E8b", claim, text, (NotAllTrue((DiedBy(target, "vigilante"),)),))]
    if claim.result == "survived" and not immune:
        silent = [role for role in ROLE_SPECS if role in roles_always_immune(night, view.cast_role_counts)]
        text = wording.shot_went_ahead_false(claim.claimant, target, night, killed=False, silent=silent)
        return [_item(view, "E8b", claim, text, (NotAllTrue((went_ahead,)),))]
    return []  # only chosen, or gone ahead at a target that could be immune: F8's list


# --- E9 -----------------------------------------------------------------------------------------

def _sigil(view: SeatView, claim: ActionClaim) -> list[DeductionItem]:
    target, night = claim.target, claim.night
    announcement = announcement_of(view, night)
    if not target or announcement is None:
        return []
    death = death_of(announcement, target)
    if death is not None and {"sigilist", "reanimated_sigilist"} & set(death.attacker_types):
        return []
    text = wording.sigil_struck_false(claim.claimant, target, night)
    return [_item(view, "E9", claim, text, (NotAllTrue((DiedBy(target, "sigilist"),)),))]


# --- E6 -----------------------------------------------------------------------------------------

def _unblockable(view: SeatView, living: set[str]) -> list[DeductionItem]:
    items = []
    for player in view.claims:
        role = player.current_role
        if player.player == view.player_id or player.player not in living or role not in ROLE_SPECS \
                or not view.cast_role_counts.get(role) or (role not in UNBLOCKABLE and role != CHANTEUSE):
            continue
        for claim in player.actions:
            if claim.latest and claim.blocked:
                text = wording.unblockable(player.player, role, claim.night)
                conclusion = (NotAllTrue((RoleIn(player.player, frozenset({role})), blocked_fact(player.player))),)
                items.append(DeductionItem(row="E6", subject=player.player, night=claim.night, conclusion=conclusion,
                                           text=text, sources=(Source("claim", claim.night, player.player),),
                                           derivation=(claim,), receiver=view.player_id))
                break
    return items


# --- E11 ----------------------------------------------------------------------------------------

def _too_many(view: SeatView, living: set[str]) -> list[DeductionItem]:
    from Agents.config.game import GameConfig  # the config package imports the prompts, which import this

    uses = GameConfig().starting_uses()
    items = []
    for player in view.claims:
        if player.player == view.player_id or player.player not in living or player.current_role == NECROMANCER:
            continue
        for action, role in LIMITED.items():
            if not view.cast_role_counts.get(role):
                continue
            done: dict[int, ActionClaim] = {}
            for claim in player.actions:
                went = claim.completed or (action == "watch" and bool(claim.seen))
                if claim.latest and claim.action == action and claim.night > 0 and claim.target and went:
                    done.setdefault(claim.night, claim)
            if len(done) <= uses[role]:
                continue
            nights = sorted(done)
            text = wording.too_many_uses(player.player, action, nights, role, uses[role])
            facts = tuple(OnNight(night, ChoseAction(player.player, action, done[night].target, went_ahead=True))
                          for night in nights)
            items.append(DeductionItem(row="E11", subject=player.player, night=nights[-1],
                                       conclusion=(NotAllTrue(facts),), text=text,
                                       sources=tuple(Source("claim", night, player.player) for night in nights),
                                       derivation=tuple(done[night] for night in nights), receiver=view.player_id))
    return items

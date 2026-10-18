"""An evil seat's covers (slice 14; ruling R11, owner 2026-10-18: evil seats claim, they never deny a
sighting; "Stories yes"): for each town role the seat can claim, the night story that fits its real
nights and every claim made so far, or that it would start a counter-claim.

The story names the seat's real visits, so no watch or follow, reported or not, can contradict it: on
each of the last two nights, a visit a watch or a follow could show becomes that role's action on the
same player (a check, a protection, a watch, a follow, a shot, a sigil); a night with no such visit
becomes holding back (fire, a check, a watch, a sigil), for the roles that may hold. A role that must
act each night (the Healer, the Trailseer) has no story for a night with no shown visit, and a night
with two shown visits (the Chanteuse carrying the kill) has none for any role.

Generate and test: the story is added to the claims as the seat's role claim and night actions, and
the comparisons (Table E, the role claims' status) run as a public observer would, with the public's
candidate roles and no private record. The story fits when every line drawn from it agrees (E1, E17):
no line calls it false, sets it against another claim, or leaves it open; and when the morning lets
the role have made each visit (conditionals/visits.py: a sigil that struck elsewhere, a save elsewhere). The lines stay facts (R11:
the advice is the cards'): which stories fit, which would be counter-claimed and by whom.

Wolves and the Serial Killer only; the Necromancer's visits are under the bodies' names, never its
own, so its covers are the claimable roles alone (status.py). Only for a seat that has not yet said
what it did on those nights, and, once it claims a role, only that role.
"""

from __future__ import annotations

import dataclasses

from Agents.deduction.candidates import public_candidates
from Agents.deduction.comparisons import wording
from Agents.deduction.evil.own_visits import RECENT_NIGHTS, _visits
from Agents.deduction.evil.claimable import claimable_roles
from Agents.deduction.conditionals.visits import roles_that_could_visit
from Agents.deduction.morning import announcement_of
from Agents.deduction.seat_view import public_record
from Agents.schemas.deduction import ActionClaim, DeductionItem, PlayerClaimView, RoleClaim, SeatView, Source
from Agents.schemas.role_traits import BODY_USER, ROLE_TRAITS
from Agents.schemas.roles import LONE_KILLER, ROLE_SPECS, TOWN, WOLVES

ACTION_OF = {"investigator": "investigate", "healer": "protect", "sentinel": "watch", "trailseer": "follow",
             "vigilante": "shoot", "sigilist": "sigil"}
"""Each town role's visit, as a claimed action."""
HOLD_OF = {"investigator": "kept_check", "sentinel": "kept_watch", "vigilante": "held_fire", "sigilist": "kept_sigil"}
"""What a role that may hold says for a night it made no visit."""
AGREE = frozenset({"E1", "E17"})
"""The comparison rows that agree with a claim (a sighting and the visitor's own word; the two
directions of a visit): every other line drawn from a story stops it fitting."""
OBSERVER = "observer"
OBSERVER_ROLE = "villager"
"""The observer holds a retired role never dealt in a ten-seat cast, so no role check is about it."""


def cover_items(view: SeatView, today: int) -> list[DeductionItem]:
    """One shared line: per claimable town role, the story that fits the seat's last two nights,
    the counter-claimed ones apart; nothing when no role has a story."""
    spec = ROLE_SPECS.get(view.role)
    if (spec is None or spec.side not in (WOLVES, LONE_KILLER) or view.role == BODY_USER
            or view.player_id not in view.living):
        return []
    nights = [night for night in range(max(1, today - RECENT_NIGHTS), today) if announcement_of(view, night) is not None]
    mine = next((player for player in view.claims if player.player == view.player_id), None)
    said = {claim.night for claim in mine.actions} if mine is not None else set()
    nights = [night for night in nights if night not in said]  # what it already said is its story
    if not nights:
        return []
    record = public_record(view)
    public = public_candidates(record)
    if public is None:
        return []
    roles = [role for role in claimable_roles(view) if ROLE_SPECS[role].side == TOWN and role in ACTION_OF]
    if mine is not None and mine.current_role is not None:
        roles = [role for role in roles if role == mine.current_role]
    visits = {night: [target for target, shown in _visits(view, night).items() if shown] for night in nights}
    living = set(view.living)
    fitting, countered = [], []
    for role in roles:
        story = _story(view, role, visits, today, public)
        if story is None:
            continue
        claimants = [player.player for player in view.claims
                     if player.player in living and player.player != view.player_id and player.current_role == role]
        (countered if claimants else fitting).append((role, story, claimants))
    if not fitting and not countered:
        return []
    reported = _reported(view, nights)
    n = wording.Names(view.player_id)
    # In the screen a seat offered only a counter-claimed story claimed a role whose story did not fit
    # ("I'm the Vigilante, I shot player_8": no shot was announced), so the line says when the rest fail.
    others_fail = (mine is None or mine.current_role is None) and len(fitting) + len(countered) < len(roles)
    text = wording.covers(n, [(role, _deeds(story)) for role, story, _ in fitting],
                          [(role, _deeds(story), claimants, [c for c in claimants if c in view.pack_roles])
                           for role, story, claimants in countered], reported, others_fail)
    return [DeductionItem(row="F7+S14", subject=None, night=max(nights), conclusion=(), text=text,
                          sources=(Source("own_record", max(nights), view.player_id),
                                   *(Source("claim", 0, player) for player in sorted({p for _, _, cs in countered for p in cs}))),
                          derivation=tuple(claim for _, story, _ in fitting + countered for claim in story),
                          receiver=view.player_id)]


def _story(view: SeatView, role: str, visits: dict[int, list[str]], today: int, public) -> tuple[ActionClaim, ...] | None:
    """The role's story for the nights, or None: a night it cannot tell, or a line that does not agree."""
    claims = []
    for night, targets in visits.items():
        if len(targets) > 1:
            return None
        if targets:
            if role not in _could_visit(view, targets[0], night, public):
                return None  # the morning places this role's one visit elsewhere (a sigil's strike, a save)
            if role == "sentinel" and _attacked(view, night, targets[0]):
                return None  # a watch there saw the attacker come, and the story would have to name it
            claims.append(_claim(view, night, ACTION_OF[role], targets[0], _result(view, role, night, targets[0]), today))
        elif role in HOLD_OF and not ROLE_TRAITS[role].must_act:
            claims.append(_claim(view, night, "no_action", "", HOLD_OF[role], today))
        else:
            return None
    story = tuple(claims)
    observer = _observer(view, role, story, today)
    from Agents.deduction.comparisons import compare  # the package imports this module

    for item in compare(observer, today, public):
        drawn = any(claim in item.derivation for claim in story)
        about_role = item.subject == view.player_id and item.row.startswith("E15")
        if (drawn or about_role) and item.row not in AGREE:
            return None
    return story


def _could_visit(view: SeatView, target: str, night: int, public) -> frozenset[str]:
    """The roles that could have gone to `target` that night, by the morning (the conditionals' rule:
    a role whose one visit the morning places elsewhere could not). The comparisons place an
    announced attack on a role, never a player, so a story's role claim would not meet it there."""
    dealt = frozenset(role for role, count in view.cast_role_counts.items() if count > 0)
    death = next((d for d in view.dead_roster if d.player == target and not d.concealed), None)
    target_roles = frozenset({death.role}) if death is not None else frozenset(public.roles.get(target, dealt))
    return roles_that_could_visit(target, night, announcement_of(view, night), dealt, target_roles, view.cast_role_counts)


def _attacked(view: SeatView, night: int, target: str) -> bool:
    announcement = announcement_of(view, night)
    return any(event.player == target for event in (*announcement.deaths, *announcement.saves))


def _result(view: SeatView, role: str, night: int, target: str) -> str:
    """What the role would say came of its action, where the record fixes it: a check of a player
    whose role is revealed reads as that role reads (in the screen, a fake Investigator called the
    revealed Chanteuse Not suspicious); a protection of a player saved by the Healer that night saved
    them; a sigil or shot that killed no one had no effect or left them alive. Otherwise not said (an
    unrevealed player's reading, a watch's or a follow's sightings)."""
    announcement = announcement_of(view, night)
    died = any(death.player == target for death in announcement.deaths)
    if role == "investigator":
        revealed = next((d.role for d in view.dead_roster if d.player == target and not d.concealed and d.role), None)
        reads = ROLE_TRAITS[revealed].reads_suspicious if revealed in ROLE_TRAITS else None
        return {"always": "suspicious", "never": "not_suspicious"}.get(reads, "not_said")
    if role == "healer":
        saved = any(save.player == target and save.saver == "healer" for save in announcement.saves)
        return "saved_from_attack" if saved else "no_attack"
    if role == "sigilist":
        return "no_effect" if not died else "not_said"
    if role == "vigilante":
        return "survived" if not died else "died"
    return "not_said"


def _claim(view: SeatView, night: int, action: str, target: str, result: str, today: int) -> ActionClaim:
    return ActionClaim(claimant=view.player_id, day=today, night=night, action=action, target=target, result=result,
                       seen=(), latest=True, blocked=False,
                       completed=action != "no_action" and result != "not_said", seen_complete=False, source="speaker")


def _observer(view: SeatView, role: str, story: tuple[ActionClaim, ...], today: int) -> SeatView:
    """The public with the story said: the seat claims `role` today, with the story's night actions
    beside what it already said; the observer has no role, no pack and no night record."""
    mine = next((player for player in view.claims if player.player == view.player_id), None)
    told = PlayerClaimView(
        player=view.player_id,
        roles=(*(mine.roles if mine is not None else ()), RoleClaim(today, role, False)),
        current_role=role,
        withdrawn_roles=mine.withdrawn_roles if mine is not None else (),
        actions=(*(mine.actions if mine is not None else ()), *story),
    )
    claims = [player for player in view.claims if player.player != view.player_id] + [told]
    return dataclasses.replace(view, player_id=OBSERVER, role=OBSERVER_ROLE, night_records=[], pack_roles={},
                               claims=claims)


def _reported(view: SeatView, nights: list[int]) -> dict[int, list[str]]:
    """Per night, the players who say they saw the seat's visit: a watch that names it, a follow of it."""
    out: dict[int, list[str]] = {}
    for player in view.claims:
        if player.player == view.player_id:
            continue
        for claim in player.actions:
            if not claim.latest or claim.night not in nights or claim.blocked:
                continue
            if (claim.action == "watch" and view.player_id in claim.seen) or (claim.action == "follow" and claim.target == view.player_id):
                out.setdefault(claim.night, []).append(player.player)
    return out


def _deeds(story: tuple[ActionClaim, ...]) -> list[tuple[int, str, str, str]]:
    return [(claim.night, claim.action, claim.target, claim.result) for claim in story]

"""The role claims' status (catalogue F3's claim half, E15), each role claim against what the seat knows
(Table D).

- The status line, shared, from the first role claim on: which claimed roles no one else claims
  (AC4, line 3), which are claimed by two or more players ("at most one holds it", a role dealt
  once), a role claim withdrawn today, and the living players who have made no role claim (nothing
  follows from that), named only when three or fewer. Only the living players' current claims count;
  a role a dead player whose role is hidden claimed is not called unclaimed by anyone else.
- A role claim the seat knows is false: a role not dealt, a role revealed at another player's death,
  the seat's own role, a packmate's, or a role the seat's candidates leave the claimant no longer.
  A false claim does not prove an evil role (Table E): the line says only that the claim is false.
An evil seat's own lines (the roles it can claim, a hidden body's role) are in Agents/deduction/evil/.
The claim ledger in the prompt (days before today) already says when a claim exceeds a role's count
or a revealed role: those lines are left to it for a claim said before today.
"""

from __future__ import annotations

from Agents.deduction.comparisons import wording
from Agents.deduction.comparisons.statements import Possible
from Agents.schemas.deduction import (
    DeductionItem,
    NotAllTrue,
    PlayerClaimView,
    RoleIn,
    SeatView,
    Source,
)
from Agents.schemas.roles import ROLE_SPECS

MOST_SILENT_NAMED = 3
"""The players with no role claim are named only when this few (coordinator, 2026-10-17): a longer
list early in a game says little."""


def _dealt(view: SeatView) -> list[str]:
    return [role for role in ROLE_SPECS if view.cast_role_counts.get(role)]


def _claimed_on(player: PlayerClaimView, role: str) -> int:
    """The day the player made its current claim of `role`."""
    return max((claim.day for claim in player.roles if claim.role == role and not claim.withdrawn), default=0)


def _revealed_holders(view: SeatView, role: str) -> list[str]:
    return [death.player for death in view.dead_roster if death.role == role and not death.concealed]


def status_items(view: SeatView, today: int, night: int) -> list[DeductionItem]:
    """The shared status line, from the first role claim on."""
    if not any(player.roles for player in view.claims):
        return []
    n = wording.Names(view.player_id)
    living = set(view.living)
    hidden = {death.player for death in view.dead_roster if death.concealed}
    current = {player.player: player for player in view.claims
               if player.current_role in ROLE_SPECS and player.player in living}
    claimed_by_hidden = {player.current_role for player in view.claims if player.player in hidden}
    by_role: dict[str, list[str]] = {}
    for player in view.living:
        if player in current:
            by_role.setdefault(current[player].current_role, []).append(player)
    sentences, facts, sources = [], [], []
    alone = [role for role in ROLE_SPECS if len(by_role.get(role, [])) == 1 and view.cast_role_counts.get(role) == 1
             and not _revealed_holders(view, role) and role not in claimed_by_hidden]
    for player in view.claims:
        last = player.roles[-1] if player.roles else None
        if player.player in living and player.player != view.player_id and last is not None and last.implied_by:
            said = [(a.action, a.result, a.target, a.night) for a in last.implied_by]
            sentences.append(wording.implied_claim(n, player.player, said, last.role))
    if alone:
        sentences.append(wording.no_one_else_claims(alone))
    for role in ROLE_SPECS:
        players = by_role.get(role, [])
        if len(players) < 2 or view.cast_role_counts.get(role) != 1 or _revealed_holders(view, role):
            continue
        if all(_claimed_on(current[player], role) < today for player in players if player != view.player_id):
            continue  # the ledger says it: "the game has 1 healer, and player_8 also claims it"
        sentences.append(wording.counter_claim(n, players, role))
        facts += [NotAllTrue((RoleIn(a, frozenset({role})), RoleIn(b, frozenset({role}))))
                  for i, a in enumerate(players) for b in players[i + 1:]]
    for player in view.claims:
        if player.player not in living or player.current_role is not None:
            continue
        last = player.roles[-1] if player.roles else None
        if last is not None and last.withdrawn and last.day >= today:
            claimed = max((claim.day for claim in player.roles if claim.role == last.role and not claim.withdrawn),
                          default=last.day)
            sentences.append(wording.withdrew(player.player, last.role, claimed, last.day))
    ever = {player.player for player in view.claims if player.roles}
    silent = [player for player in view.living if player != view.player_id and player not in ever]
    if 0 < len(silent) <= MOST_SILENT_NAMED:
        sentences.append(wording.no_role_claim(silent))
    if not sentences:
        return []
    sources = tuple(Source("claim", 0, player.player) for player in view.claims if player.roles)
    return [DeductionItem(row="F3+E15", subject=None, night=night, conclusion=tuple(facts), text=" ".join(sentences),
                          sources=sources, receiver=view.player_id)]


def role_claim_items(view: SeatView, today: int, night: int, possible: Possible) -> list[DeductionItem]:
    """Each living player's current role claim that the seat knows is false, in its entry."""
    living = set(view.living)
    dealt = set(_dealt(view))
    items = []
    for player in view.claims:
        role = player.current_role
        if player.player == view.player_id or player.player not in living or role not in ROLE_SPECS:
            continue
        said_today = _claimed_on(player, role) >= today
        conclusion = [NotAllTrue((RoleIn(player.player, frozenset({role})),))]
        revealed = [p for p in _revealed_holders(view, role) if p != player.player]
        if role not in dealt:
            reason = wording.not_in_cast(role) if said_today else None
        elif revealed and len(revealed) >= view.cast_role_counts[role]:
            reason = wording.revealed_as(revealed, role) if said_today else None
        elif role == view.role and view.cast_role_counts[role] == 1:
            reason = wording.you_are(role)
        elif role in view.pack_roles.values() and view.cast_role_counts[role] == 1:
            mate = next(p for p, r in view.pack_roles.items() if r == role)
            if mate == player.player:
                continue
            reason = wording.packmate_is(mate, role)
        elif role not in possible(player.player):
            roles = possible(player.player)
            listed = [r for r in ROLE_SPECS if r in roles]
            if not listed:
                continue
            reason = wording.can_only_be(player.player, listed)
            conclusion.insert(0, RoleIn(player.player, frozenset(roles)))
        else:
            continue
        if reason is None:
            continue  # the ledger says it for a claim said before today
        items.append(DeductionItem(row="E15+D", subject=player.player, night=night, conclusion=tuple(conclusion),
                                   text=wording.role_claim_false(player.player, role, reason,
                                                                 implied=bool(player.roles and player.roles[-1].implied_by)),
                                   sources=(Source("claim", 0, player.player),), receiver=view.player_id))
    return items

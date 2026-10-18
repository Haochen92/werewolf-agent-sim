"""The role claims' status (catalogue F3's claim half, E15), each role claim against what the seat knows
(Table D), and, for an evil seat, the roles it can still claim (F7's note, owner 2026-10-16).

- The status line, shared, from the first role claim on: which claimed roles no one else claims
  (AC4, line 3), which are claimed by two or more players ("at most one holds it", a role dealt
  once), a role claim withdrawn today, and the living players who have made no role claim (nothing
  follows from that), named only when three or fewer. Only the living players' current claims count;
  a role a dead player whose role is hidden claimed is not called unclaimed by anyone else.
- A role claim the seat knows is false: a role not dealt, a role revealed at another player's death,
  the seat's own role, a packmate's, or a role the seat's candidates leave the claimant no longer.
  A false claim does not prove an evil role (Table E): the line says only that the claim is false.
- An evil seat (a wolf, the lone killer): the town and neutral roles the public record still allows
  it, the full list, so it can claim one without a public contradiction; and which of them no living
  player claims now (claiming one that is claimed starts a counter-claim). Facts only, no advice.
  The public's candidate roles for the seat are what the public record allows (propagation, checked
  against every legal deal by the brute-force oracle in the tests). With it, a hidden body's role the
  seat's own record shows (a wolf's pack kill, the Necromancer's kill through the Illusionist's body),
  when it is one of those roles and dealt once: no living player holds it (owner, 2026-10-17).
The claim ledger in the prompt (days before today) already says when a claim exceeds a role's count
or a revealed role: those lines are left to it for a claim said before today.
"""

from __future__ import annotations

from Agents.deduction.candidates import public_candidates
from Agents.deduction.comparisons import wording
from Agents.deduction.comparisons.statements import Possible
from Agents.deduction.records import read_record
from Agents.deduction.seat_view import public_record
from Agents.schemas.deduction import (
    DeductionItem,
    HeldBy,
    NotAllTrue,
    OpenRoles,
    PlayerClaimView,
    RoleIn,
    SeatView,
    Source,
)
from Agents.schemas.roles import LONE_KILLER, NEUTRAL, ROLE_SPECS, TOWN, WOLVES

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
                                   text=wording.role_claim_false(player.player, role, reason),
                                   sources=(Source("claim", 0, player.player),), receiver=view.player_id))
    return items


def claimable_items(view: SeatView, night: int) -> list[DeductionItem]:
    """An evil seat's own line: the town and neutral roles the public record still allows it."""
    spec = ROLE_SPECS.get(view.role)
    if spec is None or spec.side not in (WOLVES, LONE_KILLER) or not view.living:
        return []
    public = public_candidates(public_record(view))
    if public is None or view.player_id not in public.roles:
        return []
    allowed = public.roles[view.player_id]
    roles = [role for role in _dealt(view) if role in allowed and ROLE_SPECS[role].side in (TOWN, NEUTRAL)]
    living = set(view.living)
    claimed = {player.current_role for player in view.claims if player.player in living}
    unclaimed = [role for role in roles if role not in claimed]
    return [DeductionItem(row="F7+E15", subject=None, night=night,
                          conclusion=(OpenRoles(view.player_id, frozenset(roles)),),
                          text=wording.claimable(roles, unclaimed),
                          sources=(Source("dead_roster", night), Source("announcement", night)),
                          receiver=view.player_id), *_hidden_roles(view, roles)]


def _hidden_roles(view: SeatView, claimable: list[str]) -> list[DeductionItem]:
    """A hidden body's role the seat's own record shows (L8: the living Illusionist's conceal, on the
    pack's kill record, to every wolf; one through its body, on the Necromancer's kill record, to the
    Necromancer), when it is a role the seat can claim (so the public record does not show it) dealt
    once (so the body was its only holder)."""
    concealed = {death.player for death in view.dead_roster if death.concealed}
    items = []
    for record in view.night_records:
        read = read_record(record, view)
        role = read.hidden_role
        if (not role or read.target not in concealed or role not in claimable
                or view.cast_role_counts.get(role) != 1):
            continue
        source = wording.own_record(read.night) if read.body else wording.pack_kill_record(read.night)
        items.append(DeductionItem(row="F7+L8", subject=None, night=read.night,
                                   conclusion=(HeldBy(role, (read.target,)), OpenRoles(view.player_id, frozenset({role}))),
                                   text=wording.hidden_role_claim(read.target, role, source),
                                   sources=(Source("own_record", read.night, read.target), Source("dead_roster", read.night)),
                                   derivation=(record,), receiver=view.player_id))
    return items

"""The candidate roles of every player, living or a hidden body, by propagation (catalogue Table F,
"How the engine derives them"; Table C, C18).

Each player starts with the census: the dealt roles not known to be held by someone else (C1). The
constraints remove candidates, then these rules run until nothing changes:
- one copy of each role (C18): a role whose every copy has a certain holder is removed from
  everyone else; a role with as many possible holders as copies is theirs;
- k players who can only hold k roles between them: no one else holds those roles (C18);
- one of the players a watch saw made the attack (C6): if only one of them can, it did; and no one
  outside them holds a role dealt once;
- the game continued past every check so far (C18, continuation.py).
A role whose holder must have been alive on a night leaves the bodies that died before it.

Sound, not complete: a candidate is removed only when no legal game that agrees with the view gives
it to that player, but a full search may remove more (the brute-force oracle in the tests checks the
first; the second only means the seat is told less). A view that leaves some player no candidate is
an input or rule error: no candidates at all, so nothing is said.
"""

from __future__ import annotations

from itertools import combinations

from Agents.deduction.candidates.continuation import body_roles_that_continue
from Agents.deduction.night_state import deaths_before_night
from Agents.schemas.deduction import (
    AliveAtNight,
    Candidates,
    HolderAmong,
    OnlyRoles,
    RoleConstraint,
    Removal,
    Source,
    SourceEvent,
)
from Agents.schemas.game_events import DeathRecord


class Contradiction(Exception):
    """Some player is left no candidate role: the view and the rules disagree."""


class _Board:
    """The candidates as they narrow, with why each role went."""

    def __init__(self, players: list[str], census: frozenset[str], known: dict[str, str]):
        self.roles = {player: {known[player]} if player in known else set(census) for player in players}
        self.removals: dict[str, list[Removal]] = {player: [] for player in players}
        self.changed = False

    def restrict(self, player: str, allowed, rule: str, sources: tuple[Source, ...] = (),
                 derivation: tuple[SourceEvent, ...] = ()) -> bool:
        """Keep only `allowed` for `player`; True when a role went."""
        gone = self.roles[player] - set(allowed)
        if not gone:
            return False
        for role in sorted(gone):
            self.removals[player].append(Removal(role, rule, sources, derivation))
        self.roles[player] -= gone
        if not self.roles[player]:
            raise Contradiction(player)
        self.changed = True
        return True

    def sources_of(self, players) -> tuple[tuple[Source, ...], tuple[SourceEvent, ...]]:
        """What the removals on `players` rested on: the provenance of a count rule's step."""
        sources, derivation = {}, {}
        for player in players:
            for removal in self.removals[player]:
                sources.update(dict.fromkeys(removal.sources))
                derivation.update({id(event): event for event in removal.derivation})
        return tuple(sources), tuple(derivation.values())


def solve(living: list[str], dead_roster: list[DeathRecord], copies: dict[str, int], known: dict[str, str],
          constraints: list[RoleConstraint], receiver: str | None = None) -> Candidates | None:
    """Every player's candidate roles; None when the players do not match the cast or the view
    leaves some player no role."""
    players = list(living) + [death.player for death in dead_roster]
    if len(set(players)) != len(players) or len(players) != sum(copies.values()):
        return None
    if any(player not in players or role not in copies for player, role in known.items()):
        return None
    census = _census(copies, known)
    board = _Board(players, census, known)
    try:
        for constraint in constraints:
            if isinstance(constraint, OnlyRoles) and constraint.player in board.roles:
                board.restrict(constraint.player, constraint.roles, constraint.rule, constraint.sources,
                               constraint.derivation)
        alive_reasons = _alive_at_night(board, [c for c in constraints if isinstance(c, AliveAtNight)], dead_roster)
        among = [c for c in constraints if isinstance(c, HolderAmong)]
        _propagate(board, among, dead_roster, copies)
    except Contradiction:
        return None
    return Candidates(
        living=tuple(living),
        hidden_bodies=tuple(death.player for death in dead_roster if death.concealed),
        roles={player: frozenset(roles) for player, roles in board.roles.items()},
        census=census,
        known=frozenset(known),
        removals={player: tuple(removals) for player, removals in board.removals.items()},
        alive_reasons=alive_reasons,
        receiver=receiver,
    )


def _census(copies: dict[str, int], known: dict[str, str]) -> frozenset[str]:
    """C1: the dealt roles with a copy no known player holds."""
    held = {}
    for role in known.values():
        held[role] = held.get(role, 0) + 1
    return frozenset(role for role, count in copies.items() if count > held.get(role, 0))


def _alive_at_night(board: _Board, alive: list[AliveAtNight], dead_roster: list[DeathRecord]) -> dict[str, AliveAtNight]:
    """A role whose holder was alive at the start of night n is not a body that died before it.
    Returns, per role this took off a body, its latest such night: the census line's reason."""
    latest: dict[str, AliveAtNight] = {}
    took_off_a_body: set[str] = set()
    for constraint in alive:
        if constraint.role not in latest or constraint.night > latest[constraint.role].night:
            latest[constraint.role] = constraint
        for death in deaths_before_night(dead_roster, constraint.night):
            if not death.concealed:
                continue
            if board.restrict(death.player, board.roles[death.player] - {constraint.role},
                              f"{constraint.rule}+C18" if constraint.rule else "C18", constraint.sources,
                              constraint.derivation):
                took_off_a_body.add(constraint.role)
    return {role: latest[role] for role in sorted(took_off_a_body)}


def _propagate(board: _Board, among: list[HolderAmong], dead_roster: list[DeathRecord],
               copies: dict[str, int]) -> None:
    board.changed = True
    while board.changed:
        board.changed = False
        for constraint in among:
            _holder_among(board, constraint, copies)
        _one_copy_each(board, copies)
        _k_players_k_roles(board, copies)
        _game_continued(board, dead_roster, copies)


def _holder_among(board: _Board, constraint: HolderAmong, copies: dict[str, int]) -> None:
    """C6: one of `players` holds one of `roles`. If only one of them can, it does; if only one of
    the roles is left to them (a wolf among them, with the other wolf ruled out), and it is dealt
    once, no one else holds it."""
    members = [player for player in constraint.players if player in board.roles]
    able = [player for player in members if board.roles[player] & constraint.roles]
    if not able:
        raise Contradiction(constraint.players)
    if len(able) == 1:
        board.restrict(able[0], constraint.roles, constraint.rule, constraint.sources, constraint.derivation)
    roles_left = {role for role in constraint.roles if any(role in board.roles[player] for player in members)}
    if len(roles_left) == 1:
        (role,) = roles_left
        if copies.get(role) == 1:
            for player in board.roles:
                if player not in members:
                    board.restrict(player, board.roles[player] - {role}, constraint.rule, constraint.sources,
                                   constraint.derivation)


def _one_copy_each(board: _Board, copies: dict[str, int]) -> None:
    """C18: each copy of a role has one holder. All copies certain: no one else holds it. As many
    possible holders as copies: each of them holds it."""
    for role, count in copies.items():
        certain = [player for player, roles in board.roles.items() if roles == {role}]
        if len(certain) > count:
            raise Contradiction(role)
        if len(certain) == count:
            sources, derivation = board.sources_of(certain)
            for player, roles in board.roles.items():
                if player not in certain:
                    board.restrict(player, roles - {role}, "C18", sources, derivation)
        possible = [player for player, roles in board.roles.items() if role in roles]
        if len(possible) < count:
            raise Contradiction(role)
        if len(possible) == count:
            others = [player for player in board.roles if player not in possible]
            sources, derivation = board.sources_of(others)
            for player in possible:
                board.restrict(player, {role}, "C18", sources, derivation)


def _k_players_k_roles(board: _Board, copies: dict[str, int]) -> None:
    """C18: when k players can only hold roles with k copies left between them, no one else holds
    those roles."""
    open_players = [player for player, roles in board.roles.items() if len(roles) > 1]
    certain: dict[str, int] = {}
    for roles in board.roles.values():
        if len(roles) == 1:
            (role,) = roles
            certain[role] = certain.get(role, 0) + 1
    left = {role: count - certain.get(role, 0) for role, count in copies.items()}
    for size in range(2, len(open_players)):
        # A player whose own roles already have more copies left than `size` is in no such group.
        fits = [player for player in open_players if sum(left[role] for role in board.roles[player]) <= size]
        for group in combinations(fits, size):
            their_roles = set().union(*(board.roles[player] for player in group))
            copies_left = sum(left[role] for role in their_roles)
            if copies_left < size:
                raise Contradiction(group)
            if copies_left > size:
                continue
            sources, derivation = board.sources_of(group)
            for player in open_players:
                if player not in group:
                    board.restrict(player, board.roles[player] - their_roles, "C18", sources, derivation)


def _game_continued(board: _Board, dead_roster: list[DeathRecord], copies: dict[str, int]) -> None:
    """C18: the hidden bodies keep only roles with which the game went on at every check."""
    bodies = [death.player for death in dead_roster if death.concealed]
    if not bodies:
        return
    others_fixed: dict[str, int] = {}
    for player, roles in board.roles.items():
        if player not in bodies and len(roles) == 1:
            (role,) = roles
            others_fixed[role] = others_fixed.get(role, 0) + 1
    kept = body_roles_that_continue(bodies, {body: frozenset(board.roles[body]) for body in bodies}, dead_roster,
                                    copies, others_fixed)
    if kept is None:
        return
    sources = tuple(Source("dead_roster", death.day, death.player) for death in dead_roster)
    for body in bodies:
        board.restrict(body, kept[body], "C18", sources, tuple(dead_roster))

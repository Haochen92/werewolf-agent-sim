"""Works out which roles each player could still hold, living players and hidden bodies alike.

This is constraint propagation, the way a sudoku is solved by hand. Every player starts with every
dealt role that no known player already holds. The facts the engine gathered (constraints.py)
remove some of those candidates. Then four rules run in a loop until a full pass removes nothing:
- One holder per copy. When every copy of a role has a certain holder, no one else holds it. When a
  role has exactly as many possible holders as copies, each of them holds it.
- k players, k roles. When k players can only hold roles that have k copies left between them, no
  one outside the group holds those roles. (If player_2 and player_4 can each only be the Healer or
  the Sentinel, and one of each was dealt, those two hold both roles, so no one else is either.)
- One of these players did it. When a watch saw several visitors and one of them made the
  announced attack (or save), and only one of them can hold a role that does that, it holds it.
- The game went on. The game checks for a winner after every day and night, and it did not end, so
  a hidden body keeps only the roles that let it go on at every check (continuation.py).
Before the loop, a role whose holder must have been alive on some night is taken off every hidden
body that died before that night.

Sound, not complete. A role is removed only when no legal game consistent with what the seat knows
gives it to that player, so every "can only be" line is true. A search over every possible game can
sometimes remove more; missing that only means the seat is told less, never something false. The
oracle tests (tests/engine/deduction/test_candidates.py) check soundness that way, by brute force on
random games. When the facts leave some player no role at all, an input or a rule is wrong: the
solver returns None, and nothing is said.

Each removal records the catalogue row that made it (such as "C18", the counting rules) and the
events it rested on, so any line can be traced back to them.
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
    """Raised when some player is left no candidate role: the facts and the rules disagree."""


class _Board:
    """Each player's candidate roles as they narrow, with the reason each removed role went."""

    def __init__(self, players: list[str], census: frozenset[str], known: dict[str, str]):
        self.roles = {player: {known[player]} if player in known else set(census) for player in players}
        self.removals: dict[str, list[Removal]] = {player: [] for player in players}
        self.changed = False

    def restrict(self, player: str, allowed, rule: str, sources: tuple[Source, ...] = (),
                 derivation: tuple[SourceEvent, ...] = ()) -> bool:
        """Keeps only `allowed` for `player`, recording each removal with its reason.

        Args:
            player: whose candidates to narrow.
            allowed: the roles the player may keep; roles it has but `allowed` lacks are removed.
            rule: the catalogue row behind the removal (e.g. "A13", "C18"), for the log.
            sources: short citations of the evidence (kind, night, player).
            derivation: the evidence itself, the event objects the citations point at.

        Returns:
            True when at least one role was removed, False when the player kept every role.
            Raises Contradiction when no role is left."""
        ruled_out = self.roles[player] - set(allowed)  # the player's remaining roles this fact excludes
        if not ruled_out:
            return False
        for role in sorted(ruled_out):
            self.removals[player].append(Removal(role, rule, sources, derivation))
        self.roles[player] -= ruled_out
        if not self.roles[player]:
            raise Contradiction(player)
        self.changed = True
        return True

    def sources_of(self, players) -> tuple[tuple[Source, ...], tuple[SourceEvent, ...]]:
        """Returns what the removals on `players` rested on, so a counting rule's step can cite it."""
        sources, derivation = {}, {}
        for player in players:
            for removal in self.removals[player]:
                sources.update(dict.fromkeys(removal.sources))
                derivation.update({id(event): event for event in removal.derivation})
        return tuple(sources), tuple(derivation.values())


def solve(living: list[str], dead_roster: list[DeathRecord], copies: dict[str, int], known: dict[str, str],
          constraints: list[RoleConstraint], receiver: str | None = None) -> Candidates | None:
    """Works out which roles every player, living or a hidden body, could still hold.

    Args:
        living: the living players' ids, in seat order.
        dead_roster: every death so far, in order; a concealed one is a hidden body.
        copies: the dealt cast, role -> how many copies were dealt (public: every seat is told it).
        known: player -> role for every player whose role the viewer knows for sure: the revealed
            dead, and for a seat its own role and (a wolf) its pack. The public's run knows only the
            revealed dead.
        constraints: the facts to apply, from constraints.py: OnlyRoles ("this player is one of
            these roles"), AliveAtNight ("this role's holder was alive on night n") and HolderAmong
            ("one of these players holds one of these roles").
        receiver: whose view this is, a seat's id, or None for the public's. It does not change the
            solving; it is passed through to the result for the lines built from it.

    Returns:
        A Candidates: each player's remaining roles (one role for a known player), the starting
        census, the reason for every removal, and the receiver. None when the players do not match
        the dealt cast, or when the facts leave some player no role at all (an input or rule error,
        or, with a claim added as a premise, a claim that cannot be true)."""
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
        alive = [c for c in constraints if isinstance(c, AliveAtNight)]
        alive_reasons = _rule_out_later_actors_from_bodies(board, alive, dead_roster)
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
    """Returns the dealt roles that still have a copy no known player holds: every unknown player's
    starting candidates."""
    held = {}
    for role in known.values():
        held[role] = held.get(role, 0) + 1
    return frozenset(role for role, count in copies.items() if count > held.get(role, 0))


def _rule_out_later_actors_from_bodies(board: _Board, alive: list[AliveAtNight],
                                       dead_roster: list[DeathRecord]) -> dict[str, AliveAtNight]:
    """A role still acting on a night cannot be a hidden body that died before that night.

    Example: a sigil struck on night 2, so the Sigilist was alive then; player_1's hidden body died
    on night 1, so player_1 is not the Sigilist. Only hidden bodies are narrowed (a revealed body's
    role is already known).

    Returns, for each role this took off a body, the fact with the latest night: the census line
    gives it as the reason the role is alive."""
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
    """Runs the four rules below again and again until a full pass removes nothing.

    Each rule can unlock another (one pins a player, the next removes that role from everyone
    else), so one pass is not enough. It always stops: roles are only ever removed."""
    board.changed = True
    while board.changed:
        board.changed = False
        for constraint in among:
            _holder_among(board, constraint, copies)
        _one_copy_each(board, copies)
        _k_players_k_roles(board, copies)
        _game_continued(board, dead_roster, copies)


def _holder_among(board: _Board, constraint: HolderAmong, copies: dict[str, int]) -> None:
    """Rule: "one of these players did it."

    The fact: one of `constraint.players` holds one of `constraint.roles` (e.g. a watch saw
    player_2 and player_4 visit, and one of them made the attack).
    - If only one of the players could still hold such a role, it does.
      (player_4 is known to be the Healer, so player_2 made the attack.)
    - If only one such role is left to the group and it was dealt once, no one outside the group
      holds it. (The other wolf is dead, so the attacker is the last wolf: no one else is it.)"""
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
    """Uses how many copies of each role were dealt to narrow players' candidate sets.

        For each role:
        - If every copy already has a certain holder (a player whose set is only that role),
        the role is removed from every other player's set.
        (One Healer dealt, player_3's set is {Healer} -> Healer is removed from everyone else.)
        - If exactly as many players have the role in their set as there are copies,
        each of those players' sets shrinks to just that role.
        (Two Wolves dealt, only player_2 and player_5 have Wolf in their sets -> both become {Wolf}.)
        Raises Contradiction if the counts can't work: more certain holders than copies,
        or fewer players who could hold it than copies.
    """
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
    """Rule: "a closed group."

    When a group of k players can only hold roles that have k copies left between them, those roles
    are used up inside the group, so no one outside it holds them.
    (player_2 and player_4 can each only be the Healer or the Sentinel: two players, two roles, so
    no one else is the Healer or the Sentinel.)"""
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
    """Rule: "the game did not end."

    The game checks for a winner after every day and every night, and it is still going. So a hidden
    body cannot hold a role that would have ended it at one of those checks.
    (If player_1's hidden body being a wolf would have left no wolf alive, the town would already
    have won: player_1 is not a wolf.) The checking itself is in continuation.py."""
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

"""The brute-force oracle for the candidate roles (catalogue "Build verification": tests only, never in
a game). It enumerates every way to deal the cast to the players that agrees with what a view knows,
and says which roles each player holds in at least one of them (its support).

What a view knows, written here from the rules and the facts' meanings, not from the engine's
propagation (Agents/deduction/candidates/):
- the cast, one copy of each role per dealt copy, every player holding one; the revealed roles; for a
  seat, its own role, its pack and the hidden role its pack's kill record (or the Necromancer's kill
  through the Illusionist's body) names;
- every certain fact the engine states (the public items, and the seat's own lines), each read as a
  condition on the deal: a fact about roles directly, an action that went ahead on night n as "one
  of its possible makers was alive when night n began";
- a night death was not immune that night (never the Serial Killer; never the Necromancer on nights
  1 and 2); how a body was hidden narrows it (catalogue L8);
- the game continued past every check so far: the real `determine_winner` and `is_draw` find no
  end at any of them;
- for a conditional line (slice 10, `add_premise`), its premise: the roles it assumes, and each
  claimed visit as a condition on the visitor's and the target's roles in the deal, from the rules.
The search deals to the dead first (every condition on the dead is then decided), then to the living
with the fewest choices first. Once every player left could take every role left and no condition is
open, every order of the rest is a deal: they are counted, not listed.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from math import factorial

from Agents.deduction import own_result_lines, public_items
from Agents.nodes.orchestrator import determine_winner, is_draw
from Agents.rules.night_record import PACK_ACTOR
from Agents.schemas.deduction import (
    ActedThroughBody,
    AttackedInOwnName,
    BlockedBy,
    CarriedPackKill,
    KilledThroughBody,
    MadeBy,
    PickMade,
    ProtectedBy,
    PublicRecord,
    RoleIn,
    SeatView,
    SilentAttack,
    VisitAsClaimed,
    Visited,
    WentTo,
)
from Agents.schemas.game_events import DeathRecord
from Agents.schemas.roles import NECROMANCER_IMMUNE_NIGHTS, ROLE_SPECS, TOWN, WOLVES

WOLF_ROLES = frozenset(role for role, spec in ROLE_SPECS.items() if spec.pack and not spec.retired)
MAKERS = {"wolves": WOLF_ROLES, "serial_killer": frozenset({"serial_killer"}),
          "vigilante": frozenset({"vigilante"}), "sigilist": frozenset({"sigilist"}),
          "healer": frozenset({"healer"})}
"""Who makes each announced attack type under their own name, or the living Healer's save."""
NEVER_VISIT = {"necromancer", "speculator", "fortune_teller"}


@dataclass
class Oracle:
    """What one view knows, as conditions on a deal of the cast."""

    players: list[str]
    copies: dict[str, int]
    allowed: dict[str, set[str]]
    """Each player's possible roles from the conditions on that player alone."""
    dead: list[DeathRecord]
    on_the_dead: list[Callable[[dict[str, str]], bool]] = field(default_factory=list)
    """Conditions decided by the dead players' roles alone (alive at a night, the game went on)."""
    among: list[tuple[tuple[str, ...], frozenset[str]]] = field(default_factory=list)
    """Some player of the first holds a role of the second."""
    on_players: list[tuple[tuple[str, ...], Callable[[dict[str, str]], bool]]] = field(default_factory=list)
    """Conditions decided by the roles of the players named (a conditional line's claimed visit: the
    visitor's role and the target's), checked once all of them are dealt."""

    def allows(self, deal: dict[str, str]) -> bool:
        """Whether a full deal meets every condition (the true deal must)."""
        expected = sorted(role for role, count in self.copies.items() for _ in range(count))
        if sorted(deal[p] for p in self.players) != expected:
            return False
        if any(deal[p] not in self.allowed[p] for p in self.players):
            return False
        return (all(check(deal) for check in self.on_the_dead) and self._among_met(deal)
                and all(check(deal) for _, check in self.on_players))

    def _among_met(self, deal: dict[str, str]) -> bool:
        return all(any(deal.get(p) in roles for p in players) for players, roles in self.among)

    def support(self) -> tuple[dict[str, set[str]], int]:
        """Each player's roles over every deal that meets the conditions, and how many deals."""
        dead = [death.player for death in self.dead]
        in_conditions = {p for players, _ in self.on_players for p in players}
        living = sorted((p for p in self.players if p not in dead),
                        key=lambda p: (p not in in_conditions, len(self.allowed[p]), p))
        order = sorted(dead, key=lambda p: len(self.allowed[p])) + living
        support: dict[str, set[str]] = {p: set() for p in self.players}
        left = dict(self.copies)
        deal: dict[str, str] = {}
        found = 0

        def search(index: int) -> None:
            nonlocal found
            if index == len(dead) and not all(check(deal) for check in self.on_the_dead):
                return
            if index >= len(dead):
                rest = order[index:]
                roles_left = {role for role, n in left.items() if n > 0}
                open_condition = any(set(players) & set(rest) for players, _ in self.on_players)
                if all(self.allowed[p] >= roles_left for p in rest) and self._among_met(deal) and not open_condition:
                    found += _orders(left)
                    for p, role in deal.items():
                        support[p].add(role)
                    for p in rest:
                        support[p] |= roles_left
                    return
                if index == len(order):
                    return
            player = order[index]
            for role in sorted(self.allowed[player]):
                if left.get(role, 0) <= 0:
                    continue
                left[role] -= 1
                deal[player] = role
                if all(check(deal) for players, check in self.on_players
                       if player in players and all(p in deal for p in players)):
                    search(index + 1)
                del deal[player]
                left[role] += 1

        search(0)
        return support, found


def _orders(left: dict[str, int]) -> int:
    """The ways to hand out the roles left to as many players: n! over each role's copies!."""
    total = factorial(sum(left.values()))
    for n in left.values():
        total //= factorial(n)
    return total


# --- what a view knows ------------------------------------------------------------------------

def _dead_before(dead_roster: list[DeathRecord], night: int) -> set[str]:
    """Who was dead when night `night` began: a night death before it, or a lynch on day `night` or
    before."""
    return {d.player for d in dead_roster
            if (d.phase == "night" and d.day < night) or (d.phase == "day" and d.day <= night)}


def oracle_of(record: PublicRecord, view: SeatView | None = None) -> Oracle:
    """The conditions the public record knows, plus, given a seat's view, what that seat knows."""
    players = list(record.living) + [death.player for death in record.dead_roster]
    copies = dict(record.cast_role_counts)
    dealt = {role for role, count in copies.items() if count}
    oracle = Oracle(players=players, copies=copies, allowed={p: set(dealt) for p in players},
                    dead=list(record.dead_roster))
    _the_dead(oracle, record)
    facts = [(fact, item.night) for item in public_items(record) if item.grade != "follows_if_claims"
             for fact in item.conclusion]
    if view is not None:
        _the_seat(oracle, view)
        facts += [(fact, own.day) for own, line in zip(view.night_records, own_result_lines(view))
                  if line is not None for fact in line.facts]
    for fact, night in facts:
        _read(fact, night, oracle, record.dead_roster, dealt)
    _the_game_went_on(oracle, record, dealt)
    return oracle


def _the_dead(oracle: Oracle, record: PublicRecord) -> None:
    hidden_by = {(death.player, a.night): death.hidden_by for a in record.announcements for death in a.deaths}
    for death in record.dead_roster:
        if not death.concealed:
            oracle.allowed[death.player] &= {death.role}
        if death.phase == "night":
            oracle.allowed[death.player] -= {"serial_killer"} | ({"necromancer"} if death.day <= NECROMANCER_IMMUNE_NIGHTS else set())
        how = hidden_by.get((death.player, death.day), "")
        if death.concealed and how == "illusionist":
            oracle.allowed[death.player] -= WOLF_ROLES
        if death.concealed and how == "reanimated_illusionist":
            oracle.allowed[death.player] -= {"necromancer", "illusionist"}


def _the_seat(oracle: Oracle, view: SeatView) -> None:
    oracle.allowed[view.player_id] &= {view.role}
    for player, role in view.pack_roles.items():
        oracle.allowed[player] &= {role}
    for own in view.night_records:
        if own.actor == PACK_ACTOR and own.action == "kill" and own.seen and own.target in oracle.allowed:
            oracle.allowed[own.target] &= {own.seen[0]}  # the role the living Illusionist hid
        if own.actor == view.player_id and own.hidden_role and own.target in oracle.allowed:
            oracle.allowed[own.target] &= {own.hidden_role}  # the role the Necromancer hid through the body


def _alive_at(roles, night: int, oracle: Oracle, dead_roster: list[DeathRecord]) -> None:
    """One of the holders of `roles` was alive when night `night` began."""
    before = _dead_before(dead_roster, night)
    roles = set(roles)
    oracle.on_the_dead.append(
        lambda deal: not roles or any(not any(deal.get(p) == role for p in before) for role in roles))


def _read(fact, night: int, oracle: Oracle, dead_roster: list[DeathRecord], dealt: set[str]) -> None:
    allowed = oracle.allowed
    if isinstance(fact, RoleIn):
        allowed[fact.player] &= set(fact.roles)
    elif isinstance(fact, CarriedPackKill):
        allowed[fact.player] &= WOLF_ROLES
    elif isinstance(fact, AttackedInOwnName):
        allowed[fact.player] &= WOLF_ROLES | {"serial_killer", "vigilante"}
    elif isinstance(fact, KilledThroughBody):
        allowed[fact.player] &= {"necromancer"}
        _alive_at({"necromancer"}, night, oracle, dead_roster)
    elif isinstance(fact, WentTo):
        if fact.visitor not in _dead_before(dead_roster, night):
            allowed[fact.visitor] -= NEVER_VISIT
    elif isinstance(fact, ActedThroughBody):
        allowed[fact.target] -= {"necromancer"}
        _alive_at({"necromancer"}, night, oracle, dead_roster)
    elif isinstance(fact, BlockedBy):
        _alive_at({"necromancer" if fact.through_body else "chanteuse"}, night, oracle, dead_roster)
        if fact.player != PACK_ACTOR:
            allowed[fact.player] &= {role for role in dealt if ROLE_SPECS[role].side in (TOWN, WOLVES)}
    elif isinstance(fact, ProtectedBy):
        _alive_at({"necromancer" if fact.through_body else "healer"}, night, oracle, dead_roster)
    elif isinstance(fact, Visited):
        _alive_at(fact.roles & dealt, night, oracle, dead_roster)
    elif isinstance(fact, MadeBy):
        oracle.among.append((fact.players, MAKERS[fact.action]))
        _alive_at(MAKERS[fact.action] & dealt, night, oracle, dead_roster)
    elif isinstance(fact, PickMade):
        _alive_at({"speculator"}, night, oracle, dead_roster)
    elif isinstance(fact, SilentAttack):
        _alive_at(fact.immune_roles & dealt, night, oracle, dead_roster)
        _alive_at(MAKERS.get(fact.attacker_type, frozenset()) & dealt, night, oracle, dead_roster)


def _the_game_went_on(oracle: Oracle, record: PublicRecord, dealt: set[str]) -> None:
    """At every check that changed who was alive, the real terminal rules found no end. Only the
    side counts of the living matter there, and they are the cast minus the dead."""
    order = lambda death: (death.day, 0 if death.phase == "day" else 1)  # noqa: E731 - day n before night n
    checks = sorted({order(death) for death in record.dead_roster})
    cast = [role for role, count in record.cast_role_counts.items() for _ in range(count)]
    for check in checks:
        dead_then = [death.player for death in record.dead_roster if order(death) <= check]
        alive_then = [p for p in oracle.players if p not in dead_then]

        def went_on(deal, dead_then=dead_then, alive_then=alive_then) -> bool:
            roles_left = list(cast)
            for player in dead_then:
                roles_left.remove(deal[player])
            state = {"roles": dict(zip(alive_then, roles_left)), "lineup": sorted(dealt),
                     "surviving_wolves": [], "surviving_villagers": alive_then}
            return determine_winner(state) is None and not is_draw(state)

        oracle.on_the_dead.append(went_on)


# --- a conditional line's premise (slice 10: catalogue F4 to F6) ---------------------------------

def add_premise(oracle: Oracle, facts, night: int, record: PublicRecord,
                engine_visits: list[tuple[str, str]] = ()) -> None:
    """A conditional line's premise as conditions on the deal, so the oracle's deals are those that
    agree with the view and the premise. A role directly; a claimed visit as the rules say who could
    have made it, decided on the deal's own roles (the target's role is the deal's, not a list of
    candidates); two visits by one player on that night (with `engine_visits`, the visits the seat's
    records and the wills show) only by the Chanteuse."""
    dealt = {role for role, count in record.cast_role_counts.items() if count}
    morning = next((a for a in record.announcements if a.night == night), None)
    before = _dead_before(record.dead_roster, night)
    visits = list(engine_visits)
    for fact in facts:
        if isinstance(fact, RoleIn):
            oracle.allowed[fact.player] &= set(fact.roles)
        elif isinstance(fact, BlockedBy):
            _read(fact, night, oracle, record.dead_roster, dealt)
        elif isinstance(fact, VisitAsClaimed):
            visits.append((fact.visitor, fact.target))
            if fact.target in before:
                oracle.allowed[fact.target] = set()  # no visit goes to the dead: no deal
            elif fact.visitor in before:
                _alive_at({"necromancer"}, night, oracle, record.dead_roster)
                oracle.allowed[fact.target] -= {"necromancer"}
            elif fact.visitor in oracle.allowed:
                oracle.on_players.append(((fact.visitor, fact.target), _could_visit(fact.visitor, fact.target, night, morning)))
    targets: dict[str, set[str]] = {}
    for visitor, target in visits:
        targets.setdefault(visitor, set()).add(target)
    for visitor, where in targets.items():
        if len(where) > 1 and visitor not in before and visitor in oracle.allowed:
            oracle.allowed[visitor] &= {"chanteuse"}


def _could_visit(visitor: str, target: str, night: int, morning) -> Callable[[dict[str, str]], bool]:
    """Whether the visitor's role in a deal could have gone to the target that night, given the
    morning: a neutral and the Necromancer never visit under their own name; a wolf never visits a
    wolf; the Serial Killer, the Vigilante and the Illusionist only to an attack of theirs that the
    morning names (the pack's, for the Illusionist), or to a target immune in silence (the Serial
    Killer; the Necromancer on night 1) when the morning names that attack on no one else; the
    Sigilist and the Healer not when the morning shows their one visit went elsewhere (a sigil's
    attack, the Healer's save)."""
    events = [*morning.deaths, *morning.saves] if morning is not None else []
    on_target = {kind for event in events if event.player == target for kind in event.attacker_types}
    elsewhere = {kind for event in events if event.player != target for kind in event.attacker_types}
    healer_elsewhere = morning is not None and any(save.saver == "healer" and save.player != target
                                                   for save in morning.saves)

    def could(deal: dict[str, str]) -> bool:
        role, target_role = deal[visitor], deal[target]
        if role in NEVER_VISIT or (role in WOLF_ROLES and target_role in WOLF_ROLES):
            return False
        if morning is None:
            return True
        silent = target_role == "serial_killer" or (target_role == "necromancer" and night <= NECROMANCER_IMMUNE_NIGHTS)
        if role == "serial_killer":
            return "serial_killer" in on_target
        if role == "vigilante":  # one shot a night: announced here, or silent here and not announced elsewhere
            return "vigilante" in on_target or (silent and "vigilante" not in elsewhere)
        if role == "illusionist":  # its visits all go to the pack's victim
            return "wolves" in on_target or (silent and "wolves" not in elsewhere)
        if role == "sigilist":
            return "sigilist" not in elsewhere
        if role == "healer":
            return not healer_elsewhere
        return True

    return could

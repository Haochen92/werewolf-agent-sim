"""Catalogue F3 and F7 as items (grade certain), from one view's candidate roles.

- F3, the census half (claims are slices 9 to 11): which evil and neutral roles are dead, which are
  alive and who could hold them, a hidden body included. One item for the wolves and the lone
  killer, one for the neutral. A role the receiver holds, or its pack, is left out: it knows them.
  When the role's holder could have been a hidden body but acted after it died, the line says so.
- F7: what a living player, or a hidden body, could still be, when that is less than the census
  leaves everyone (a role pinned on one player aside), or a single role. The full list, never a
  part of it.
"""

from __future__ import annotations

from Agents.deduction.candidates import wording
from Agents.schemas.deduction import Candidates, DeductionItem, HeldBy, RoleIn, Source, SourceEvent
from Agents.schemas.game_events import DeathRecord
from Agents.schemas.roles import LONE_KILLER, NEUTRAL, ROLE_SPECS, WOLVES


def candidate_items(candidates: Candidates, dead_roster: list[DeathRecord], night: int,
                    informative: bool = False, public: Candidates | None = None) -> list[DeductionItem]:
    """`informative` (the deduction blocks, Agents/deduction/render.py): leave out what tells the
    view nothing. A census clause naming every player whose role the view does not know (rule 1);
    and for a seat, given the public's candidates, an F7 line that is the public's minus the seat
    and its pack (rule 2), which the seat reads in the public block already. The census itself is
    shown in the seat block only, so it is never the public's repeated."""
    keep = _clause_filter(candidates) if informative else None
    return census_items(candidates, dead_roster, night, keep) + roles_left_items(candidates, night,
                                                                                  public if informative else None)


def _dealt(candidates: Candidates, side: str) -> list[str]:
    """The roles of `side` in this cast, in the rules block's order."""
    held = set().union(*candidates.roles.values())
    return [role for role, spec in ROLE_SPECS.items() if spec.side == side and role in held]


# --- F3 -----------------------------------------------------------------------------------------

class _Clause:
    """One clause of a census line: its sentence, its facts and what they rest on. `holders` are the
    players it names for `roles` (living players and hidden bodies, or the dead player)."""

    def __init__(self, sentence: str, roles: tuple[str, ...], holders: tuple[str, ...], dead: bool = False):
        self.sentence, self.roles, self.holders = sentence, roles, holders
        self.dead = dead  # a form that says the role is dead (revealed, or a hidden body): never noise
        self.facts: list[HeldBy] = []
        self.sources: dict[Source, None] = {}
        self.derivation: dict[int, SourceEvent] = {}

    def death(self, death: DeathRecord) -> None:
        self.facts.append(HeldBy(death.role, (death.player,)))
        self.sources[Source("dead_roster", death.day, death.player)] = None
        self.derivation[id(death)] = death


def census_items(candidates: Candidates, dead_roster: list[DeathRecord], night: int,
                 keep=None) -> list[DeductionItem]:
    """One item for the wolves and the lone killer, one for the neutral, each its clauses joined;
    `keep` (a clause filter) leaves clauses out, and a line left with none is not emitted."""
    revealed = {death.role: death for death in dead_roster if not death.concealed}
    evil: list[_Clause] = []
    wolves = _dealt(candidates, WOLVES)
    dead_wolves = [death for death in dead_roster if not death.concealed and death.role in wolves]
    if len(wolves) == 2 and len(dead_wolves) == 2:
        clause = _Clause(wording.both_wolves_dead([death.player for death in dead_wolves]), tuple(wolves),
                         tuple(death.player for death in dead_wolves), dead=True)
        for death in dead_wolves:
            clause.death(death)
        evil.append(clause)
    else:
        for death in dead_wolves:
            clause = _Clause(wording.one_wolf_dead(death.player, death.role), (death.role,), (death.player,),
                             dead=True)
            clause.death(death)
            evil.append(clause)
    both_alive = _both_wolves_alive(wolves, candidates)
    if both_alive is not None:
        evil.append(both_alive)
    else:
        for role in wolves:
            if role not in revealed:
                evil += _alive_or_hidden(role, candidates)
    for role in _dealt(candidates, LONE_KILLER):
        evil += _role_line(role, candidates, revealed)
    neutral: list[_Clause] = []
    for role in _dealt(candidates, NEUTRAL):
        neutral += _role_line(role, candidates, revealed)

    items = []
    for clauses in (evil, neutral):
        clauses = [clause for clause in clauses if keep is None or keep(clause)]
        if not clauses:
            continue
        sources: dict[Source, None] = {}
        derivation: dict[int, SourceEvent] = {}
        for clause in clauses:
            sources.update(clause.sources)
            derivation.update(clause.derivation)
        items.append(DeductionItem(row="F3", subject=None, night=night,
                                   conclusion=tuple(fact for clause in clauses for fact in clause.facts),
                                   text=" ".join(clause.sentence for clause in clauses), sources=tuple(sources),
                                   derivation=tuple(derivation.values()), receiver=candidates.receiver))
    return items


def _both_wolves_alive(wolves: list[str], candidates: Candidates) -> _Clause | None:
    """One sentence for both wolves when neither can be a hidden body and the same players can be
    either: "Both wolves are alive and are two of …"."""
    if len(wolves) != 2 or any(candidates.roles[player] <= set(wolves) for player in candidates.known):
        return None  # a wolf is revealed, or the receiver knows the pack
    holders = [[player for player in candidates.living if role in candidates.roles[player]] for role in wolves]
    on_bodies = any(set(wolves) & candidates.roles[body] for body in candidates.hidden_bodies)
    if on_bodies or holders[0] != holders[1]:
        return None
    clause = _Clause(wording.both_wolves_alive(holders[0]), tuple(wolves), tuple(holders[0]))
    for role in wolves:
        clause.facts.append(HeldBy(role, tuple(holders[0])))
        _add_removal_sources(clause, role, candidates)
    return clause


def _add_removal_sources(clause: _Clause, role: str, candidates: Candidates) -> None:
    for removals in candidates.removals.values():
        for removal in removals:
            if removal.role == role:
                clause.sources.update(dict.fromkeys(removal.sources))
                clause.derivation.update({id(event): event for event in removal.derivation})


def _role_line(role: str, candidates: Candidates, revealed: dict[str, DeathRecord]) -> list[_Clause]:
    if role in revealed:
        death = revealed[role]
        clause = _Clause(wording.role_dead(role, death.player), (role,), (death.player,), dead=True)
        clause.death(death)
        return [clause]
    return _alive_or_hidden(role, candidates)


def _alive_or_hidden(role: str, candidates: Candidates) -> list[_Clause]:
    """Where an unrevealed role is: among the living, or a hidden body. Nothing when the receiver or
    its pack holds it."""
    if any(candidates.roles[player] == {role} for player in candidates.known if player in candidates.living):
        return []
    living = [player for player in candidates.living if role in candidates.roles[player]]
    bodies = [body for body in candidates.hidden_bodies if role in candidates.roles[body]]
    dead = False
    if bodies and living:
        sentence = wording.alive_or_hidden_body(role, living, bodies)
    elif bodies:
        sentence, dead = wording.dead_as_hidden_body(role, bodies), True
    elif role in candidates.alive_reasons:
        reason = candidates.alive_reasons[role]
        sentence = wording.alive_because(role, wording.alive_reason(reason.deed, reason.night, reason.target), living)
    else:
        sentence = wording.alive_and_one_of(role, living)
    clause = _Clause(sentence, (role,), tuple(living + bodies), dead=dead)
    clause.facts.append(HeldBy(role, tuple(living + bodies)))
    _add_removal_sources(clause, role, candidates)
    return [clause]


def _clause_filter(candidates: Candidates):
    """The clauses worth showing (the coordinator's ruling on slice 8, 2026-10-17): not one that names
    every player whose role the view does not know, living or a hidden body; it says only what the
    census of roles in play says ("Both wolves are alive and are two of" every unknown player). A
    form that a role is dead always stays, and so does a list that leaves out one unknown player or
    one hidden body (AC2: the Serial Killer cannot be player_1's body)."""
    unknown = {player for player in [*candidates.living, *candidates.hidden_bodies] if player not in candidates.known}

    def keep(clause: _Clause) -> bool:
        return clause.dead or not set(clause.holders) >= unknown

    return keep


# --- F7 -----------------------------------------------------------------------------------------

def roles_left_items(candidates: Candidates, night: int, public: Candidates | None = None) -> list[DeductionItem]:
    """A player pinned to one role always gets its line; any other only when it has lost a role
    that is still open for someone (a role pinned on another player is no news about this one).
    Given the public's candidates (a seat's block), a line that is the public's list less the seat's
    own role and its pack's is left out: the public block has it."""
    pinned = {next(iter(roles)) for player, roles in candidates.roles.items()
              if len(roles) == 1 and player not in candidates.known}
    open_roles = candidates.census - pinned
    own_roles = set().union(*(candidates.roles[player] for player in candidates.known if player in candidates.living))
    items = []
    for player in [*candidates.living, *candidates.hidden_bodies]:
        roles = candidates.roles[player]
        if player in candidates.known or not (len(roles) == 1 or roles < open_roles):
            continue
        if public is not None and roles == public.roles.get(player, frozenset()) - own_roles:
            continue
        in_order = [role for role in ROLE_SPECS if role in roles]
        if player in candidates.living:
            text = wording.can_only_be(player, in_order)
        else:
            text = wording.hidden_role_can_only_be(player, in_order)
        sources: dict[Source, None] = {}
        derivation: dict[int, SourceEvent] = {}
        for removal in candidates.removals[player]:
            sources.update(dict.fromkeys(removal.sources))
            derivation.update({id(event): event for event in removal.derivation})
        items.append(DeductionItem(row="F7", subject=player, night=night, conclusion=(RoleIn(player, roles),),
                                   text=text, sources=tuple(sources), derivation=tuple(derivation.values()),
                                   receiver=candidates.receiver))
    return items

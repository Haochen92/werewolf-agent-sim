"""What the candidate roles are built from (catalogue Table F, "How the engine derives them"): the
census (C1), with each hidden body restricted by how it was hidden (L8), and every certain fact the
engine already states, read as a constraint on roles. Facts are read, never sentences.

How each fact narrows roles:
- RoleIn: the player's role is one of those roles (most rows of Tables A and B, and C9's
  eliminations from attacks and saves, which the public rows already state).
- A visit under a living player's own name (WentTo): it is not the Necromancer, whose visits show a
  body's name, and not a neutral, which never visits (C10). A name that was already dead is a body.
- Carrying the pack's kill, attacking in one's own name, killing through a body, being roleblocked:
  the roles that can do or suffer that.
- An action that went ahead on night n (a kill or another act through a body, a roleblock, a
  protection, a visit by a named role or by a wolf when the other wolf was revealed dead before
  that night, a pick): its maker was alive at the start of night n, so it is not a body that died
  before then (C18, "a role whose holder must be alive").
- An attack or save a watch shows was made by one of the players seen (MadeBy): one of them holds
  that role (C6).
The other facts are about actions, not roles, and narrow nothing here: AttackOutcome, NoVisitTo,
NotRoleUnlessBlocked (it needs whether a block happened), NoAttackUnless, VisitorsAmong,
CarriedOrAmong, NotProtected, NoHiddenVisitTo, AttacksOnlyOn, NoKillThroughBody, NoConcealsLeft,
MadeNoChoice, NeverPicked, BodyUsable, SilentAttack (its immune role is the Serial Killer, never a
body, or the Necromancer on night 1, when no one has died yet), and HeldBy (this level's own output).
"""

from __future__ import annotations

from Agents.deduction.morning import announcement_of, death_of
from Agents.deduction.night_state import deaths_before_night
from Agents.deduction.own_results.at_the_door import DOER_ROLES
from Agents.rules.night_record import PACK_ACTOR
from Agents.schemas.deduction import (
    ActedThroughBody,
    AliveAtNight,
    AttackedInOwnName,
    BlockedBy,
    CarriedPackKill,
    HolderAmong,
    KilledThroughBody,
    MadeBy,
    OnlyRoles,
    PickMade,
    ProtectedBy,
    RoleConstraint,
    RoleIn,
    SeatView,
    Source,
    SourceEvent,
    Visited,
    WentTo,
)
from Agents.schemas.game_events import DeathRecord
from Agents.schemas.role_traits import (
    ATTACK_IN_OWN_NAME,
    BLOCKER,
    BODY_USER,
    UNBLOCKABLE,
    WOLF_ROLES,
    roles_acting,
    silently_immune,
)
from Agents.schemas.role_traits import NEVER_VISIT_UNDER_OWN_NAME as _NEVER_VISIT
from Agents.schemas.roles import BORROWED_ABILITY, ROLE_SPECS

NECROMANCER = BODY_USER
"""Acts only through bodies: a kill through a body is its, and it cannot act on itself."""
ILLUSIONIST = roles_acting("conceal")[0]
HEALER = roles_acting("protect")[0]
SPECULATOR = roles_acting("pick")[0]
NEVER_VISIT_UNDER_OWN_NAME = frozenset(_NEVER_VISIT)
"""The Necromancer's visits show a body's name; the neutrals never visit (catalogue C10)."""
DEED = {"protect": "protected", "conceal": "went_to"}
"""What a role's visit to a player did, by its night action; any other visit there was an attack."""


class Provenance:
    """Where a fact came from: the row that stated it, its sources and source events."""

    def __init__(self, rule: str, sources: tuple[Source, ...], derivation: tuple[SourceEvent, ...]):
        self.rule, self.sources, self.derivation = rule, sources, derivation


# --- the census (C1, L8) ----------------------------------------------------------------------

def census_constraints(dead_roster: list[DeathRecord], view: SeatView, dealt: frozenset[str]) -> list[OnlyRoles]:
    """C1: a hidden body died at night, so it was not immune that night (never the Serial Killer;
    never the Necromancer on night 1), and L8 narrows it by how it was hidden: the living
    Illusionist hides only the pack's victim, never a wolf; a reanimated Illusionist's conceal
    hides anyone but the Necromancer (it cannot act on itself) and the Illusionist (its body)."""
    constraints = []
    for death in dead_roster:
        if not death.concealed:
            continue
        sources: tuple[Source, ...] = (Source("dead_roster", death.day, death.player),)
        derivation: tuple[SourceEvent, ...] = (death,)
        ruled_out = set(silently_immune(death.day))
        rule = "C1"
        morning = announcement_of(view, death.day)
        announced = death_of(morning, death.player) if morning is not None else None
        if announced is not None and announced.hidden_by:
            sources += (Source("announcement", death.day, death.player),)
            derivation += (announced,)
            rule = "C1+L8"
            if announced.hidden_by == "illusionist":
                ruled_out |= WOLF_ROLES
            elif announced.hidden_by == "reanimated_illusionist":
                ruled_out |= {NECROMANCER, ILLUSIONIST}
        constraints.append(OnlyRoles(death.player, dealt - ruled_out, rule, sources, derivation))
    return constraints


# --- facts as constraints ---------------------------------------------------------------------

def fact_constraints(fact, night: int, where: Provenance, dead_roster: list[DeathRecord],
                     dealt: frozenset[str]) -> list[RoleConstraint]:
    """The role constraints one certain fact about night `night` states; [] for a fact about
    actions alone."""
    if isinstance(fact, RoleIn):
        return [_only(fact.player, fact.roles, where)]
    if isinstance(fact, CarriedPackKill):
        return [_only(fact.player, WOLF_ROLES, where)]
    if isinstance(fact, AttackedInOwnName):
        return [_only(fact.player, ATTACK_IN_OWN_NAME, where)]
    if isinstance(fact, KilledThroughBody):
        return [_only(fact.player, frozenset({NECROMANCER}), where),
                _alive(NECROMANCER, night, "killed_through_body", None, where)]
    if isinstance(fact, WentTo):
        return _went_to(fact, night, where, dead_roster, dealt)
    if isinstance(fact, ActedThroughBody):
        deed = "killed_through_body" if _body_kills(fact.body, dead_roster) else "acted_through_body"
        return [_only(fact.target, dealt - {NECROMANCER}, where),
                _alive(NECROMANCER, night, deed, fact.target, where)]
    if isinstance(fact, BlockedBy):
        return _blocked(fact, night, where, dealt)
    if isinstance(fact, ProtectedBy):
        return [_alive(NECROMANCER if fact.through_body else HEALER, night, "protected", fact.player, where)]
    if isinstance(fact, Visited):
        return _one_of_them_alive(fact.roles, night, fact.target, where, dead_roster)
    if isinstance(fact, MadeBy):
        return _made_by(fact, night, where, dead_roster)
    if isinstance(fact, PickMade):
        return [_alive(SPECULATOR, night, "picked", None, where)]
    return []


def _only(player: str, roles: frozenset[str], where: Provenance) -> OnlyRoles:
    return OnlyRoles(player, frozenset(roles), where.rule, where.sources, where.derivation)


def _alive(role: str, night: int, deed: str, target: str | None, where: Provenance) -> AliveAtNight:
    return AliveAtNight(role, night, deed, target, where.rule, where.sources, where.derivation)


def _went_to(fact: WentTo, night: int, where: Provenance, dead_roster: list[DeathRecord],
             dealt: frozenset[str]) -> list[RoleConstraint]:
    """C10, for a living visitor only: a name dead before the night is a body the Necromancer used."""
    if fact.visitor in {death.player for death in deaths_before_night(dead_roster, night)}:
        return []
    return [OnlyRoles(fact.visitor, dealt - NEVER_VISIT_UNDER_OWN_NAME, f"{where.rule}+C10", where.sources,
                      where.derivation)]


def _body_kills(body: str, dead_roster: list[DeathRecord]) -> bool:
    """Whether the Necromancer's action through `body` was a kill: through the Illusionist's or the
    Vigilante's body every action is."""
    role = next((death.role for death in dead_roster if death.player == body and not death.concealed), None)
    return BORROWED_ABILITY.get(role or "") == "kill"


def _blocked(fact: BlockedBy, night: int, where: Provenance, dealt: frozenset[str]) -> list[RoleConstraint]:
    """A block takes on Town and wolves only, and the blocker was alive that night: the Chanteuse,
    or the Necromancer through her body."""
    blocker = NECROMANCER if fact.through_body else BLOCKER
    if fact.player == PACK_ACTOR:
        return [_alive(blocker, night, "roleblocked_the_carrier", None, where)]
    blockable = frozenset(role for role in dealt if role not in UNBLOCKABLE)
    return [_only(fact.player, blockable, where), _alive(blocker, night, "roleblocked", fact.player, where)]


def _made_by(fact: MadeBy, night: int, where: Provenance, dead_roster: list[DeathRecord]) -> list[RoleConstraint]:
    """C6: the attack (or the living Healer's save) was made by one of the players the watch saw."""
    roles = DOER_ROLES.get(fact.action)
    if roles is None:
        return []
    constraints: list[RoleConstraint] = [HolderAmong(fact.players, roles, where.rule, where.sources, where.derivation)]
    return constraints + _one_of_them_alive(roles, night, fact.target, where, dead_roster)


def _one_of_them_alive(roles: frozenset[str], night: int, target: str, where: Provenance,
                       dead_roster: list[DeathRecord]) -> list[RoleConstraint]:
    """A holder of one of `roles` went to `target` on night `night`, so it was alive then. For the
    wolves: when the other wolf was revealed dead before that night, it was this one."""
    revealed_before = {death.role for death in deaths_before_night(dead_roster, night) if not death.concealed}
    left = roles - revealed_before
    if len(left) != 1:
        return []
    (role,) = left
    deed = DEED.get(ROLE_SPECS[role].night_action, "attacked")
    return [_alive(role, night, deed, target, where)]

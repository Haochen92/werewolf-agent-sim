"""What each role is, as the deduction engine reasons about it: one row of traits per role of the pool.

`ROLE_SPECS` (roles.py) is what the engine needs to run a role (its side, its night action, its
uses, its decline word); this table is what the deduction rows need to reason about one: whether it
can be killed at night, whether a block takes on it, whose name its visits show, whether it reads
Suspicious, and the words a line names it with. The rows (Agents/deduction/) ask the table ("the
roles that never visit in their own name") instead of naming roles, so a new role is declared here
once. The night engine (Agents/rules/night.py) is the authority: tests/engine/deduction/
test_role_traits.py resolves real nights and fails on any trait the engine disagrees with.

How to add a role: Agents/deduction/__init__.py (and the catalogue's Build status).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from Agents.schemas.roles import BORROWED_ABILITY, NECROMANCER_IMMUNE_NIGHTS, ROLE_SPECS

NightImmunity = Literal["never", "always", "first_nights", "self_bet"]
VisitName = Literal["own_name", "under_body", "never"]
SuspiciousReading = Literal["always", "when_killing_through_body", "never"]


@dataclass(frozen=True)
class RoleTraits:
    """One role's properties, as the deduction rows read them (catalogue §0.1, lemmas L1–L10)."""

    title: str
    """How a line names the role: "the Serial Killer"."""
    night_immune: NightImmunity
    """When an attack on it fails: never; always (in silence); on its first nights only, 1 to
    NECROMANCER_IMMUNE_NIGHTS (in silence); or on a
    night it bets on itself (announced, R10). Catalogue L1."""
    blockable: bool
    """Whether a roleblock on it takes effect (cancels its action). Catalogue L2."""
    blocks: bool
    """Whether its own night action is a roleblock. A body that gives a block is BORROWED_ABILITY's."""
    visits: VisitName
    """Whose name a watch or a follow shows for its visits: its own; a dead body's, never its own; or
    none, since its action is no visit. Catalogue L4, C10."""
    visits_two: bool
    """Whether it can visit two players on one night (the Chanteuse carrying the pack's kill and
    blocking someone else). Catalogue L4, A34."""
    attacks_in_own_name: bool
    """Whether it can attack someone under its own name: what makes a sigil strike back. Catalogue L6."""
    attack_announced_as: str | None
    """The attacker type the morning names for an attack it makes itself (a kill, or the sigil's
    strike); None for a role that makes none. A wolf's is the pack's: "wolves"."""
    reads_suspicious: SuspiciousReading
    """What an Investigator's check on it reads: Suspicious always; only on a night it killed through
    a body; or never. Catalogue L7."""
    must_act: bool
    """Whether it has no word to decline its night action, so it acts every night it is alive.
    Catalogue L5."""
    borrowed_verb: str | None
    """What the Necromancer does to its target through this role's body ("shoot"); None for a body
    that gives nothing."""


ROLE_TRAITS: dict[str, RoleTraits] = {
    # Town
    "investigator": RoleTraits(
        title="the Investigator", night_immune="never", blockable=True, blocks=False, visits="own_name",
        visits_two=False, attacks_in_own_name=False, attack_announced_as=None, reads_suspicious="never",
        must_act=False, borrowed_verb="check"),
    "sentinel": RoleTraits(
        title="the Sentinel", night_immune="never", blockable=True, blocks=False, visits="own_name",
        visits_two=False, attacks_in_own_name=False, attack_announced_as=None, reads_suspicious="never",
        must_act=False, borrowed_verb="watch"),
    "trailseer": RoleTraits(
        title="the Trailseer", night_immune="never", blockable=True, blocks=False, visits="own_name",
        visits_two=False, attacks_in_own_name=False, attack_announced_as=None, reads_suspicious="never",
        must_act=True, borrowed_verb="follow"),
    "vigilante": RoleTraits(
        title="the Vigilante", night_immune="never", blockable=True, blocks=False, visits="own_name",
        visits_two=False, attacks_in_own_name=True, attack_announced_as="vigilante", reads_suspicious="never",
        must_act=False, borrowed_verb="shoot"),
    "sigilist": RoleTraits(
        title="the Sigilist", night_immune="never", blockable=True, blocks=False, visits="own_name",
        visits_two=False, attacks_in_own_name=False, attack_announced_as="sigilist", reads_suspicious="never",
        must_act=False, borrowed_verb="set a sigil on"),
    "healer": RoleTraits(
        title="the Healer", night_immune="never", blockable=True, blocks=False, visits="own_name",
        visits_two=False, attacks_in_own_name=False, attack_announced_as=None, reads_suspicious="never",
        must_act=True, borrowed_verb="protect"),
    # Wolves
    "chanteuse": RoleTraits(
        title="the Chanteuse", night_immune="never", blockable=True, blocks=True, visits="own_name",
        visits_two=True, attacks_in_own_name=True, attack_announced_as="wolves", reads_suspicious="always",
        must_act=True, borrowed_verb="block"),
    "illusionist": RoleTraits(
        title="the Illusionist", night_immune="never", blockable=True, blocks=False, visits="own_name",
        visits_two=False, attacks_in_own_name=True, attack_announced_as="wolves", reads_suspicious="always",
        must_act=False, borrowed_verb="attack"),
    # The lone killers
    "serial_killer": RoleTraits(
        title="the Serial Killer", night_immune="always", blockable=False, blocks=False, visits="own_name",
        visits_two=False, attacks_in_own_name=True, attack_announced_as="serial_killer", reads_suspicious="never",
        must_act=True, borrowed_verb=None),
    "necromancer": RoleTraits(
        title="the Necromancer", night_immune="first_nights", blockable=False, blocks=False, visits="under_body",
        visits_two=False, attacks_in_own_name=False, attack_announced_as=None,
        reads_suspicious="when_killing_through_body", must_act=False, borrowed_verb=None),
    # The neutrals
    "speculator": RoleTraits(
        title="the Speculator", night_immune="never", blockable=False, blocks=False, visits="never",
        visits_two=False, attacks_in_own_name=False, attack_announced_as=None, reads_suspicious="never",
        must_act=False, borrowed_verb=None),
    "fortune_teller": RoleTraits(
        title="the Fortune Teller", night_immune="self_bet", blockable=False, blocks=False, visits="never",
        visits_two=False, attacks_in_own_name=False, attack_announced_as=None, reads_suspicious="never",
        must_act=True, borrowed_verb=None),
}
"""Every role of the pool, in the pool's order (the rules block's). Retired roles have no row."""


def roles_with(**traits) -> tuple[str, ...]:
    """The roles whose traits have the given values, in the pool's order: roles_with(visits="never")."""
    return tuple(role for role, row in ROLE_TRAITS.items()
                 if all(getattr(row, name) == value for name, value in traits.items()))


def the_role(**traits) -> str:
    """The role with the given traits, for a row written about one role (the table's tests check
    that exactly one role has them)."""
    return roles_with(**traits)[0]


def roles_acting(night_action: str) -> tuple[str, ...]:
    """The roles whose own night action is `night_action` (RoleSpec), in the pool's order."""
    return tuple(role for role in ROLE_TRAITS if ROLE_SPECS[role].night_action == night_action)


WOLF_ROLES = frozenset(role for role in ROLE_TRAITS if ROLE_SPECS[role].pack)
"""The pack's roles: they share the kill, and a check reads them Suspicious."""
UNBLOCKABLE = roles_with(blockable=False)
"""The roles a block does not take on, in the pool's order."""
NEVER_VISIT_UNDER_OWN_NAME = tuple(role for role, row in ROLE_TRAITS.items() if row.visits != "own_name")
"""The roles no watch or follow ever shows under their own name, in the pool's order."""
ATTACK_IN_OWN_NAME = frozenset(roles_with(attacks_in_own_name=True))
"""Who can attack under their own name: the roles a sigil strikes back at (L6)."""
STRUCK_BY_SIGIL = frozenset(role for role in ATTACK_IN_OWN_NAME if ROLE_TRAITS[role].night_immune != "always")
"""Who a sigil can strike and harm: those attacking under their own name, less the always immune."""


# The roles some rows are written about, one each (their wording names them; the tests check that
# exactly one role has the trait).
BLOCKER = the_role(blocks=True)
"""The role whose own night action is a roleblock: the Chanteuse."""
BODY_USER = the_role(visits="under_body")
"""The role that acts only through the dead, under their names: the Necromancer."""
VISITS_TWO = the_role(visits_two=True)
"""The role that can visit two players in one night: the Chanteuse carrying the pack's kill."""
SUSPICIOUS_THROUGH_A_BODY = the_role(reads_suspicious="when_killing_through_body")
"""The role a check reads Suspicious only on a night it killed through a body: the Necromancer."""


def silently_immune(night: int) -> frozenset[str]:
    """The roles an attack fails on in silence on `night`, whatever they chose: the always immune,
    and on the first nights the first-nights immune (a self-bet's save is announced, R10)."""
    kinds = ("always", "first_nights") if night <= NECROMANCER_IMMUNE_NIGHTS else ("always",)
    return frozenset(role for role, row in ROLE_TRAITS.items() if row.night_immune in kinds)


def announced_as(attack_type: str) -> frozenset[str]:
    """The roles whose own attack the morning names `attack_type`."""
    return frozenset(roles_with(attack_announced_as=attack_type))


OWN_ATTACK_TYPES = tuple(dict.fromkeys(row.attack_announced_as for row in ROLE_TRAITS.values()
                                       if row.attack_announced_as))
"""Every attacker type a morning names for an attack made under the attacker's own name."""
BODY_OF_ATTACK_TYPE = {"reanimated_" + row.attack_announced_as: role for role, row in ROLE_TRAITS.items()
                       if row.attack_announced_as and BORROWED_ABILITY.get(role) in ("kill", "sigil")}
"""The role whose body an attack made through a body was made through, by the attacker type the
morning names it: an attack through a body is the body's own attack, reanimated."""

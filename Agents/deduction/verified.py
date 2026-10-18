"""What the deduction engine has been verified for: the roles and the use limits its rows assume.

Every row in the catalogue (evidence/reasoning_failures/deduction_catalogue.md) was proved for these
twelve roles and the standard limits ("Configuration scope"). A new role can break a line that says
"only X can…" in every game that deals it, and a different limit breaks the count rows, so a game
outside this scope gets no deduction at all rather than a possibly false line (owner, 2026-10-17).
Adding a role means verifying the engine for it first, then adding it here.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # a runtime import would close a cycle: Agents.config imports the deduction package
    from Agents.config.game import GameConfig

VERIFIED_ROLES = frozenset({
    "investigator", "sentinel", "trailseer", "vigilante", "sigilist", "healer",
    "chanteuse", "illusionist",
    "serial_killer", "necromancer",
    "speculator", "fortune_teller",
})

VERIFIED_LIMITS = {
    "investigator_checks": 2,
    "sentinel_watches": 2,
    "sigils": 2,
    "conceals": 2,
    "self_bets": 2,
}
"""The public limits the count rows use (C5, C17, C20, E11). The vigilante's bullets are not
public (R7), so no row reads them and any number is fine."""


def roles_verified(lineup: Iterable[str]) -> bool:
    """Whether every dealt role is one the engine was verified for."""
    return set(lineup) <= VERIFIED_ROLES


def limits_verified(config: "GameConfig") -> bool:
    """Whether the game's use limits are the ones the count rows assume."""
    return all(getattr(config, field) == value for field, value in VERIFIED_LIMITS.items())

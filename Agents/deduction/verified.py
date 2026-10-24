"""The roles and use limits the deduction engine has been verified for.

Every rule in the engine was proved only for these twelve roles and the standard use limits. A new
role can make a line that says "only X can…" false in every game that deals it, and a different
limit breaks the lines that count uses. So a game outside this scope gets no deduction at all, rather
than a line that might be false. To add a role, verify the engine for it first (the steps are in
Agents/deduction/__init__.py), then add it here.
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
"""The use limits the counting lines assume, such as "player_5's self-bet has saved it twice, so it
has none left". The Vigilante's bullets are not here: how many it has left is never made public, so
no line reads them and any number is fine."""


def roles_verified(lineup: Iterable[str]) -> bool:
    """Returns True when every role dealt this game is one the engine was verified for."""
    return set(lineup) <= VERIFIED_ROLES


def limits_verified(config: "GameConfig") -> bool:
    """Returns True when the game's use limits are the ones the counting lines assume."""
    return all(getattr(config, field) == value for field, value in VERIFIED_LIMITS.items())

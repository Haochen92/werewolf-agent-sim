"""Game vocabulary: the role set, the action phases, and which roles act in which phase.

The fixed domain facts of the 9-player/3-faction game (not run-time config — that's
``Agents/game_config.py``). Drives the memory-namespace iteration (every
``(memory_kind, role, action_phase)`` combination) and the ``ActionPhase`` typing
across schemas.
"""

from dataclasses import dataclass
from typing import Literal

roles = ["villager", "wolf", "investigator", "healer", "serial_killer", "vigilante"]


@dataclass(frozen=True)
class RoleSpec:
    """Declarative facts about a role — the single source the prompt layer composes each role's
    cross-faction awareness from (see Agents/prompts/roles.threat_brief), so adding a role is ONE
    entry here, not a hunt through every prompt for "where do I mention the other factions". Also
    the intended source for win-logic / night-routing / markers as those migrate onto it."""

    name: str
    faction: str
    """Which faction this role wins with: "village" | "wolves" | "serial_killer"."""
    night_action: str | None = None
    """The role's night capability: "kill" | "protect" | "investigate" | None (no night action)."""
    night_immune: bool = False
    """True if this role cannot be removed by a night kill (only a daytime vote) — the SK."""


ROLE_SPECS: dict[str, RoleSpec] = {
    "villager": RoleSpec("villager", "village"),
    "healer": RoleSpec("healer", "village", night_action="protect"),
    "investigator": RoleSpec("investigator", "village", night_action="investigate"),
    "vigilante": RoleSpec("vigilante", "village", night_action="kill"),
    "wolf": RoleSpec("wolf", "wolves", night_action="kill"),
    "serial_killer": RoleSpec("serial_killer", "serial_killer", night_action="kill", night_immune=True),
}

ActionPhase = Literal["day_discussion", "day_vote", "night_action"]
ACTION_PHASES: list[str] = ["day_discussion", "day_vote", "night_action"]

VALID_ACTION_PHASES_BY_ROLE: dict[str, list[str]] = {
    "villager": ["day_discussion", "day_vote"],
    "wolf": ["day_discussion", "day_vote", "night_action"],
    "healer": ["day_discussion", "day_vote", "night_action"],
    "investigator": ["day_discussion", "day_vote", "night_action"],
    "serial_killer": ["day_discussion", "day_vote", "night_action"],
    "vigilante": ["day_discussion", "day_vote", "night_action"],
}
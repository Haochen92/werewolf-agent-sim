"""Game vocabulary: the role set, the action phases, and which roles act in which phase.

The fixed domain facts of the 9-player/3-faction game (not run-time config — that's
``Agents/game_config.py``). Drives the memory-namespace iteration (every
``(memory_kind, role, action_phase)`` combination) and the ``ActionPhase`` typing
across schemas.
"""

from dataclasses import dataclass
from typing import Literal

roles = ["villager", "wolf", "investigator", "healer", "serial_killer", "vigilante"]

# Role-guess vocabulary for a per-player "read": every castable role, plus "unclear" for no call.
# Reconstructed from `roles` (the single source) so a newly-cast role can never silently drop out of
# the read enum — this is the model-visible enum on Agents.schemas.output.PlayerRead (the T1c reads
# field). Deriving it here, not restating the list in output.py, keeps the two from drifting apart.
READ_ROLE_ENUM = Literal[("unclear", *roles)]


def cast_role_counts(role_map: dict[str, str]) -> dict[str, int]:
    """Public role->count census of a cast (counts only, no identities) — the payload-safe form of
    the true role map. The line-up is common knowledge while the assignment is not, so payload
    builders (day fan-out, single-actor night phases) put THIS on agent payloads to feed the
    alive-roles line (cast minus revealed dead), never ``role_map`` itself."""
    counts: dict[str, int] = {}
    for role in role_map.values():
        counts[role] = counts.get(role, 0) + 1
    return counts


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
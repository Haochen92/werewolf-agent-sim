"""Game vocabulary: the role pool, each role's rules as the engine needs them, the sides, and the
action phases.

The fixed domain facts of the ten-seat game (not run-time config — that is ``Agents/config/game.py``).
The role sheet (evidence/game_play_enhancement/role_sheet.md) is the ruling; this table is what the
engine reads of it: who is on which side, what a role does at night and from which night, how many
uses it has, the word that declines its action, and the field its night answer comes back in.
Everything else about a role (its words) is on its card in ``Agents/prompts/roles/``.
"""

from dataclasses import dataclass
from typing import Literal

# The sides, as the cards spell them.
TOWN = "town"
WOLVES = "wolves"
LONE_KILLER = "lone_killer"
NEUTRAL = "neutral"
SIDES = (TOWN, WOLVES, LONE_KILLER, NEUTRAL)

# What a night action does, as the night layer resolves it (Agents/rules/night.py). "hold_fire"
# is the vigilante's recorded decline; "borrow" is the necromancer's choice before it becomes the
# body's own kind; "pick" and "bet" are the neutrals' choices, which are not visits.
NightKind = Literal[
    "kill", "protect", "investigate", "watch", "follow", "sigil", "block", "conceal",
    "hold_fire", "borrow", "pick", "bet",
]


@dataclass(frozen=True)
class RoleSpec:
    """One role's rules, the engine's reading of the sheet."""

    name: str
    side: str
    """town | wolves | lone_killer | neutral."""
    night_action: NightKind | None = None
    """What the role does at night; None for a role that never acts (none in the pool)."""
    target_field: str = ""
    """The field of its night output that carries the choice, and the turn's output key."""
    no_action: str = ""
    """The word that declines the action; "" when the role must act."""
    uses: int | None = None
    """How many times the ability may be used in a game; None = every night. The fortune
    teller's uses are its self-bets: its ordinary bet goes on without them (ACTS_WHEN_SPENT)."""
    acts_from_night: int = 1
    """The first night the role acts (the necromancer sits out night 1)."""
    night_immune: bool = False
    """Cannot be killed at night, on every night (the serial killer). The necromancer's night 1
    is in Agents/rules/night.is_night_immune."""
    pack: bool = False
    """A wolf: shares the pack's chat and kill, and the target_field is its own skill's."""
    retired: bool = False
    """A role the nine-seat game dealt and the ten-seat game does not. Kept so old replays,
    stores and the hallucination bench still resolve; never dealt, never in the pool."""


ROLE_SPECS: dict[str, RoleSpec] = {
    # Town
    "investigator": RoleSpec("investigator", TOWN, "investigate", "investigator_target"),
    "sentinel": RoleSpec("sentinel", TOWN, "watch", "sentinel_target"),
    "trailseer": RoleSpec("trailseer", TOWN, "follow", "trailseer_target"),
    "vigilante": RoleSpec("vigilante", TOWN, "kill", "vigilante_target", no_action="hold_fire", uses=2),
    "sigilist": RoleSpec("sigilist", TOWN, "sigil", "sigil_target", no_action="keep_sigil", uses=2),
    "healer": RoleSpec("healer", TOWN, "protect", "healer_target"),
    # Wolves: the pack kills through its carrier; each wolf's own field is its skill.
    "chanteuse": RoleSpec("chanteuse", WOLVES, "block", "block_target", pack=True),
    "illusionist": RoleSpec("illusionist", WOLVES, "conceal", "conceal", no_action="no_conceal", uses=2, pack=True),
    # The lone killer's seat, one of two
    "serial_killer": RoleSpec("serial_killer", LONE_KILLER, "kill", "serial_killer_target", night_immune=True),
    "necromancer": RoleSpec("necromancer", LONE_KILLER, "borrow", "necromancer_target", no_action="stay_put", acts_from_night=2),
    # The neutral seat, one of two
    "speculator": RoleSpec("speculator", NEUTRAL, "pick", "speculator_pick", no_action="not_yet", uses=1),
    "fortune_teller": RoleSpec("fortune_teller", NEUTRAL, "bet", "bet_target", uses=2),
    # Retired with the nine-seat deal.
    "villager": RoleSpec("villager", TOWN, retired=True),
    "wolf": RoleSpec("wolf", WOLVES, "kill", retired=True, pack=True),
}

# The pool: every role the ten-seat game can deal, in the order the rules block lists them.
roles = [name for name, spec in ROLE_SPECS.items() if not spec.retired]

# The ten-seat deal (role_sheet.md, "The lineup"): eight seats every game deals, and two seats drawn
# per game from two roles each, unless the user chose one.
FIXED_SEATS = [
    "investigator", "sentinel", "trailseer", "vigilante", "sigilist", "healer",
    "chanteuse", "illusionist",
]
LONE_KILLER_ROLES = ["serial_killer", "necromancer"]
NEUTRAL_ROLES = ["speculator", "fortune_teller"]
SEATS = len(FIXED_SEATS) + 2

# Roles that keep taking their night turn after their limited ability is spent: the fortune
# teller bets every night, and its two uses are self-bets only.
ACTS_WHEN_SPENT = ("fortune_teller",)


def lineup(lone_killer: str, neutral: str) -> list[str]:
    """The ten roles of a game whose drawn seats came out as given, in the rules block's order."""
    return [*FIXED_SEATS, lone_killer, neutral]


# Every lineup a game can deal: two draws of two, so four.
ALL_LINEUPS = [lineup(killer, neutral) for killer in LONE_KILLER_ROLES for neutral in NEUTRAL_ROLES]

# What a dead body gives the necromancer (role_sheet.md, "Necromancer rules"): a wolf body attacks
# or blocks, a town body gives its own ability. A lone killer's or a neutral's body gives nothing,
# and nor does a concealed one.
BORROWED_ABILITY: dict[str, NightKind] = {
    "illusionist": "kill",
    "chanteuse": "block",
    "vigilante": "kill",
    "healer": "protect",
    "sigilist": "sigil",
    "investigator": "investigate",
    "sentinel": "watch",
    "trailseer": "follow",
}

# The sides the speculator may pick, as its output names them, and the wire's winner for each
# side a faction can be (the lone killer's win is named by its role).
PICKABLE_SIDES = ("town", "wolves", "lone_killer", "self")
WINNER_OF_SIDE = {TOWN: "villagers", WOLVES: "wolves"}


def side_of(role: str) -> str:
    """The side a role is on."""
    return ROLE_SPECS[role].side


def roles_on(side: str) -> list[str]:
    """Every role of the pool on a side."""
    return [name for name in roles if ROLE_SPECS[name].side == side]


def role_for_field(target_field: str) -> str | None:
    """The role whose night turn answers in this field; None for a day or pack key."""
    for name, spec in ROLE_SPECS.items():
        if spec.target_field and spec.target_field == target_field:
            return name
    return None


def cast_role_counts(role_map: dict[str, str]) -> dict[str, int]:
    """Public role->count census of a cast (counts only, no identities) — the payload-safe form of
    the true role map. The line-up is common knowledge while the assignment is not, so payload
    builders (day fan-out, single-actor night phases) put THIS on agent payloads to feed the
    alive-roles line (cast minus revealed dead), never ``role_map`` itself."""
    counts: dict[str, int] = {}
    for role in role_map.values():
        counts[role] = counts.get(role, 0) + 1
    return counts


ActionPhase = Literal["day_discussion", "day_vote", "night_action"]
ACTION_PHASES: list[str] = ["day_discussion", "day_vote", "night_action"]

# Every role in the pool speaks, votes and acts at night (the neutrals' pick and bet are night
# actions); the retired villager had no night.
VALID_ACTION_PHASES_BY_ROLE: dict[str, list[str]] = {
    name: (["day_discussion", "day_vote", "night_action"] if spec.night_action else ["day_discussion", "day_vote"])
    for name, spec in ROLE_SPECS.items()
}

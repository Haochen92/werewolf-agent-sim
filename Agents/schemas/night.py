"""The night layer's vocabulary: a choice as a player made it, an attack, and the night's outcome.

Internal records (never sent to a model), read and written by ``Agents/rules/night.py``, which
holds the rules themselves. Attribute docstrings for hover only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from Agents.schemas.roles import NightKind

# How the morning report names an attack from its source
AttackerType = Literal["wolves", "serial_killer", "vigilante", "sigilist", "reanimated_wolves", "reanimated_vigilante", "reanimated_sigilist"]
"""How the morning names an attack. An attack a necromancer made through a body is the body's kind,
reanimated: a kill through a wolf's body, a shot through the vigilante's, a sigil through the
sigilist's (owner, 2026-10-10)."""

# What happened to an attacked player: immune > saved > killed
NightVerdict = Literal["immune", "saved", "killed"]

# The attacker type a role's kill is announced as. A necromancer's borrowed kill is announced as
# the body's would be (the body is what shows), so the pack's roles and the vigilante are here and
# the necromancer is not.
ATTACKER_TYPE_OF_ROLE: dict[str, AttackerType] = {
    "wolf": "wolves",
    "chanteuse": "wolves",
    "illusionist": "wolves",
    "serial_killer": "serial_killer",
    "vigilante": "vigilante",
}


@dataclass(frozen=True)
class NightChoice:
    """One night action as a player chose it, before the rules are applied."""

    actor: str
    """The player acting. For the pack's kill, the carrier wolf (the only wolf who visits)."""
    role: str
    """The actor's own role."""
    kind: NightKind
    """The ability used. For a necromancer, the body's ability (kill, block, ...), never "borrow"."""
    target: str | None
    """The player it is on; None for conceal and hold_fire; the picked side for a pick."""
    via: str | None = None
    """The dead player a necromancer acts through: the name a watcher or follower sees."""
    role_named: str | None = None
    """The role a fortune teller also names on its bet; None for the death alone."""


@dataclass(frozen=True)
class Attack:
    """One attack on a player tonight."""

    attacker: str
    """The player who made it."""
    attacker_type: AttackerType
    """How the morning report names it."""


@dataclass(frozen=True)
class Bet:
    """A fortune teller's bet, settled."""

    actor: str
    target: str
    role_named: str | None
    points: int
    """0, 1 for the death, 2 for the death and the role."""


@dataclass
class NightOutcome:
    """Everything the night decided, read by the records, the morning report and the wire."""

    night: int
    """The night's number (the day it follows)."""
    blocked: list[str]
    """Players whose action was cancelled by a roleblock."""
    blocks_without_effect: list[str]
    """Block targets that cannot be blocked: the block did nothing (the blocker is told so)."""
    visits: list[tuple[str, str]]
    """(visitor, visited) for every action that went ahead on a player, in choice order; a
    necromancer's visit shows its body's name."""
    attackers: list[str]
    """Players who made an attack tonight in their own name (the sigil strikes these; a
    necromancer attacking through a body is not among them)."""
    attacks_on: dict[str, list[Attack]]
    """target -> the attacks on it, in choice order, retaliation last."""
    verdicts: dict[str, NightVerdict]
    """target -> what happened to it, one verdict per attacked player."""
    deaths: list[str]
    """Who died, in seat order."""
    concealed: list[str]
    """Dead players whose role the morning report may not name."""
    suspicious: list[str] = field(default_factory=list)
    """Players who read Suspicious to an investigator tonight: the wolves, and a necromancer on a
    night it attacked."""
    picks: list[tuple[str, str]] = field(default_factory=list)
    """(speculator, side) for a pick made tonight; the morning announces the side, not the seat."""
    bets: list[Bet] = field(default_factory=list)
    """Every fortune teller's bet tonight, settled against the deaths."""
    self_bets: list[str] = field(default_factory=list)
    """Fortune tellers who bet on themselves: unharmed tonight, nothing scored."""


@dataclass(frozen=True)
class NightReport:
    """The night's public outcome, as the resolution node commits it for the wire and the record:
    what the morning report says, in the order it says it."""

    night: int
    deaths: list[tuple[str, str, list[str]]]
    """(player, role or "" if concealed, attacker types) in seat order."""
    saves: list[tuple[str, list[str]]]
    """(player, attacker types) for each announced save, in seat order."""
    pick: str | None
    """The side a speculator picked tonight, announced without the seat; None if none."""

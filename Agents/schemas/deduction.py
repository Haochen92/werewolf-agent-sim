"""What the deduction engine tells a seat: lines computed by code from what the seat knows, never
from hidden state. Specification: evidence/reasoning_failures/deduction_catalogue.md (Table A is
level 1: a seat's own night result and what it implies)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from Agents.schemas.game_events import DeathRecord, NightActionRecord

DeductionMode = Literal["off", "record", "full"]
"""How much of the engine a game's AI seats get, set once per game (RunConfig.deduction_mode):
nothing; the lines beside their own night records (level 1); or those plus the deduction block
(levels 2 to 7, not built yet). A human seat always gets nothing."""

Grade = Literal["certain", "possible"]


@dataclass(frozen=True)
class SeatView:
    """Everything one seat knows, as the engine reads it: built from the seat's own payload and
    nothing else, so no line can rest on what the seat was not told (the leak boundary)."""

    player_id: str
    role: str
    """The seat's own role."""
    cast_role_counts: dict[str, int]
    """The public cast census: how many of each role were dealt."""
    dead_roster: list[DeathRecord]
    """The public dead roster, in death order."""
    night_records: list[NightActionRecord]
    """The seat's own night records (and, for a wolf, the pack's kill records)."""


@dataclass(frozen=True)
class RoleIn:
    """A machine-checkable fact: `player`'s role is one of `roles`. The tests check every emitted
    fact against the true roles of randomly generated nights (the soundness oracle)."""

    player: str
    roles: frozenset[str]


@dataclass(frozen=True)
class BlockedBy:
    """A machine-checkable fact: `player`'s action that night was cancelled by the living
    Chanteuse's block (`through_body` False) or by the Necromancer's block through her body."""

    player: str
    through_body: bool


@dataclass(frozen=True)
class AttackOutcome:
    """A machine-checkable fact about the attacks on `player` that night: either no attack went
    ahead on it, or every attack on it failed because it was immune for one of `immune_as` (a role
    name, or "self_bet" for a fortune teller betting on itself). An empty `immune_as` means no
    attack went ahead."""

    player: str
    immune_as: frozenset[str]


@dataclass(frozen=True)
class ProtectedBy:
    """A machine-checkable fact: a protection went ahead on `player` that night, made by the
    living Healer (`through_body` False) or by the Necromancer through the Healer's body."""

    player: str
    through_body: bool


Fact = RoleIn | BlockedBy | AttackOutcome | ProtectedBy


@dataclass(frozen=True)
class OwnResultLine:
    """What a seat's own night record implies, shown next to that record."""

    text: str
    """The line the seat reads, in plain words naming players and nights."""
    row: str
    """The catalogue row it implements (e.g. "A6"), for tracing a live line back to its rule."""
    grade: Grade = "certain"
    """"possible" for a complete list of explanations ("either … or …")."""
    replaces_outcome: bool = False
    """True when the record's own prose is replaced rather than followed (the roleblock record)."""
    facts: tuple[Fact, ...] = field(default_factory=tuple)
    """The line's content as checkable facts; every one must hold in the real game."""

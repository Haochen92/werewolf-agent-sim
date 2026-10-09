"""Internal resolved-turn contracts between the turn engine and graph actor nodes.

These models are never sent to an LLM. Model-visible structured outputs describe a
player's decision; the models here describe the legal domain action produced after
that decision has passed game-rule resolution. Graph nodes then commit the action to
the appropriate state channel.
"""

from enum import Enum
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

from Agents.schemas.game_events import DayChannel, DayVote, WolfChannel
from Agents.schemas.night import NightChoice
from Agents.schemas.output import MemoryVerdict, PlayerRead, StrategyVerdict


class TurnKind(str, Enum):
    """Finite set of resolved player-action kinds."""

    DAY_DISCUSSION = "day_discussion"
    DAY_VOTE = "day_vote"
    WOLF_DISCUSSION = "wolf_discussion"
    NIGHT_CHOICE = "night_choice"


class _InternalTurnModel(BaseModel):
    """Strict immutable base for internal turn results."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)


class TurnEffects(_InternalTurnModel):
    """Non-action outputs produced alongside a resolved turn."""

    strategy: str | None = None
    reads: list[PlayerRead] = Field(default_factory=list)
    strategy_verdicts: list[StrategyVerdict] = Field(default_factory=list)
    memory_verdicts: list[MemoryVerdict] = Field(default_factory=list)


class ResolvedDayDiscussion(_InternalTurnModel):
    kind: Literal[TurnKind.DAY_DISCUSSION] = TurnKind.DAY_DISCUSSION
    entry: DayChannel | None
    effects: TurnEffects = Field(default_factory=TurnEffects)


class ResolvedDayVote(_InternalTurnModel):
    kind: Literal[TurnKind.DAY_VOTE] = TurnKind.DAY_VOTE
    entry: DayVote
    effects: TurnEffects = Field(default_factory=TurnEffects)


class ResolvedWolfDiscussion(_InternalTurnModel):
    kind: Literal[TurnKind.WOLF_DISCUSSION] = TurnKind.WOLF_DISCUSSION
    entry: WolfChannel
    effects: TurnEffects = Field(default_factory=TurnEffects)


class ResolvedNightChoice(_InternalTurnModel):
    """A night turn's decision as a choice the night layer resolves: the carrier's kill, a solo
    role's action, a wolf's skill. ``entry`` is None when the role declined (keep_sigil,
    no_conceal, stay_put, not_yet); the vigilante's hold_fire is a choice of its own kind."""

    kind: Literal[TurnKind.NIGHT_CHOICE] = TurnKind.NIGHT_CHOICE
    entry: NightChoice | None
    effects: TurnEffects = Field(default_factory=TurnEffects)


ResolvedTurn: TypeAlias = Annotated[
    ResolvedDayDiscussion | ResolvedDayVote | ResolvedWolfDiscussion | ResolvedNightChoice,
    Field(discriminator="kind"),
]


__all__ = [
    "ResolvedDayDiscussion",
    "ResolvedDayVote",
    "ResolvedNightChoice",
    "ResolvedTurn",
    "ResolvedWolfDiscussion",
    "TurnEffects",
    "TurnKind",
]

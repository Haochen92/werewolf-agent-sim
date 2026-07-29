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
from Agents.schemas.output import MemoryVerdict, PlayerRead, StrategyVerdict


class TurnKind(str, Enum):
    """Finite set of resolved player-action kinds."""

    DAY_DISCUSSION = "day_discussion"
    DAY_VOTE = "day_vote"
    WOLF_DISCUSSION = "wolf_discussion"
    WOLF_VOTE = "wolf_vote"
    HEALER_TARGET = "healer_target"
    INVESTIGATOR_TARGET = "investigator_target"
    SERIAL_KILLER_TARGET = "serial_killer_target"
    VIGILANTE_TARGET = "vigilante_target"


class _InternalTurnModel(BaseModel):
    """Strict immutable base for internal turn results."""

    model_config = ConfigDict(frozen=True, extra="forbid")


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


class ResolvedWolfVote(_InternalTurnModel):
    kind: Literal[TurnKind.WOLF_VOTE] = TurnKind.WOLF_VOTE
    entry: WolfChannel
    effects: TurnEffects = Field(default_factory=TurnEffects)


class ResolvedHealerTarget(_InternalTurnModel):
    kind: Literal[TurnKind.HEALER_TARGET] = TurnKind.HEALER_TARGET
    entry: str
    effects: TurnEffects = Field(default_factory=TurnEffects)


class ResolvedInvestigatorTarget(_InternalTurnModel):
    kind: Literal[TurnKind.INVESTIGATOR_TARGET] = TurnKind.INVESTIGATOR_TARGET
    entry: str
    effects: TurnEffects = Field(default_factory=TurnEffects)


class ResolvedSerialKillerTarget(_InternalTurnModel):
    kind: Literal[TurnKind.SERIAL_KILLER_TARGET] = TurnKind.SERIAL_KILLER_TARGET
    entry: str
    effects: TurnEffects = Field(default_factory=TurnEffects)


class ResolvedVigilanteTarget(_InternalTurnModel):
    kind: Literal[TurnKind.VIGILANTE_TARGET] = TurnKind.VIGILANTE_TARGET
    entry: str
    effects: TurnEffects = Field(default_factory=TurnEffects)


ResolvedTurn: TypeAlias = Annotated[
    ResolvedDayDiscussion
    | ResolvedDayVote
    | ResolvedWolfDiscussion
    | ResolvedWolfVote
    | ResolvedHealerTarget
    | ResolvedInvestigatorTarget
    | ResolvedSerialKillerTarget
    | ResolvedVigilanteTarget,
    Field(discriminator="kind"),
]


__all__ = [
    "ResolvedDayDiscussion",
    "ResolvedDayVote",
    "ResolvedHealerTarget",
    "ResolvedInvestigatorTarget",
    "ResolvedSerialKillerTarget",
    "ResolvedTurn",
    "ResolvedVigilanteTarget",
    "ResolvedWolfDiscussion",
    "ResolvedWolfVote",
    "TurnEffects",
    "TurnKind",
]

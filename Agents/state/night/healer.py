"""Healer night-graph state (the exemplar single-actor night state; the others mirror it)."""

from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary
from Agents.schemas.memory import StrategyAdoption


class HealerNightGraph(TypedDict, total=False):
    """Single-actor night-graph state (shared shape across healer / investigator / serial_killer
    / vigilante): the role's context + strategy in, its chosen target + strategy delta out.
    `healer_target` and `updated_strategy` are the act node's outputs."""

    day_channel: list[DayChannel]
    day_summaries: list[DaySummary]
    surviving_players: list[str]
    strategy_points: str
    strategy_adoptions: Annotated[list[StrategyAdoption], add]
    player_id: str
    player_role: str
    human_player: bool

    current_day: int
    current_round: int
    previous_strategy: str
    updated_strategy: str | None
    healer_target: str | None

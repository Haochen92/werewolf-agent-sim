"""Investigator night-graph state (single-actor; see state/night/healer.py for the shape)."""

from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary, InvestigatorResult
from Agents.schemas.memory import StrategyAdoption


class InvestigatorNightGraph(TypedDict, total=False):
    """Single-actor night state + the private investigator_results it reasons from; the act node
    outputs investigator_target (+ updated_strategy)."""

    day_channel: list[DayChannel]
    day_summaries: list[DaySummary]

    investigator_results: list[InvestigatorResult]
    strategy_points: str
    strategy_adoptions: Annotated[list[StrategyAdoption], add]

    surviving_players: list[str]
    player_id: str
    player_role: str

    current_day: int
    current_round: int
    previous_strategy: str
    updated_strategy: str | None
    human_player: bool
    investigator_target: str | None

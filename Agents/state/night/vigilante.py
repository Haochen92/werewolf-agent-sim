"""Vigilante night-graph state (single-actor; see state/night/healer.py for the shape)."""

from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary
from Agents.schemas.memory import StrategyAdoption


class VigilanteNightGraph(TypedDict, total=False):
    """Single-actor night state (see state/night/healer.py) + private vigilante_bullets/results;
    the act node outputs vigilante_target ("hold_fire" or a player) + updated_strategy."""

    day_channel: list[DayChannel]
    day_summaries: list[DaySummary]
    surviving_players: list[str]
    strategy_points: str
    strategy_adoptions: Annotated[list[StrategyAdoption], add]
    player_id: str
    player_role: str
    human_player: bool
    vigilante_bullets: int
    vigilante_results: list[str]

    current_day: int
    current_round: int
    previous_strategy: str
    updated_strategy: str | None
    vigilante_target: str | None

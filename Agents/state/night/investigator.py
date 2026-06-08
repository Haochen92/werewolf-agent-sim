from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary, InvestigatorResult
from Agents.schemas.memory import StrategyAdoption


class InvestigatorNightGraph(TypedDict, total=False):
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

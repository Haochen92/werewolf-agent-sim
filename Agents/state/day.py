from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DayVote,
    InvestigatorResult,
)
from Agents.schemas.memory import StrategyAdoption
from Agents.state.reducers import merge_strategies


class DayGraphState(TypedDict, total=False):
    current_day: int
    day_channel: Annotated[list[DayChannel], add]
    day_summaries: Annotated[list[DaySummary], add]
    day_votes: Annotated[list[DayVote], add]
    strategy_adoptions: Annotated[list[StrategyAdoption], add]

    agent_strategies: Annotated[dict[str, str], merge_strategies]
    roles: dict[str, str]
    human_player: str

    investigator_player: str | None
    investigator_results: list[InvestigatorResult]
    vigilante_results: list[str]

    surviving_villagers: list[str]
    surviving_wolves: list[str]
    no_lynch_streak: int

    current_round: int


class VillagerDayState(TypedDict):
    current_day: int
    current_round: int
    previous_strategy: str
    strategy_points: str

    human_player: bool
    day_channel: list[DayChannel]
    day_summaries: list[DaySummary]
    surviving_players: list[str]
    player_id: str
    player_role: str


class HealerDayState(TypedDict):
    current_day: int
    current_round: int
    previous_strategy: str
    strategy_points: str

    human_player: bool
    day_channel: list[DayChannel]
    day_summaries: list[DaySummary]
    surviving_players: list[str]
    player_id: str
    player_role: str


class InvestigatorDayState(TypedDict):
    current_day: int
    current_round: int

    human_player: bool
    day_channel: list[DayChannel]
    day_summaries: list[DaySummary]
    surviving_players: list[str]
    investigator_results: list[InvestigatorResult]
    player_id: str
    player_role: str
    previous_strategy: str
    strategy_points: str


class WolfDayState(TypedDict):
    current_day: int
    current_round: int

    human_player: bool
    day_channel: list[DayChannel]
    day_summaries: list[DaySummary]
    surviving_wolves: list[str]
    surviving_villagers: list[str]
    player_id: str
    player_role: str
    previous_strategy: str
    strategy_points: str



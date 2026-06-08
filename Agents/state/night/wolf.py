from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary, WolfChannel
from Agents.schemas.memory import StrategyAdoption
from Agents.state.reducers import merge_strategies


class WolfNightGraph(TypedDict, total=False):
    day_channel: list[DayChannel]
    day_summaries: list[DaySummary]
    wolf_channel: Annotated[list[WolfChannel], add]
    surviving_wolves: list[str]
    surviving_villagers: list[str]
    agent_strategies: Annotated[dict[str, str], merge_strategies]
    # Per-wolf memory adoptions from the (parallel) night discussion accumulate
    # here, then wolf_night_phase bubbles them to the orchestrator — matching the
    # single-target night roles.
    strategy_adoptions: Annotated[list[StrategyAdoption], add]

    human_player: str

    current_day: int
    wolves_kill_target: str | None

    current_round: int


class WolfNightState(TypedDict):
    day_channel: list[DayChannel]
    day_summaries: list[DaySummary]
    wolf_channel: list[WolfChannel]

    surviving_villagers: list[str]
    surviving_wolves: list[str]
    previous_strategy: str
    strategy_points: str

    player_id: str
    player_role: str
    human_player: bool

    current_day: int
    current_round: int

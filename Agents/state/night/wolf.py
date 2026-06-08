"""Wolf-night state: the subgraph channel (WolfNightGraph) + the per-wolf Send payload
(WolfNightState). The wolf night is the only multi-agent night, so it has both, like the day."""

from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary, WolfChannel
from Agents.schemas.memory import StrategyAdoption
from Agents.state.reducers import merge_strategies


class WolfNightGraph(TypedDict, total=False):
    """Working state of the wolf-night loop: wolf_channel accumulates across rounds,
    current_round tracks the 2-round discuss->vote, wolves_kill_target is set once resolved."""

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
    """Payload delivered to each surviving wolf's discuss Send (one per wolf, in parallel)."""

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

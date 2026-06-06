from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DayVote,
    InvestigatorResult,
    WolfChannel,
)
from Agents.schemas.memory import StrategyAdoption

def merge_strategies(existing: dict[str, str], new: dict[str, str]) -> dict[str, str]:
    return dict(existing, **new)


class OrchestratorGraph(TypedDict, total=False):
    day_channel: Annotated[list[DayChannel], add]
    day_summaries: Annotated[list[DaySummary], add]
    wolf_channel: Annotated[list[WolfChannel], add]
    strategy_adoptions: Annotated[list[StrategyAdoption], add]

    agent_strategies: dict[str, str]
    roles: dict[str, str]
    human_player: str
    healer_player: str | None
    investigator_player: str | None
    serial_killer_player: str | None
    vigilante_player: str | None

    wolves_kill_target: str | None
    healer_target: str | None
    investigator_target: str | None
    serial_killer_target: str | None
    vigilante_target: str | None
    vigilante_bullets: int

    investigator_results: Annotated[list[InvestigatorResult], add]
    # Private notes the vigilante learns from its own shots (e.g. discovering an immune
    # target is the serial killer). Siloed to the vigilante, like investigator_results.
    vigilante_results: Annotated[list[str], add]
    day_votes: list[DayVote]
    voted_player: str | None
    no_lynch_streak: int

    # The solo serial killer has no allies, so there is no "surviving SK" list to be
    # aware of (unlike surviving_wolves). It lives in surviving_villagers (the non-wolf
    # bucket) for discussion/targeting; serial_killer_player tracks whether it is alive.
    surviving_wolves: list[str]
    surviving_villagers: list[str]

    current_day: int
    current_round: int
    winner: str | None


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


class HealerNightGraph(TypedDict, total=False):
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


class SerialKillerNightGraph(TypedDict, total=False):
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
    serial_killer_target: str | None


class VigilanteNightGraph(TypedDict, total=False):
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

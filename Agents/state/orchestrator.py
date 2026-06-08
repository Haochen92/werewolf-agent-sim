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

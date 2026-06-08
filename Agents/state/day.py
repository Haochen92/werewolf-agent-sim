"""Day-subgraph state + the per-role payloads delivered to actor nodes.

DayGraphState is the day subgraph's working state. The ``*DayState`` classes are the payload
contracts for the per-speaker/per-voter ``Send``s — each carries only the private fields its
role is allowed to see (wolf rosters / investigator results / vigilante results), which is the
information-leak invariant enforced in build_speaker_send / fan_out_day (Agents.nodes.day.flow):
a private field never rides along to a role that shouldn't see it.
"""

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
    """Working state of the day subgraph. Channels accumulate (`add`); agent_strategies merges
    per-key (merge_strategies) so concurrent vote-node updates don't clobber each other."""
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
    """Discuss/vote payload for a role with NO private info (villager / serial killer /
    vigilante-on-discuss-without-results). The common fields shared by every role payload."""

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
    """Healer payload — same shape as VillagerDayState (the healer keeps no public private
    field during the day; its protection info is night-side only)."""
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
    """Investigator payload: common fields + the private investigator_results it may reason from."""

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
    """Wolf payload: common fields but with the wolf-visible rosters (surviving_wolves +
    surviving_villagers) instead of the role-blind surviving_players list."""

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



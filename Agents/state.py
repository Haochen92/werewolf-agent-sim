from operator import add
from typing import Annotated, TypedDict

from pydantic import BaseModel


class DayChannel(BaseModel):
    day: int
    round: int
    player: str
    message: str


class WolfChannel(BaseModel):
    day: int
    round: int
    wolf: str
    message: str
    vote: str


class InvestigatorResult(BaseModel):
    day: int
    player_investigated: str
    role_revealed: str


class DayVote(BaseModel):
    voter: str
    votee: str


class OrchestratorGraph(TypedDict, total=False):
    day_channel: Annotated[list[DayChannel], add]
    wolf_channel: Annotated[list[WolfChannel], add]

    roles: dict[str, str]
    human_player: str
    healer_player: str | None
    investigator_player: str | None

    wolves_kill_target: str | None
    healer_target: str | None
    investigator_target: str | None

    investigator_results: Annotated[list[InvestigatorResult], add]
    day_votes: list[DayVote]
    voted_player: str | None

    surviving_wolves: list[str]
    surviving_villagers: list[str]

    current_day: int
    current_round: int
    winner: str | None


class DayGraphState(TypedDict, total=False):
    current_day: int
    day_channel: Annotated[list[DayChannel], add]
    day_votes: Annotated[list[DayVote], add]

    roles: dict[str, str]
    human_player: str

    investigator_player: str | None
    investigator_results: list[InvestigatorResult]

    surviving_villagers: list[str]
    surviving_wolves: list[str]

    current_round: int


class VillagerDayState(TypedDict):
    current_day: int
    current_round: int

    human_player: bool
    day_channel: list[DayChannel]
    surviving_players: list[str]
    player_id: str
    player_role: str


class InvestigatorDayState(TypedDict):
    current_day: int
    current_round: int

    human_player: bool
    day_channel: list[DayChannel]
    surviving_players: list[str]
    investigator_results: list[InvestigatorResult]
    player_id: str
    player_role: str


class WolfDayState(TypedDict):
    current_day: int
    current_round: int

    human_player: bool
    day_channel: list[DayChannel]
    surviving_wolves: list[str]
    surviving_villagers: list[str]
    player_id: str
    player_role: str


class WolfNightGraph(TypedDict, total=False):
    day_channel: list[DayChannel]
    wolf_channel: Annotated[list[WolfChannel], add]
    surviving_wolves: list[str]
    surviving_villagers: list[str]

    human_player: str

    current_day: int
    wolves_kill_target: str | None

    current_round: int


class WolfNightState(TypedDict):
    day_channel: list[DayChannel]
    wolf_channel: list[WolfChannel]

    surviving_villagers: list[str]
    surviving_wolves: list[str]

    player_id: str
    player_role: str
    human_player: bool

    current_day: int
    current_round: int


class InvestigatorNightGraph(TypedDict, total=False):
    day_channel: list[DayChannel]

    investigator_results: list[InvestigatorResult]

    surviving_players: list[str]
    player_id: str
    player_role: str

    human_player: bool
    investigator_target: str | None


class HealerNightGraph(TypedDict, total=False):
    day_channel: list[DayChannel]
    surviving_players: list[str]
    player_id: str
    player_role: str
    human_player: bool

    healer_target: str | None


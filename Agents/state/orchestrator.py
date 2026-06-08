"""Orchestrator (parent-graph) state: the authoritative state for a whole game.

This is the single source of truth the day/night subgraphs read from and write deltas back
into. Two things to know: (1) list channels marked ``Annotated[..., add]`` ACCUMULATE across
phases (the subgraphs return only their newly-appended slice — see graphs/parent.py); (2) the
special-role aliveness model is two-layer — the survivor *buckets* (surviving_wolves /
surviving_villagers) hold who's alive for discussion/targeting, while the role *markers*
(healer_player / investigator_player / serial_killer_player / vigilante_player) are the source
of truth for whether each special role is still in play (set to None when that player dies).
"""

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
    """Full-game state. total=False: phases populate fields incrementally."""

    # Accumulating transcripts/records (the `add` reducer appends across phases).
    day_channel: Annotated[list[DayChannel], add]
    day_summaries: Annotated[list[DaySummary], add]
    wolf_channel: Annotated[list[WolfChannel], add]
    strategy_adoptions: Annotated[list[StrategyAdoption], add]

    # Cast & identity.
    agent_strategies: dict[str, str]  # player_id -> private strategy note
    roles: dict[str, str]             # player_id -> true role
    human_player: str
    # Role markers: source of truth for special-role aliveness (None once that player dies).
    healer_player: str | None
    investigator_player: str | None
    serial_killer_player: str | None
    vigilante_player: str | None

    # Tonight's chosen targets (reset each night; None = no action / not present).
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
    # Day outcome.
    day_votes: list[DayVote]
    voted_player: str | None
    no_lynch_streak: int  # consecutive no-elimination days (forces abstain off past a cap)

    # The solo serial killer has no allies, so there is no "surviving SK" list to be
    # aware of (unlike surviving_wolves). It lives in surviving_villagers (the non-wolf
    # bucket) for discussion/targeting; serial_killer_player tracks whether it is alive.
    surviving_wolves: list[str]
    surviving_villagers: list[str]

    current_day: int
    current_round: int
    winner: str | None  # set once a faction wins; None while the game is live

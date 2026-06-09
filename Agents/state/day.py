"""Day-subgraph state + the per-role payloads delivered to actor nodes.

DayGraphState is the day subgraph's working state. The ``*DayState`` classes are the payload
contracts for the per-speaker/per-voter ``Send``s — each carries only the private fields its
role is allowed to see (wolf rosters / investigator results / vigilante results), which is the
information-leak invariant enforced in build_speaker_send / fan_out_day (Agents.nodes.day.flow):
a private field never rides along to a role that shouldn't see it.

Field docstrings are IDE-only (Pylance hover) — TypedDict state is never serialized to a model,
so nothing here leaks. See the project schema-doc convention.
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
    """1-based current game day."""
    day_channel: Annotated[list[DayChannel], add]
    """Public day-discussion transcript; accumulates across speaker turns."""
    day_summaries: Annotated[list[DaySummary], add]
    """Prior-day summaries carried in as context."""
    day_votes: Annotated[list[DayVote], add]
    """Votes cast this day; accumulates as vote nodes report."""
    strategy_adoptions: Annotated[list[StrategyAdoption], add]
    """Memory-adoption records emitted by actor nodes (tracing/eval)."""

    agent_strategies: Annotated[dict[str, str], merge_strategies]
    """player_id -> private strategy note; merged per-key so concurrent votes don't clobber."""
    roles: dict[str, str]
    """player_id -> true role (ground truth; never shown to other agents)."""
    human_player: str
    """player_id of the human seat, or "" when fully agent-played."""

    investigator_player: str | None
    """Investigator's player_id while alive; None once dead/absent."""
    investigator_results: list[InvestigatorResult]
    """Private investigation outcomes (siloed to the investigator's payload)."""
    vigilante_results: list[str]
    """Private notes the vigilante learned from its shots (siloed to the vigilante)."""

    surviving_villagers: list[str]
    """Living non-wolves (includes the solo serial killer)."""
    surviving_wolves: list[str]
    """Living wolves — the wolf-visible ally roster."""
    no_lynch_streak: int
    """Consecutive no-elimination days; forces abstain off past a cap."""

    current_round: int
    """Discussion round within the current day."""


class VillagerDayState(TypedDict):
    """Discuss/vote payload for a role with NO private info (villager / serial killer /
    vigilante-on-discuss-without-results). The common fields shared by every role payload."""

    current_day: int
    """1-based current game day."""
    current_round: int
    """Discussion round within the day."""
    previous_strategy: str
    """This agent's own prior strategy note, fed back in."""
    strategy_points: str
    """Retrieved/reranked memory strategy points formatted for the prompt."""

    human_player: bool
    """True if this seat is the human player (suppresses the LLM call)."""
    day_channel: list[DayChannel]
    """Public day-discussion transcript visible to everyone."""
    day_summaries: list[DaySummary]
    """Prior-day summaries for context."""
    surviving_players: list[str]
    """Role-blind roster of all living players (no faction split — this role can't see one)."""
    player_id: str
    """This actor's player_id."""
    player_role: str
    """This actor's role label (drives the prompt's role block)."""


class HealerDayState(TypedDict):
    """Healer payload — same shape as VillagerDayState (the healer keeps no public private
    field during the day; its protection info is night-side only)."""

    current_day: int
    """1-based current game day."""
    current_round: int
    """Discussion round within the day."""
    previous_strategy: str
    """The healer's own prior strategy note."""
    strategy_points: str
    """Retrieved memory strategy points formatted for the prompt."""

    human_player: bool
    """True if this seat is the human player."""
    day_channel: list[DayChannel]
    """Public day-discussion transcript."""
    day_summaries: list[DaySummary]
    """Prior-day summaries for context."""
    surviving_players: list[str]
    """Role-blind roster of all living players."""
    player_id: str
    """This actor's player_id."""
    player_role: str
    """This actor's role label."""


class InvestigatorDayState(TypedDict):
    """Investigator payload: common fields + the private investigator_results it may reason from."""

    current_day: int
    """1-based current game day."""
    current_round: int
    """Discussion round within the day."""

    human_player: bool
    """True if this seat is the human player."""
    day_channel: list[DayChannel]
    """Public day-discussion transcript."""
    day_summaries: list[DaySummary]
    """Prior-day summaries for context."""
    surviving_players: list[str]
    """Role-blind roster of all living players."""
    investigator_results: list[InvestigatorResult]
    """Private: the roles this investigator has learned (the leak-boundary payload field)."""
    player_id: str
    """This actor's player_id."""
    player_role: str
    """This actor's role label."""
    previous_strategy: str
    """The investigator's own prior strategy note."""
    strategy_points: str
    """Retrieved memory strategy points formatted for the prompt."""


class WolfDayState(TypedDict):
    """Wolf payload: common fields but with the wolf-visible rosters (surviving_wolves +
    surviving_villagers) instead of the role-blind surviving_players list."""

    current_day: int
    """1-based current game day."""
    current_round: int
    """Discussion round within the day."""

    human_player: bool
    """True if this seat is the human player."""
    day_channel: list[DayChannel]
    """Public day-discussion transcript."""
    day_summaries: list[DaySummary]
    """Prior-day summaries for context."""
    surviving_wolves: list[str]
    """Private: living wolf allies (the leak-boundary payload field — wolves only)."""
    surviving_villagers: list[str]
    """Living non-wolves the wolves may target."""
    player_id: str
    """This actor's player_id."""
    player_role: str
    """This actor's role label."""
    previous_strategy: str
    """This wolf's own prior strategy note."""
    strategy_points: str
    """Retrieved memory strategy points formatted for the prompt."""

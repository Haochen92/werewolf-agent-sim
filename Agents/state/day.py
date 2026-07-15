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
    DeathRecord,
    InvestigatorResult,
    WolfChannel,
)
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
    dead_roster: list[DeathRecord]
    """Ordered PUBLIC dead roster (dead player -> revealed role + when), seeded from orchestrator
    state so every day payload can render who is dead. Read-only in the day graph (deaths are
    written by night/day resolution, which are parent-graph nodes — never here)."""
    cast_role_counts: dict[str, int]
    """Public fixed-cast census (role -> how many players were cast with it; counts only, no
    identities), seeded from orchestrator state so every day payload can render the alive-roles line
    (this census minus the revealed dead). Read-only in the day graph like dead_roster."""
    wolf_channel: list[WolfChannel]
    """Wolf night coordination + GM whiff notes, seeded from orchestrator state so the wolf day
    payload can carry it into discuss/vote turns (read-only in the day graph — never written here)."""
    day_votes: Annotated[list[DayVote], add]
    """Votes cast this day; accumulates as vote nodes report."""

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
    vigilante_bullets: int
    """Remaining vigilante shots; seeded from orchestrator state so the vigilante's day payload can
    fill the deterministic `bullets_left` situation dim (not shown in any prompt)."""

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
    dead_roster: list[DeathRecord]
    """Public dead roster (dead player -> revealed role + when); shown to every role."""
    cast_role_counts: dict[str, int]
    """Public fixed-cast census (role -> count; counts only, no identities) feeding the alive-roles line."""
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
    dead_roster: list[DeathRecord]
    """Public dead roster (dead player -> revealed role + when); shown to every role."""
    cast_role_counts: dict[str, int]
    """Public fixed-cast census (role -> count; counts only, no identities) feeding the alive-roles line."""
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
    dead_roster: list[DeathRecord]
    """Public dead roster (dead player -> revealed role + when); shown to every role."""
    cast_role_counts: dict[str, int]
    """Public fixed-cast census (role -> count; counts only, no identities) feeding the alive-roles line."""
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
    dead_roster: list[DeathRecord]
    """Public dead roster (dead player -> revealed role + when); shown to every role."""
    cast_role_counts: dict[str, int]
    """Public fixed-cast census (role -> count; counts only, no identities) feeding the alive-roles line."""
    surviving_wolves: list[str]
    """Private: living wolf allies (the leak-boundary payload field — wolves only)."""
    surviving_villagers: list[str]
    """Living non-wolves the wolves may target."""
    wolf_channel: list[WolfChannel]
    """Private: the wolves' night coordination + GM whiff notes, carried into day discuss/vote so a
    wolf can act on what was decided/learned at night (wolves only — a wolf's own information)."""
    player_id: str
    """This actor's player_id."""
    player_role: str
    """This actor's role label."""
    previous_strategy: str
    """This wolf's own prior strategy note."""
    strategy_points: str
    """Retrieved memory strategy points formatted for the prompt."""

"""Investigator night-graph state (single-actor; see state/night/healer.py for the shape)."""

from typing import TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary, DeathRecord, InvestigatorResult


class InvestigatorNightGraph(TypedDict, total=False):
    """Single-actor night state + the private investigator_results it reasons from; the act node
    outputs investigator_target (+ updated_strategy)."""

    day_channel: list[DayChannel]
    """Public day-discussion transcript carried into the night for context."""
    day_summaries: list[DaySummary]
    """Prior-day summaries for context."""
    dead_roster: list[DeathRecord]
    """Public dead roster (dead player -> revealed role + when), carried into the night to render the
    who-died block. Must be declared: LangGraph drops undeclared keys off a subgraph's state schema."""
    cast_role_counts: dict[str, int]
    """Public fixed-cast census (role -> count; counts only, no identities) feeding the alive-roles
    line (cast minus revealed dead). Must be declared for the same reason as dead_roster."""

    investigator_results: list[InvestigatorResult]
    """Private: roles learned on prior nights, reasoned from when picking tonight's probe."""
    strategy_points: str
    """Retrieved memory strategy points formatted for the prompt."""

    surviving_players: list[str]
    """Candidate targets: every living player except the investigator."""
    player_id: str
    """The investigator's player_id."""
    player_role: str
    """Role label ("investigator")."""

    current_day: int
    """1-based current game day."""
    current_round: int
    """Round counter (0 for single-actor nights)."""
    previous_strategy: str
    """The investigator's own prior strategy note, fed back in."""
    updated_strategy: str | None
    """Act-node output: the investigator's revised strategy note (None if unchanged)."""
    human_player: bool
    """True if the investigator seat is the human player."""
    investigator_target: str | None
    """Act-node output: the player the investigator probes tonight (None if no probe)."""

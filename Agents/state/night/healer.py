"""Healer night-graph state (the exemplar single-actor night state; the others mirror it)."""

from typing import TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary, DeathRecord


class HealerNightGraph(TypedDict, total=False):
    """Single-actor night-graph state (shared shape across healer / investigator / serial_killer
    / vigilante): the role's context + strategy in, its chosen target + strategy delta out.
    `healer_target` and `updated_strategy` are the act node's outputs."""

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
    surviving_players: list[str]
    """Candidate targets: every living player except the healer."""
    strategy_points: str
    """Retrieved memory strategy points formatted for the prompt."""
    player_id: str
    """The healer's player_id."""
    player_role: str
    """Role label ("healer")."""
    human_player: bool
    """True if the healer seat is the human player."""

    current_day: int
    """1-based current game day."""
    current_round: int
    """Round counter (0 for single-actor nights)."""
    previous_strategy: str
    """The healer's own prior strategy note, fed back in."""
    updated_strategy: str | None
    """Act-node output: the healer's revised strategy note (None if unchanged)."""
    healer_target: str | None
    """Act-node output: the player the healer protects tonight (None if no protection)."""

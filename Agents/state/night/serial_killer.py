"""Serial-killer night-graph state (single-actor; see state/night/healer.py for the shape)."""

from typing import TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary, DeathRecord


class SerialKillerNightGraph(TypedDict, total=False):
    """Single-actor night state (see state/night/healer.py); the act node outputs
    serial_killer_target (+ updated_strategy)."""

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
    """Candidate targets: every living player except the serial killer."""
    strategy_points: str
    """Retrieved memory strategy points formatted for the prompt."""
    player_id: str
    """The serial killer's player_id."""
    player_role: str
    """Role label ("serial_killer")."""
    human_player: bool
    """True if the serial-killer seat is the human player."""

    current_day: int
    """1-based current game day."""
    current_round: int
    """Round counter (0 for single-actor nights)."""
    previous_strategy: str
    """The serial killer's own prior strategy note, fed back in."""
    updated_strategy: str | None
    """Act-node output: the serial killer's revised strategy note (None if unchanged)."""
    serial_killer_target: str | None
    """Act-node output: the player the serial killer strikes tonight (None if no strike)."""

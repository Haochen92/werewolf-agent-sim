"""Vigilante night-graph state (single-actor; see state/night/healer.py for the shape)."""

from typing import TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary, DeathRecord


class VigilanteNightGraph(TypedDict, total=False):
    """Single-actor night state (see state/night/healer.py) + private vigilante_bullets/results;
    the act node outputs vigilante_target ("hold_fire" or a player) + updated_strategy."""

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
    """Candidate targets: every living player except the vigilante."""
    strategy_points: str
    """Retrieved memory strategy points formatted for the prompt."""
    player_id: str
    """The vigilante's player_id."""
    player_role: str
    """Role label ("vigilante")."""
    human_player: bool
    """True if the vigilante seat is the human player."""
    vigilante_bullets: int
    """Remaining shots (starts at 2); 0 forces hold_fire."""
    vigilante_results: list[str]
    """Private notes the vigilante learned from past shots (e.g. an immune target = the SK)."""

    current_day: int
    """1-based current game day."""
    current_round: int
    """Round counter (0 for single-actor nights)."""
    previous_strategy: str
    """The vigilante's own prior strategy note, fed back in."""
    updated_strategy: str | None
    """Act-node output: the vigilante's revised strategy note (None if unchanged)."""
    vigilante_target: str | None
    """Act-node output: "hold_fire", a player to shoot, or None (normalized downstream)."""

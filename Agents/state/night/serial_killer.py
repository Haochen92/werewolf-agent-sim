"""Serial-killer night-graph state (single-actor; see state/night/healer.py for the shape)."""

from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary
from Agents.schemas.memory import StrategyAdoption


class SerialKillerNightGraph(TypedDict, total=False):
    """Single-actor night state (see state/night/healer.py); the act node outputs
    serial_killer_target (+ updated_strategy)."""

    day_channel: list[DayChannel]
    """Public day-discussion transcript carried into the night for context."""
    day_summaries: list[DaySummary]
    """Prior-day summaries for context."""
    surviving_players: list[str]
    """Candidate targets: every living player except the serial killer."""
    strategy_points: str
    """Retrieved memory strategy points formatted for the prompt."""
    strategy_adoptions: Annotated[list[StrategyAdoption], add]
    """Memory-adoption records emitted by the act node (tracing/eval)."""
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

"""Wolf-night state: the subgraph channel (WolfNightGraph) + the per-wolf Send payload
(WolfNightState). The wolf night is the only multi-agent night, so it has both, like the day."""

from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary, WolfChannel
from Agents.schemas.memory import StrategyAdoption
from Agents.state.reducers import merge_strategies


class WolfNightGraph(TypedDict, total=False):
    """Working state of the wolf-night loop: wolf_channel accumulates across rounds,
    current_round tracks the 2-round discuss->vote, wolves_kill_target is set once resolved."""

    day_channel: list[DayChannel]
    """Public day-discussion transcript carried into the night for context."""
    day_summaries: list[DaySummary]
    """Prior-day summaries for context."""
    wolf_channel: Annotated[list[WolfChannel], add]
    """Private wolf discussion + kill votes; accumulates across the night's rounds."""
    surviving_wolves: list[str]
    """Living wolves participating in the night."""
    surviving_villagers: list[str]
    """Living non-wolves — the wolves' candidate kill targets."""
    agent_strategies: Annotated[dict[str, str], merge_strategies]
    """player_id -> private strategy note; merged per-key across parallel wolf turns."""
    # Per-wolf memory adoptions from the (parallel) night discussion accumulate
    # here, then wolf_night_phase bubbles them to the orchestrator — matching the
    # single-target night roles.
    strategy_adoptions: Annotated[list[StrategyAdoption], add]
    """Memory-adoption records from the parallel wolf turns (tracing/eval)."""

    human_player: str
    """player_id of the human seat, or "" when fully agent-played."""

    current_day: int
    """1-based current game day."""
    wolves_kill_target: str | None
    """Resolved kill target once the binding vote completes (None mid-night)."""

    current_round: int
    """Wolf-night round (1=open discussion, 2=binding vote)."""


class WolfNightState(TypedDict):
    """Payload delivered to each surviving wolf's discuss Send (one per wolf, in parallel)."""

    day_channel: list[DayChannel]
    """Public day-discussion transcript for context."""
    day_summaries: list[DaySummary]
    """Prior-day summaries for context."""
    wolf_channel: list[WolfChannel]
    """Private wolf discussion + votes so far this night."""

    surviving_villagers: list[str]
    """Living non-wolves — the candidate kill targets."""
    surviving_wolves: list[str]
    """Living wolf allies."""
    previous_strategy: str
    """This wolf's own prior strategy note, fed back in."""
    strategy_points: str
    """Retrieved memory strategy points formatted for the prompt."""

    player_id: str
    """This wolf's player_id."""
    player_role: str
    """Role label ("werewolf")."""
    human_player: bool
    """True if this wolf seat is the human player."""

    current_day: int
    """1-based current game day."""
    current_round: int
    """Wolf-night round (1=discussion, 2=vote)."""

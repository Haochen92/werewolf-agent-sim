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
    DeathRecord,
    InvestigatorResult,
    WolfChannel,
)
from Agents.state.reducers import merge_strategies


class OrchestratorGraph(TypedDict, total=False):
    """Full-game state. total=False: phases populate fields incrementally."""

    # Accumulating transcripts/records (the `add` reducer appends across phases).
    day_channel: Annotated[list[DayChannel], add]
    """Public day-discussion transcript; accumulates across all days."""
    day_summaries: Annotated[list[DaySummary], add]
    """One condensed summary per completed day, carried into later days."""
    wolf_channel: Annotated[list[WolfChannel], add]
    """Wolf-night discussion + kill-vote transcript; accumulates across nights."""
    dead_roster: Annotated[list[DeathRecord], add]
    """Ordered PUBLIC dead roster; a DeathRecord is appended at each death (night_resolution /
    day_resolution) so agents read who died + their revealed role from state, not GM prose."""

    # Cast & identity.
    agent_strategies: Annotated[dict[str, str], merge_strategies]
    """player_id -> that agent's private strategy note. Per-key merge (merge_strategies), so a
    single-actor night phase folding back {player: note} updates only that seat instead of
    overwriting the whole map — matching how the day/wolf subgraph channels already reduce it."""
    roles: dict[str, str]
    """player_id -> true role (ground truth; never shown to other agents)."""
    human_player: str
    """player_id of the human seat, or "" when fully agent-played."""
    # Role markers: source of truth for special-role aliveness (None once that player dies).
    healer_player: str | None
    """Healer's player_id while alive; None once dead/absent."""
    investigator_player: str | None
    """Investigator's player_id while alive; None once dead/absent."""
    serial_killer_player: str | None
    """Serial killer's player_id while alive; None once dead/absent."""
    vigilante_player: str | None
    """Vigilante's player_id while alive; None once dead/absent."""

    # Tonight's chosen targets (reset each night; None = no action / not present).
    wolves_kill_target: str | None
    """Tonight's wolf kill target; None if no kill resolved."""
    healer_target: str | None
    """Player the healer protects tonight; None if no protection."""
    investigator_target: str | None
    """Player the investigator probes tonight; None if no probe."""
    serial_killer_target: str | None
    """Player the serial killer strikes tonight; None if no strike."""
    vigilante_target: str | None
    """Player the vigilante shoots tonight; None if holding fire."""
    vigilante_bullets: int
    """Remaining vigilante shots (starts at 2)."""

    investigator_results: Annotated[list[InvestigatorResult], add]
    """Private investigation outcomes, siloed to the investigator."""
    # Private notes the vigilante learns from its own shots (e.g. discovering an immune
    # target is the serial killer). Siloed to the vigilante, like investigator_results.
    vigilante_results: Annotated[list[str], add]
    """Private notes the vigilante learns from its shots (e.g. an immune target = the
    serial killer). Siloed to the vigilante, like investigator_results."""
    # Day outcome.
    day_votes: list[DayVote]
    """This day's recorded votes (public, permanent)."""
    voted_player: str | None
    """Player eliminated by today's vote; None on a no-lynch day."""
    no_lynch_streak: int
    """Consecutive no-elimination days; forces abstain off past a cap."""

    # The solo serial killer has no allies, so there is no "surviving SK" list to be
    # aware of (unlike surviving_wolves). It lives in surviving_villagers (the non-wolf
    # bucket) for discussion/targeting; serial_killer_player tracks whether it is alive.
    surviving_wolves: list[str]
    """Living wolves — the wolf-visible ally roster."""
    surviving_villagers: list[str]
    """Living non-wolves (includes the solo serial killer) for discussion/targeting."""

    current_day: int
    """1-based current game day."""
    current_round: int
    """Discussion round within the current day."""
    winner: str | None
    """Winning faction once decided; None while the game is live."""


def fresh_game_state() -> dict:
    """A new game's initial state: just the accumulator channels, as fresh empty lists.

    Everything decided (roles, roster, day counter) is INITIALIZE_GAME's output delta;
    what needs seeding is only the append-over-time lists, so accumulation has a starting
    point. A factory, not a shared constant: each game must get its own list objects —
    a module-level template's containers would be silently shared across concurrent games.
    """
    return {
        "day_channel": [],
        "day_summaries": [],
        "wolf_channel": [],
        "investigator_results": [],
        "day_votes": [],
    }

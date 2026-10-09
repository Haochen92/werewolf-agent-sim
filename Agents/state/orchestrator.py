"""Orchestrator (parent-graph) state: the authoritative state for a whole game.

This is the single source of truth the day/night subgraphs read from and write deltas back
into. List channels marked ``Annotated[..., add]`` ACCUMULATE across phases (the subgraphs return
only their newly-appended slice — see graphs/parent.py). Who is alive is the two survivor buckets
(surviving_wolves / surviving_villagers), split by side; who holds a role is read off ``roles``
and the buckets (Agents.rules.seats.alive_holder), so a death is one removal from a bucket.
"""

from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DayVote,
    DeathRecord,
    NightActionRecord,
    WolfChannel,
)
from Agents.schemas.night import NightChoice, NightReport
from Agents.state.reducers import merge_night_choices, merge_strategies


class OrchestratorGraph(TypedDict, total=False):
    """Full-game state. total=False: phases populate fields incrementally."""

    # Accumulating transcripts/records (the `add` reducer appends across phases).
    day_channel: Annotated[list[DayChannel], add]
    """Public day-discussion transcript; accumulates across all days."""
    day_summaries: Annotated[list[DaySummary], add]
    """One condensed summary per completed day, carried into later days."""
    wolf_channel: Annotated[list[WolfChannel], add]
    """The pack's night chat and the carrier's kill; accumulates across nights."""
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
    lineup: list[str]
    """The ten roles this game dealt, in the rules block's order (public: the line-up is common
    knowledge). The prompts, the output schemas and the win logic read it."""
    human_players: list[str]
    """player_ids of the human seats (multi-human rooms hold several); empty when
    fully agent-played."""

    # Tonight, as it is decided.
    night_choices: Annotated[list[NightChoice], merge_night_choices]
    """Every choice made tonight, one per acting player (the pack's kill under its carrier),
    appended by the parallel night branches and cleared by one_more_day (None)."""
    night_report: NightReport | None
    """The night's public outcome, as night_resolution committed it: what the morning said. The
    wire reads it instead of recomputing the night."""

    # What is left of the limited abilities, spent by night_resolution, never by a turn.
    uses_left: dict[str, int]
    """role -> uses remaining, for the roles with a limit (vigilante bullets, sigils, conceals,
    the fortune teller's self-bets, the speculator's one pick)."""
    speculator_pick: str | None
    """The side the speculator picked (town, wolves, lone_killer, self); None until it picks."""
    fortune_points: int
    """The fortune teller's running score."""
    last_body: str | None
    """The body the necromancer acted through last night; it may not use the same one twice
    in a row."""

    night_actions: Annotated[list[NightActionRecord], add]
    """Every night actor's private record (the pack's kill as actor "wolves"), written by
    night_resolution. Payload builders hand each player only its own
    (Agents.rules.night_record.own_night_actions)."""
    # Day outcome.
    day_votes: list[DayVote]
    """This day's recorded votes (public, permanent)."""
    voted_player: str | None
    """Player eliminated by today's vote; None on a no-lynch day."""
    no_lynch_streak: int
    """Consecutive no-elimination days; forces abstain off past a cap."""

    surviving_wolves: list[str]
    """Living wolves — the wolf-visible ally roster."""
    surviving_villagers: list[str]
    """Living non-wolves: town, the lone killer and the neutral, for discussion/targeting."""

    current_day: int
    """1-based current game day."""
    current_round: int
    """Discussion round within the current day."""
    winner: str | None
    """Winning side once decided (villagers, wolves, or the lone killer's role); None while the
    game is live, and at the end of a drawn game."""
    neutral_result: str | None
    """How the neutral fared, beside the winner: "won" or "lost" for a speculator, the fortune
    teller's points as "won (N points)" / "lost (N points)"; None before the end."""


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
        "night_actions": [],
        "night_choices": [],
        "day_votes": [],
    }

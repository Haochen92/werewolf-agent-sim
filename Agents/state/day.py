"""Day-subgraph state + the payload delivered to the actor nodes.

DayGraphState is the day subgraph's working state. DayActorState is the payload contract of the
per-speaker/per-voter ``Send``s: it carries only the private fields the role is allowed to see,
which is the information-leak invariant enforced in build_speaker_send / fan_out_day
(Agents.nodes.day.flow): a private field never rides along to a role that shouldn't see it.

Field docstrings are IDE-only (Pylance hover) — TypedDict state is never serialized to a model,
so nothing here leaks. See the project schema-doc convention.
"""

from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import (
    DayChannel,
    DayRound,
    DaySummary,
    DayVote,
    DeathRecord,
    FiringReason,
    NightActionRecord,
    RoundCandidate,
    WolfChannel,
)
from Agents.state.reducers import merge_strategies


class DayGraphState(TypedDict, total=False):
    """Working state of the day subgraph: the orchestrator's public channels and rosters in,
    the day's lines, votes and strategy notes out."""

    agent_strategies: Annotated[dict[str, str], merge_strategies]
    """player_id -> private strategy note; merged per-key across parallel actor turns."""
    current_day: int
    """1-based current game day."""
    day_channel: Annotated[list[DayChannel], add]
    """Public day-discussion transcript; this day's lines accumulate."""
    day_summaries: Annotated[list[DaySummary], add]
    """Prior-day summaries, plus today's once written."""
    dead_roster: list[DeathRecord]
    """Public dead roster, read-only in the day graph."""
    wolf_channel: list[WolfChannel]
    """The pack's night chat, carried into the day for the wolves' payloads only."""
    roles: dict[str, str]
    """player_id -> true role: read by the payload builders to gate private fields, never put on
    a payload."""
    lineup: list[str]
    """The dealt roles, public."""
    human_players: list[str]
    """player_ids of the human seats."""
    night_actions: list[NightActionRecord]
    """Every night actor's private record; each payload builder attaches only the speaker's own
    (own_night_actions). Read-only in the day graph."""
    uses_left: dict[str, int]
    """role -> uses remaining, for the day payloads' private lines (bullets, sigils)."""
    speculator_pick: str | None
    """The speculator's pick, for its own payload."""
    fortune_points: int
    """The fortune teller's score, for its own payload."""
    day_votes: Annotated[list[DayVote], add]
    """This day's votes; the parallel vote nodes each append one."""

    surviving_villagers: list[str]
    """Living non-wolves: town, the lone killer and the neutral."""
    surviving_wolves: list[str]
    """Living wolves — the wolf-visible ally roster."""
    no_lynch_streak: int
    """Consecutive no-elimination days; forces abstain off past a cap."""

    day_round: DayRound
    """The round of the day now running (Phase 2): "opening" or "closing". Written by the round's
    entry node (start_opening / start_closing); fan_out_round and collect_round read it. The
    scheduler's sweep turns carry "proactive" on their entries but run no round."""
    round_players: list[str]
    """Who is in the round now running, in the order their lines are played: every survivor in seat
    order for the opening, the accused for the closing. Written by the round's entry node with
    day_round; fan_out_round sends to exactly these players and collect_round plays their lines in
    this order. The translator reads it off the entry node's chunk for the round_opened event."""
    round_candidates: Annotated[list[RoundCandidate], add]
    """The parallel round turns' lines, held until collect_round orders and numbers them into
    day_channel. The day graph's state is rebuilt every day and day_phase returns only four keys,
    so these never reach the parent graph."""


class DayActorState(TypedDict, total=False):
    """The Send payload of one player's discussion, round or vote turn. The common fields are on
    every payload; the private ones (marked) only on the role they belong to — the builders in
    flow.py are the leak boundary (tests/leak_test.py guards it), since run_agent builds the
    prompt input straight from the payload."""

    current_day: int
    """1-based current game day."""
    day_round: DayRound
    """Which round of the day the turn belongs to (opening / discussion / proactive / closing)."""
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
    lineup: list[str]
    """The dealt roles, public: the rules block and the output schema come from it."""
    surviving_players: list[str]
    """Role-blind roster of all living players."""
    player_id: str
    """This actor's player_id."""
    player_role: str
    """This actor's role label (drives the prompt's role block)."""
    voting_available: bool
    """Whether today ends in a vote (day 1 does not)."""
    allow_abstain: bool
    """Vote turns: whether "abstain" is offered today."""
    firing_reason: FiringReason
    """Discussion turns: why the scheduler fired this player."""
    night_actions: list[NightActionRecord]
    """PRIVATE: the speaker's own night record (and the pack's kills for a wolf)."""
    surviving_wolves: list[str]
    """PRIVATE, wolves only: the pack."""
    surviving_villagers: list[str]
    """Wolves only: the non-wolves."""
    wolf_channel: list[WolfChannel]
    """PRIVATE, wolves only: the pack's night chat."""
    initial_wolf_count: int
    """Wolves only: how many wolves were dealt (a count, for the memory cell's fill)."""
    uses_left: int
    """PRIVATE, a role with a limit: what is left of it."""
    vigilante_bullets: int
    """PRIVATE, the vigilante: its bullets (the memory cell's fill reads this name)."""
    speculator_pick: str
    """PRIVATE, the speculator: its pick so far."""
    fortune_points: int
    """PRIVATE, the fortune teller: its score."""

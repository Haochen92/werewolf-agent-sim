"""Night state: the one payload every solo night turn and every wolf's skill turn runs on, and
the pack's subgraph channel. The solo roles share one shape because their turns differ only in
the words and the field, which come from the card and the registry."""

from operator import add
from typing import Annotated, TypedDict

from Agents.schemas.game_events import DayChannel, DaySummary, DeathRecord, NightActionRecord, WolfChannel
from Agents.state.reducers import merge_strategies


class NightTurnState(TypedDict, total=False):
    """The payload of one player's night turn (a solo role, the carrier, a wolf's skill)."""

    day_channel: list[DayChannel]
    """Public day-discussion transcript carried into the night for context."""
    day_summaries: list[DaySummary]
    """Prior-day summaries for context."""
    dead_roster: list[DeathRecord]
    """Public dead roster, carried into the night to render the who-died block."""
    cast_role_counts: dict[str, int]
    """Public fixed-cast census (role -> count; counts only, no identities) feeding the alive-roles
    line (cast minus revealed dead)."""
    lineup: list[str]
    """The dealt roles, public, for the rules block and the output schema."""
    night_actions: list[NightActionRecord]
    """Private: this actor's own night record (for a wolf, its own and the pack's), filtered by
    own_night_actions in the payload builder."""
    surviving_players: list[str]
    """Candidate targets: every living player except the actor."""
    surviving_wolves: list[str]
    """The pack, on a wolf's payload only."""
    surviving_villagers: list[str]
    """The non-wolves, on a wolf's payload only: the pack's candidate targets."""
    wolf_channel: list[WolfChannel]
    """The pack's chat, on a wolf's payload only."""
    carrier: str
    """Tonight's carrier, on a wolf's payload only."""
    wolves_target: str
    """The pack's kill tonight, on a wolf's skill payload only; "" until the carrier named it."""
    pack_turn: bool
    """A wolf's payload: True on the chat and the carrier's turn (the pack's lot applies), False
    on its own skill turn."""
    uses_left: int
    """What is left of a limited ability; absent for a role without a limit."""
    bodies: list[str]
    """The bodies a necromancer may act through tonight."""
    speculator_pick: str
    """The speculator's pick so far ("not yet", or the side)."""
    fortune_points: int
    """The fortune teller's score so far."""
    strategy_points: str
    """Retrieved memory strategy points formatted for the prompt."""
    player_id: str
    """The actor's player_id."""
    player_role: str
    """The actor's role."""
    human_player: bool
    """True if this seat is the human player."""
    current_day: int
    """1-based current game day."""
    current_round: int
    """The pack's chat round for a wolf's chat turn; 0 for the others."""
    previous_strategy: str
    """The actor's own prior strategy note, fed back in."""


class PackNightGraph(TypedDict, total=False):
    """Working state of the pack's night: the chat accumulates across rounds, the carrier names
    the kill, then each wolf's skill turn adds its choice."""

    day_channel: list[DayChannel]
    day_summaries: list[DaySummary]
    dead_roster: list[DeathRecord]
    cast_role_counts: dict[str, int]
    lineup: list[str]
    night_actions: list[NightActionRecord]
    """The pack's records: every wolf's own and the pack's kills."""
    wolf_channel: Annotated[list[WolfChannel], add]
    """The pack's chat and the carrier's kill; accumulates across the night's rounds."""
    surviving_wolves: list[str]
    surviving_villagers: list[str]
    roles: dict[str, str]
    """The true roles: a wolf's skill turn needs its own role, and the carrier's choice its."""
    uses_left: dict[str, int]
    agent_strategies: Annotated[dict[str, str], merge_strategies]
    human_players: list[str]
    current_day: int
    current_round: int
    """Chat round: 1..WOLF_CHAT_ROUNDS; the carrier's and skill turns run after."""
    carrier: str
    """Tonight's carrier, decided at entry by rotation."""
    wolves_target: str | None
    """The pack's kill once the carrier named it."""
    night_choices: Annotated[list, add]
    """The pack's choices tonight: the carrier's kill and each wolf's skill."""

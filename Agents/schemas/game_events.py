"""Game-event / transcript value objects shared across graph state and prompts.

These are internal records — formatted into prompts as text and stored in graph state — NOT
structured-output schemas, with ONE exception: AddressedTarget is embedded in DayDiscussOutput
and is therefore part of the model-visible structured-output contract. Do not add a class
docstring or edit AddressedTarget's fields/descriptions without a prompt-freeze review (its
field descriptions are sent to the model; the others here are not).

Convention: the internal classes carry attribute docstrings (IDE hover only — never reach a
model). AddressedTarget keeps Field(description=...) because those strings ARE sent to the model.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


# Model-visible: embedded in DayDiscussOutput -> its field descriptions are part of the frozen
# structured-output contract. Frozen; do not edit without a prompt-freeze review.
class AddressedTarget(BaseModel):
    target: str = Field(
        description="Player ID or name."
    )

    addressed_form: Literal["question", "response", "mention"] = Field(
        description="question=directly asks the target something that expects their reply; response=replies to the target; mention=talks about the target in the third person."
    )

    stance: Literal["accusation", "defense", "agreement", "neutral"] = Field(
        description="accusation=suspects/blames the target of being evil or lying; defense=supports/protects; agreement=agrees; neutral=no clear stance (passing commentary, e.g. noting someone has been quiet, is neutral, not accusation)."
    )


# The rounds of a day (Phase 2): the opening (every living player at once), the scheduler's
# reactive discussion chains, the scheduler's sweep over the players who have not spoken (one at
# a time, the echo gate holding repeats) and the closing defence of the most accused.
DayRound = Literal["opening", "discussion", "proactive", "closing"]


class FiringReason(BaseModel):
    """Why the scheduler fired a turn — observability only; rides the Send and is stamped onto
    the resulting DayChannel, but hidden from agents."""

    tier: Literal["reactive", "proactive"]
    """reactive = the turn answers an open obligation; proactive = the scheduler's sweep gave the
    floor to a player who had not spoken."""
    owes: list[str] = Field(default_factory=list)
    """Creditors the speaker owes a response to (reactive only). Empty for proactive."""
    sweep: int = 0
    """For a proactive turn, which sweep of the day it belongs to: 1 = the first pass over the
    players silent since the day began, 2 = the second pass over those silent since the first
    sweep began. 0 on a reactive turn. The scheduler is stateless and reads the day's sweep
    structure back from these marks (Agents/turn/scheduler.py)."""


class DiscussionPassReason(str, Enum):
    """Why a discussion turn produced a hidden pass marker instead of speech."""

    VOLUNTARY = "voluntary"
    NOVELTY_GATED = "novelty_gated"
    """A proactive turn held back because an earlier line of the day made the same point (the echo
    gate, Agents/turn/echo_gate.py). The held text is kept in gated_candidate and shown to its
    author only; its accusation tags stay on the marker for records but count for nothing (the
    closing counts spoken lines only, ruling 2026-10-07)."""
    GENERATION_FAILED = "generation_failed"
    ROUND_ECHO = "round_echo"
    """Records only. A line of the parallel proactive round held back because another line of the
    same round made the same point (Phase 2 step 4b, 2026-10-07; the round went sequential the
    same day, step 4c, and the engine no longer produces this reason)."""
    OPENING_FILTERED = "opening_filtered"
    """An opening line held back because it was not one of the kinds an opening may hold (a role
    claim, the speaker's own night action or result, a challenge to an earlier claim), or it
    repeated an earlier opening that was not a claim (Phase 2's opening filter). Held text in
    gated_candidate, shown to its author only."""


class DayChannel(BaseModel):
    """One entry in the public day-discussion transcript (a spoken message or a pass marker)."""

    day: int
    """1-based game day this entry belongs to."""
    seq: int
    """Order within the day (monotonic; pass markers included)."""
    player: str
    """Speaker player_id, or "game_master" for narration."""
    message: str
    """The spoken text (empty for a pass marker)."""
    addressed_targets: list[AddressedTarget] = Field(default_factory=list)
    """Structured who-this-addresses tags parsed from the speech (empty for narration/passes)."""
    day_round: DayRound = "discussion"
    """Which round of the day the entry belongs to: "opening" (every living player at once, before
    the discussion), "discussion" (the scheduler's reactive turns), "proactive" (a sweep turn: the
    scheduler gave the floor to a player who had not spoken) or "closing" (the accused's last
    word). Phase 2; entries from before it carry the default."""
    passed: bool = False
    """True = hidden pass marker (voluntary, novelty-gated, or generation failure)."""
    pass_reason: DiscussionPassReason | None = None
    """Observer classification for a pass. None on speech and legacy pass records."""
    firing_reason: FiringReason | None = None
    """Scheduler trace for why this turn fired; observability only, hidden from agents. None for
    non-scheduler (e.g. legacy/human) messages."""
    gated: bool = False
    """On a pass marker: True = the novelty gate SILENCED a would-be proactive turn; False = the
    agent VOLUNTARILY declined (pass_turn). Lets a gate-selectivity audit tell the two apart (they
    were previously one indistinguishable passed=True marker). Observability only; never on a real
    utterance."""
    gated_candidate: str = ""
    """The held-back text of a gated or filtered pass marker; shown to its author only. ⚠️ LEAK
    BOUNDARY: this text was removed from the discussion ON PURPOSE — it must NEVER be formatted into
    any other player's prompt. Persisted-but-hidden like firing_reason: the day-channel formatters
    drop passed markers, so it is guarded there; tests/leak_test.check_held_lines_reach_only_their_author
    is the standing guard. Observability only (a future gate audit reads it), never model-visible."""
    opening_kind: str = ""
    """The opening filter's label for an opening line (claim / night_action / challenge / repeat /
    other); observer only, "" on every other entry."""


class RoundCandidate(BaseModel):
    """One round turn's line, held until the round is collected (Phase 2).

    The opening and closing rounds send every player's turn at once, and parallel turns cannot
    write day_channel themselves: each would count the same seq from the transcript it was
    given. So a round turn returns its entry here, and collect_round orders the round's
    candidates, numbers them, and writes them into day_channel in one step."""

    day: int
    """The day the round belongs to."""
    day_round: DayRound
    """"opening" or "closing" (a discussion or sweep turn writes day_channel directly). Each runs
    once a day, so (day, day_round) names a round."""
    entry: DayChannel
    """The turn's line or pass marker, with the seq it counted itself (overwritten on collection)."""


class DaySummary(BaseModel):
    """One block carried into later days: either the summariser's account of a day's discussion,
    or a game-master announcement (a night's outcome, a vote result) filed alongside it."""

    day: int
    """The day summarized."""
    summary: str
    """Serialized day-summary text."""
    source: Literal["discussion", "game_master"] = "discussion"
    """Who wrote it: "game_master" = an exact engine announcement; "discussion" = the summariser's
    account of what players said. Prompts render the two apart, so a claim repeated in a summary
    never reads with the authority of an announcement (audit 2026-10-03, finding 5)."""

    @model_validator(mode="after")
    def _label_old_announcements(self) -> "DaySummary":
        # Saved before `source` existed (a checkpoint of a game in progress at the change): the
        # engine's announcements open with fixed phrases, and no discussion summary does.
        if "source" not in self.model_fields_set and self.summary.lstrip().startswith(
                ("Night of day", "Here's the vote result")):
            self.source = "game_master"
        return self
    structured: dict = Field(default_factory=dict)
    """The summariser's structured output as a dict: v4 has accusations / role_claims; older games also
    alliances / village_dynamics. Agents read previous days from it: format_day_summaries builds the
    claim ledger and the accusations from these fields (day summary v4, 2026-10-04), and shows the
    text `summary` only for a day stored without them. Also read by the post-game tagger/credit
    (role_claims for role-reveal; accusations for advocacy-correctness crosses) and the replay's
    X-ray card. {} on the raw-channel fallback."""


class WolfChannel(BaseModel):
    """One wolf-night entry: talk, a binding vote, or a hidden technical-pass marker."""

    day: int
    """Game day of this night."""
    round: int
    """Wolf-night round (talk rounds, then the binding-vote round)."""
    wolf: str
    """Speaking wolf's player_id."""
    message: str
    """The wolf's discussion text; empty for a vote or technical pass."""
    vote: str
    """The wolf's current kill-target vote (a surviving villager)."""
    passed: bool = False
    """True only when wolf discussion exhausted every model attempt; hidden from pack prompts."""
    pass_reason: DiscussionPassReason | None = None
    """Observer classification for a pass; currently generation_failed is the only wolf value."""


class InvestigatorResult(BaseModel):
    """One night's investigation outcome, private to the investigator."""

    day: int
    """Night the investigation happened."""
    player_investigated: str
    """Target player_id."""
    role_revealed: str
    """The target's true role, learned privately."""


class DayVote(BaseModel):
    """A recorded day-phase vote (public and permanent)."""

    voter: str
    """Voting player_id."""
    votee: str
    """Voted-for player_id, or "abstain"."""


class DeathRecord(BaseModel):
    """One player's death as it was PUBLICLY announced — the authoritative, ordered dead roster.

    Appended (in death order) at each death site: night_resolution for a night kill, and
    day_resolution for a lynch. Every current death path announces the dead player's role (see
    the game_master messages), so `role` is public information — this whole record is rendered
    into every role's day payload, no leak gating. Deriving the roster from this field is the
    deterministic alternative to re-parsing the game_master's prose out of the day transcript."""

    player: str
    """The dead player's player_id."""
    role: str
    """The role the announcement publicly revealed (empty only if a future path stops revealing it)."""
    day: int
    """1-based game day of the death (for a night kill: the night belonging to that day)."""
    phase: Literal["night", "day"]
    """"night" = killed overnight (wolves / serial killer / vigilante); "day" = lynched by vote."""


class NightActionRecord(BaseModel):
    """One night action as its actor experienced it: written by night resolution, private to the
    actor. The healer, vigilante and serial killer each see only their own; every wolf sees the
    pack's kill. Gives the actor an exact record of what it did, which its own prose note cannot
    be relied on to keep (audit 2026-10-03, finding 1)."""

    day: int
    """The night the action was taken (the night belonging to that day)."""
    actor: str
    """The acting player_id, or "wolves" for the pack's kill."""
    action: Literal["protect", "shoot", "hold_fire", "kill"]
    """What the actor did: the healer protects, the vigilante shoots or holds fire, the serial
    killer and the wolves kill."""
    target: str | None
    """Who the action was on; None for hold_fire."""
    outcome: str
    """What the actor is allowed to know of the result, in plain words."""

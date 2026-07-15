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

from typing import Literal

from pydantic import BaseModel, Field


# Model-visible: embedded in DayDiscussOutput -> its field descriptions are part of the frozen
# structured-output contract. Frozen; do not edit without a prompt-freeze review.
class AddressedTarget(BaseModel):
    target: str = Field(
        description="Player ID or name."
    )

    addressed_form: Literal["question", "response", "mention"] = Field(
        description="question=asks target; response=replies to target; mention=refers to target."
    )

    stance: Literal["accusation", "defense", "agreement", "neutral"] = Field(
        description="accusation=suspects/blames; defense=supports/protects; agreement=agrees; neutral=no clear stance."
    )


class FiringReason(BaseModel):
    """Why the scheduler fired a turn — observability only; rides the Send and is stamped onto
    the resulting DayChannel, but hidden from agents."""

    tier: Literal["reactive", "proactive"]
    """reactive=turn forced by an open obligation; proactive=scheduler-initiated on a quiet cycle."""
    owes: list[str] = Field(default_factory=list)
    """Creditors the speaker owes a response to (reactive only). Empty for proactive."""


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
    passed: bool = False
    """True = proactive pass marker (hidden, not counted)."""
    firing_reason: FiringReason | None = None
    """Scheduler trace for why this turn fired; observability only, hidden from agents. None for
    non-scheduler (e.g. legacy/human) messages."""
    gated: bool = False
    """On a pass marker: True = the novelty gate SILENCED a would-be proactive turn; False = the
    agent VOLUNTARILY declined (pass_turn). Lets a gate-selectivity audit tell the two apart (they
    were previously one indistinguishable passed=True marker). Observability only; never on a real
    utterance."""
    gated_candidate: str = ""
    """The discarded candidate text the novelty gate silenced (empty unless gated=True). ⚠️ LEAK
    BOUNDARY: this text was removed from the discussion ON PURPOSE — it must NEVER be formatted into
    any agent-facing prompt. Persisted-but-hidden like firing_reason: the day-channel formatters drop
    passed markers, so it is guarded there; tests/leak_test.check_gated_candidate_isolation is the
    standing guard. Observability only (a future gate audit reads it), never model-visible."""


class DaySummary(BaseModel):
    """A condensed summary of one day's discussion, carried into later days."""

    day: int
    """The day summarized."""
    summary: str
    """Serialized day-summary text."""
    structured: dict = Field(default_factory=dict)
    """The full DaySummaryOutput (role_claims / accusations / alliances / village_dynamics) as a dict —
    the structured signal the post-game tagger/credit reuse (role_claims for role-reveal; accusations for
    advocacy-correctness crosses). The prose `summary` above is the agent-facing flatten of the same.
    {} on the raw-channel fallback. NOT model-visible: agents only ever see `summary`
    (format_day_summaries reads `.day`/`.summary` only) — so persisting this changes no gameplay input."""


class WolfChannel(BaseModel):
    """One wolf's message + kill vote in a wolf-night discussion round."""

    day: int
    """Game day of this night."""
    round: int
    """Wolf-night round (1=open discussion, 2=binding vote)."""
    wolf: str
    """Speaking wolf's player_id."""
    message: str
    """The wolf's discussion text."""
    vote: str
    """The wolf's current kill-target vote (a surviving villager)."""


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

    Appended (in death order) at each death site: night_kill_resolution for a night kill, and
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

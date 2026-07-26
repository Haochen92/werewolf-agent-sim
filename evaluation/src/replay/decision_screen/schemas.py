"""Replay-INPUT output-schema variants for the vote replay — reason-first,
memory-linked, situation-match, and forced-structured applicability. Each swaps
the field ORDER (and, for the applicability probes, adds a per-memory verdict
step) versus the production DayVoteOutput; field semantics are unchanged. They
are handed to ``_replay_vote(..., schema_override=)`` / ``_replay_vote_structured``
as replay inputs and are NEVER written to production.

``MemoryVerdict`` (the per-memory verdict row) is re-exported here so callers that
build the structured schema import the whole replay-input vocabulary from one place."""

from __future__ import annotations

from pydantic import BaseModel, Field

from Agents.schemas.output import MemoryVerdict

__all__ = [
    "MemoryVerdict",
    "DayVoteOutputReasonFirst",
    "DayVoteOutputMemoryLinked",
    "DayVoteOutputSituationMatch",
    "DayVoteOutputStructuredApplicability",
]


class DayVoteOutputReasonFirst(BaseModel):
    """Experimental reason-before-act variant of DayVoteOutput: updated_strategy
    (the reasoning, where injected memory gets integrated) is emitted BEFORE
    vote_target, so the model thinks before committing the vote instead of
    snap-voting then rationalizing. Field semantics match production; only the
    ORDER differs. Used as a replay input, never written to production."""

    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    updated_strategy: str
    vote_target: str


class DayVoteOutputMemoryLinked(BaseModel):
    """Reason-before-act with an explicit memory-LINKING step: the reasoning field
    (kept named updated_strategy so the live extractor + the adherence judge read
    it unchanged) is emitted FIRST and its description forces the agent to connect
    the retrieved memories to THIS vote before committing. Aim is to maximize
    memory consideration, not the score. Replay input only."""

    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    updated_strategy: str = Field(
        description=(
            "Before you vote, reason about THIS vote: go through the retrieved "
            "memories one by one, decide which actually apply to the current "
            "players and situation, and state explicitly how each changes (or does "
            "not change) who you should vote for. Make the link between the "
            "memories and your final choice explicit; if none apply, say so and why."
        )
    )
    vote_target: str


class DayVoteOutputSituationMatch(BaseModel):
    """Situation-applicability variant: updated_strategy (emitted BEFORE vote_target)
    is instructed to compare EACH retrieved observation's situation to the current
    board across the decision-relevant dimensions, judge how much it applies, and
    apply each lesson only to that degree. Capability probe — tests whether the game
    model can reason about applicability when asked explicitly. adopted_strategy_keys
    is intentionally DROPPED: we inject no strategy points, so it would be a vestigial
    no-op that competes with the observation-applicability prose we're testing.
    Replay input only."""

    updated_strategy: str = Field(
        description=(
            "Before you vote, go through the retrieved observations ONE BY ONE and compare each "
            "one's situation to your CURRENT board: the evidence available and how credible it is, "
            "how many players and which roles remain and who this vote would remove, and the "
            "consensus and who is targeting whom. For each, state whether it FULLY applies, PARTLY "
            "applies, or does NOT apply to your board, and why. Then decide, applying each lesson "
            "only to the degree its situation matches yours."
        )
    )
    vote_target: str


class DayVoteOutputStructuredApplicability(BaseModel):
    """Forced-structured applicability variant: ONE verdict row per retrieved
    observation (the model cannot skip the assessment), emitted BEFORE the vote.
    Capability probe — does the game model produce sensible per-memory verdicts? Captured
    by a direct chain call (a new field is dropped by run_agent's mapping). No
    adopted_strategy_keys (vestigial here). Replay input only."""

    memory_applicability: list[MemoryVerdict] = Field(
        description="Produce ONE verdict per retrieved observation, in the SAME ORDER they are listed. "
        "For each, compare its situation to your current board and judge whether it fully applies, "
        "partly applies, or does not apply."
    )
    updated_strategy: str = Field(
        description="Your vote reasoning, applying each observation only to the degree your "
        "memory_applicability verdict says it applies."
    )
    vote_target: str

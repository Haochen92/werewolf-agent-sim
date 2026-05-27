from __future__ import annotations

from pydantic import BaseModel, Field


class WolfNightDiscussOutput(BaseModel):
    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    message: str
    vote_target: str
    updated_strategy: str


class DayDiscussOutput(BaseModel):
    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    message: str | None
    updated_strategy: str


class DayVoteOutput(BaseModel):
    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    vote_target: str
    updated_strategy: str


class Accusation(BaseModel):
    accusers: list[str] = Field(
        description="ALL player IDs who participated in this accusation (e.g. ['player_1', 'player_3'])",
    )
    target: str = Field(description="Player ID of the accused")
    reasoning: str = Field(description="Core reasoning behind the accusation (1-2 sentences)")
    evidence_type: str = Field(
        description="Type of evidence: voting_record, communication_style, behavioral_pattern, or concrete_claim",
    )
    defense: str = Field(
        default="",
        description="How the target responded (1-2 sentences). Empty if no defense given.",
    )


class RoleClaim(BaseModel):
    player: str = Field(description="Player ID who made the claim")
    claimed_role: str = Field(description="The role claimed")
    evidence: str = Field(
        description=(
            "Evidence supporting the claim: describe public corroboration "
            "if any, otherwise 'unverified'"
        ),
    )


class Alliance(BaseModel):
    players: list[str] = Field(description="Player IDs in this alliance or bloc")
    basis: str = Field(description="What the alignment is based on (1 sentence)")


class VillageDynamics(BaseModel):
    information_landscape: str = Field(
        description=(
            "Information-rich or information-starved? What type of evidence "
            "is driving suspicion: voting records, communication style, "
            "behavioral patterns, or concrete claims? 1-2 sentences."
        ),
    )
    consensus: str = Field(
        description=(
            "Village alignment: unified push against one target, fragmented "
            "suspicion across many, or split into opposing camps? Is this "
            "driven by evidence or social momentum? 1-2 sentences."
        ),
    )
    drivers: str = Field(
        description=(
            "Who is driving the discussion vs. staying quiet or deflecting? "
            "Name specific player IDs. 1-2 sentences."
        ),
    )


class DaySummaryOutput(BaseModel):
    accusations: list[Accusation] = Field(
        default_factory=list,
        description="All distinct accusations from the discussion. List every accusation separately.",
    )
    role_claims: list[RoleClaim] = Field(
        default_factory=list,
        description="Any role claims made during discussion. Empty list if none.",
    )
    alliances: list[Alliance] = Field(
        default_factory=list,
        description="Any alliances or voting blocs that formed. Empty list if none.",
    )
    village_dynamics: VillageDynamics


class HealerOutput(BaseModel):
    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    healer_target: str
    updated_strategy: str


class InvestigatorOutput(BaseModel):
    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    investigator_target: str
    updated_strategy: str


class SituationSummary(BaseModel):
    situations: list[str] = Field(
        description=(
            "1-3 discrete situations the player currently faces, each as a 2-3 "
            "sentence description of a game dynamic suitable for semantic search."
        ),
        min_length=1,
        max_length=3,
    )

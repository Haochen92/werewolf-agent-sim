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


class SituationEntry(BaseModel):
    situation: str = Field(
        description=(
            "The core game dynamic — what happened and who is involved. "
            "Lead with the concrete event or conflict, not abstract framing. "
            "Do not embed dimensional context (information landscape, game "
            "phase, etc.) here; use the dedicated fields below. 2-3 sentences."
        )
    )
    information_landscape: str = Field(
        description=(
            "What evidence exists and what type: information-rich (confirmed "
            "roles, voting records, caught lies) or information-starved (no "
            "leads, speculative reads). 1 sentence."
        )
    )
    game_phase: str = Field(
        description=(
            "Early (no eliminations, no data), mid (some data, roles "
            "emerging), or endgame (few players, high stakes per vote). "
            "Note what changed most recently. 1 sentence."
        )
    )
    consensus_texture: str = Field(
        description=(
            "How aligned is the village? Unified, fragile, split, or no "
            "consensus? Driven by evidence or social momentum? Do not "
            "describe who is under pressure here."
        ),
    )
    agent_exposure: str = Field(
        description=(
            "The agent's position: driving the push, aligned with consensus, "
            "under indirect scrutiny, or primary target? Based on specific "
            "evidence, behavioral reads, or association?"
        ),
    )

    @property
    def composed(self) -> str:
        from Agents.schemas.memory import _compose_situation

        return _compose_situation(
            self.situation,
            self.information_landscape,
            self.game_phase,
            self.consensus_texture,
            self.agent_exposure,
        )


class SituationSummary(BaseModel):
    situations: list[SituationEntry] = Field(
        description=(
            "1-2 distinct situations the player currently faces, each with "
            "structured dimensional fields for semantic search."
        ),
        min_length=1,
        max_length=2,
    )

    @property
    def composed_situations(self) -> list[str]:
        return [s.composed for s in self.situations]

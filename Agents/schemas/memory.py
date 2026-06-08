"""Memory-pipeline data models: extraction/rerank OUTPUTS plus store/retrieval records.

⚠️ MODEL-VISIBLE / FROZEN — Observation, StrategyPoint, GameStrategyOutput (post-game extraction
output) and CandidateRelevance, RerankResult (reranker output). Their class docstrings and
Field(description=...) are serialized into the schema sent to the model, so they condition outputs
and the Phase B gold labels; do NOT add docstrings or edit descriptions without a prompt-freeze
review. The rest — StoredStrategy / StoredObservation / StoredStrategyPoint / StrategyAdoption /
RetrievedObservation / RetrievedStrategyPoint — are internal store / retrieval / state records
(never sent to a model) and are documented freely.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from Agents.constants import ActionPhase, VALID_ACTION_PHASES_BY_ROLE, roles


def _compose_situation(
    situation: str,
    information_landscape: str,
    game_phase: str,
    consensus_texture: str | None,
    agent_exposure: str | None,
) -> str:
    """Fold the dimensional fields into one searchable situation string (used for embedding /
    retrieval matching); optional dimensions are appended only when present."""
    parts = [situation]
    parts.append(f"Information landscape: {information_landscape}")
    parts.append(f"Game phase: {game_phase}")
    if consensus_texture:
        parts.append(f"Consensus texture: {consensus_texture}")
    if agent_exposure:
        parts.append(f"Agent exposure: {agent_exposure}")
    return " ".join(parts)


class Observation(BaseModel):
    perspective: str = Field(
        description=(
            "The role this observation is most useful for: wolf, villager, "
            "healer, or investigator"
        )
    )
    action_phase: ActionPhase = Field(
        description=(
            "The game phase this observation applies to: day_discussion, "
            "day_vote, or night_action"
        )
    )
    situation: str = Field(
        description=(
            "The core game dynamic — what triggered the situation. Do not "
            "embed dimensional context (information landscape, game phase, "
            "etc.) in this field; use the dedicated dimensional fields "
            "instead. 1-2 sentences."
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
    consensus_texture: str | None = Field(
        default=None,
        description=(
            "How aligned is the village? Unified, fragile, split, or no "
            "consensus? Driven by evidence or social momentum? Do not "
            "describe who is under pressure here. Only include if relevant."
        ),
    )
    agent_exposure: str | None = Field(
        default=None,
        description=(
            "The agent's position: driving the push, aligned with consensus, "
            "under indirect scrutiny, or primary target? Based on specific "
            "evidence, behavioral reads, or association? Only include if "
            "relevant to the situation."
        ),
    )
    approach: str = Field(
        description=(
            "What the agent(s) did in that situation. May use actual roles. "
            "1-2 sentences."
        )
    )
    outcome: str = Field(
        description=(
            "What resulted — how others responded and the downstream "
            "consequences. May reveal actual roles. 1-2 sentences."
        )
    )

    @property
    def composed_situation(self) -> str:
        return _compose_situation(
            self.situation,
            self.information_landscape,
            self.game_phase,
            self.consensus_texture,
            self.agent_exposure,
        )

    @field_validator("perspective")
    def validate_perspective(cls, value: str) -> str:
        if value not in roles:
            raise ValueError(
                f"{value} is not a valid role. Perspective must be one of {roles}"
            )
        return value

    @model_validator(mode="after")
    def validate_action_phase_for_role(self) -> Observation:
        valid = VALID_ACTION_PHASES_BY_ROLE.get(self.perspective, [])
        if self.action_phase not in valid:
            raise ValueError(
                f"action_phase '{self.action_phase}' is not valid for "
                f"perspective '{self.perspective}'. Valid phases: {valid}"
            )
        return self


class StrategyPoint(BaseModel):
    perspective: str = Field(
        description=(
            "The role this strategy point is most useful for: wolf, villager, "
            "healer, or investigator"
        )
    )
    action_phase: ActionPhase = Field(
        description=(
            "The game phase this strategy applies to: day_discussion, "
            "day_vote, or night_action"
        )
    )
    situation: str = Field(
        description=(
            "The core game dynamic this principle applies to. Start with "
            "'When...' or 'If...'. Do not embed dimensional context "
            "(information landscape, game phase, etc.) in this field; use "
            "the dedicated dimensional fields instead. Do not include "
            "recommended actions or conditional strategy — those belong in "
            "the action field. Describe players by publicly known role "
            "status, not hidden roles or player IDs."
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
    consensus_texture: str | None = Field(
        default=None,
        description=(
            "How aligned is the village? Unified, fragile, split, or no "
            "consensus? Driven by evidence or social momentum? Do not "
            "describe who is under pressure here. Only include if relevant."
        ),
    )
    agent_exposure: str | None = Field(
        default=None,
        description=(
            "The agent's position: driving the push, aligned with consensus, "
            "under indirect scrutiny, or primary target? Based on specific "
            "evidence, behavioral reads, or association? Only include if "
            "relevant to the situation."
        ),
    )
    action: str = Field(
        description=(
            "The recommended action to take in the described situation. "
            "Concrete and prescriptive; may refer to the role this point is "
            "assigned to. Include conditional branches here if the situation "
            "implies different responses for different findings."
        )
    )

    @property
    def composed_situation(self) -> str:
        return _compose_situation(
            self.situation,
            self.information_landscape,
            self.game_phase,
            self.consensus_texture,
            self.agent_exposure,
        )

    @field_validator("perspective")
    def validate_perspective(cls, value: str) -> str:
        if value not in roles:
            raise ValueError(
                f"{value} is not a valid role. Perspective must be one of {roles}"
            )
        return value

    @model_validator(mode="after")
    def validate_action_phase_for_role(self) -> StrategyPoint:
        valid = VALID_ACTION_PHASES_BY_ROLE.get(self.perspective, [])
        if self.action_phase not in valid:
            raise ValueError(
                f"action_phase '{self.action_phase}' is not valid for "
                f"perspective '{self.perspective}'. Valid phases: {valid}"
            )
        return self


class GameStrategyOutput(BaseModel):
    observations: list[Observation] = Field(
        description="Key strategic observations extracted from the full game"
    )
    strategy_points: list[StrategyPoint] = Field(
        description=(
            "Tactical strategy principles extracted from the full game, each with "
            "a situational trigger and recommended action"
        )
    )


class StoredStrategy(BaseModel):
    """A stored free-text strategy record (game_id + content + creation time)."""

    game_id: Optional[str] = ""
    content: str
    created_at: datetime


class StoredObservation(BaseModel):
    """A deduped observation as persisted in the store: the composed situation + approach/outcome,
    with observation_count growing as duplicates merge into it."""

    observation_count: int
    last_observed: datetime
    game_id: Optional[str] = ""
    situation: str
    approach: str = ""
    outcome: str = ""


class StoredStrategyPoint(BaseModel):
    """A deduped strategy point as persisted: situation + action, plus usage counters
    (retrieved/used and positive/neutral/negative outcome tallies) for impact analysis."""

    observation_count: int
    last_observed: datetime
    game_id: Optional[str] = ""
    situation: str
    action: str
    retrieved_count: int = 0
    used_count: int = 0
    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0


class StrategyAdoption(BaseModel):
    """Record that an agent adopted a specific stored strategy at a decision point
    (player/role/day/round/phase) — feeds adoption + memory-impact tracking."""

    strategy_key: str
    player_id: str
    role: str
    day: int
    round: int
    action_phase: str


class RetrievedObservation(BaseModel):
    """A store observation returned by retrieval: the stored record + which situation it matched +
    its similarity score (None if not scored)."""

    key: str
    observation: StoredObservation
    matched_situation: str
    score: float | None = None


class RetrievedStrategyPoint(BaseModel):
    """A store strategy point returned by retrieval: the stored record + matched situation +
    score (None if not scored)."""

    key: str
    strategy_point: StoredStrategyPoint
    matched_situation: str
    score: float | None = None


class CandidateRelevance(BaseModel):
    index: int = Field(description="0-based index of the candidate")
    relevance: int = Field(
        ge=1,
        le=5,
        description="Relevance score: 1 = irrelevant, 5 = highly relevant",
    )


class RerankResult(BaseModel):
    rankings: list[CandidateRelevance] = Field(
        description="Relevance scores for each candidate"
    )

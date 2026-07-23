"""Structured-output schemas the game/judge models emit (via with_structured_output).

⚠️ MODEL-VISIBLE / FROZEN. Every class docstring and Field(description=...) here is serialized into
the JSON schema sent to the model, so it is part of the generation contract that conditions outputs
(and the Phase B gold labels). Do NOT add class docstrings or edit/add field descriptions without a
prompt-freeze review — that changes what the model sees. Document with `#` comments (never
serialized) instead; defer descriptive edits to the v5 prompt-unfreeze. The same rule covers
AddressedTarget (game_events.py), which is embedded in DayDiscussOutput.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from Agents.schemas.game_events import AddressedTarget
from Agents.schemas.roles import READ_ROLE_ENUM


# Per-memory applicability verdict. Emitted BEFORE the action field (prospective commitment: the
# vote/message/target follows the reasoning rather than rationalising it). The "one verdict per
# numbered observation" instruction lives in the PROMPT BODY (memory-context block), not here — these
# descriptions stay terse. Model-visible: no class docstring.
class MemoryVerdict(BaseModel):
    memory_index: int = Field(
        description="1-based position of the observation in the numbered list shown.",
    )
    verdict: Literal["fully_applies", "partly_applies", "does_not_apply"] = Field(
        description="How much this observation's situation matches your current board.",
    )
    why: str = Field(description="One-line reason, grounded in your current board.")


# Per-strategy-point adoption verdict. Emitted BEFORE the action (prospective commitment), like
# MemoryVerdict. The "one verdict per numbered strategy point" instruction lives in the PROMPT BODY
# (memory-context block), not here — these descriptions stay terse. Model-visible: no class docstring.
class StrategyVerdict(BaseModel):
    strategy_index: int = Field(
        description="1-based position of the strategy point in the numbered list shown.",
    )
    verdict: Literal["follow", "override", "not_relevant"] = Field(
        description="Your decision on this point for your current board: follow (act on its advice), "
        "override (its situation holds but you have a better move), or not_relevant (its situation does not hold).",
    )
    why: str = Field(description="One-line reason, grounded in your current board.")


# Per-player suspicion commitment (one entry per living player other than yourself). Emitted BEFORE
# the free-text strategy note, so the read is a prospective commitment (like MemoryVerdict /
# StrategyVerdict) rather than a post-hoc rationalisation. The field order verdicts -> reads ->
# strategy -> action is the tested lever, validated by the T1c decision-replay A/B (role-fact
# hallucinations 48%->30%, p=0.003). The read-role enum is sourced from Agents.schemas.roles so it
# can't drift from the cast. Model-visible: no class docstring.
class PlayerRead(BaseModel):
    player: str = Field(description="A living player's ID (never your own).")
    why: str = Field(description="One line of evidence for this read; write 'unchanged' if your read has not moved.")
    suspected_role: READ_ROLE_ENUM = Field(description="Your best guess of this player's role; 'unclear' if you cannot tell.")
    confidence: Literal["low", "high"] = Field(description="How sure you are.")


class WolfNightDiscussOutput(BaseModel):
    strategy_verdicts: list[StrategyVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered strategy point shown, in order; empty list if none shown.",
    )
    memory_applicability: list[MemoryVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered observation shown, in order; empty list if none shown.",
    )
    updated_strategy: str
    message: str
    vote_target: str


class DayDiscussOutput(BaseModel):
    strategy_verdicts: list[StrategyVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered strategy point shown, in order; empty list if none shown.",
    )
    memory_applicability: list[MemoryVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered observation shown, in order; empty list if none shown.",
    )
    reads: list[PlayerRead] = Field(
        description="One read per living player other than yourself.",
    )
    updated_strategy: str
    pass_turn: bool = Field(
        description="True only if you have nothing new to add and decline to speak. False when answering/defending.",
    )
    message: str
    addressed_targets: list[AddressedTarget] = Field(
        description="List of targets addressed in the discussion. Empty list if none.",
    )


class DayVoteOutput(BaseModel):
    strategy_verdicts: list[StrategyVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered strategy point shown, in order; empty list if none shown.",
    )
    memory_applicability: list[MemoryVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered observation shown, in order; empty list if none shown.",
    )
    reads: list[PlayerRead] = Field(
        description="One read per living player other than yourself.",
    )
    updated_strategy: str
    vote_target: str


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
    strategy_verdicts: list[StrategyVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered strategy point shown, in order; empty list if none shown.",
    )
    memory_applicability: list[MemoryVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered observation shown, in order; empty list if none shown.",
    )
    reads: list[PlayerRead] = Field(
        description="One read per living player other than yourself.",
    )
    updated_strategy: str
    healer_target: str


class InvestigatorOutput(BaseModel):
    strategy_verdicts: list[StrategyVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered strategy point shown, in order; empty list if none shown.",
    )
    memory_applicability: list[MemoryVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered observation shown, in order; empty list if none shown.",
    )
    reads: list[PlayerRead] = Field(
        description="One read per living player other than yourself.",
    )
    updated_strategy: str
    investigator_target: str


class SerialKillerOutput(BaseModel):
    strategy_verdicts: list[StrategyVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered strategy point shown, in order; empty list if none shown.",
    )
    memory_applicability: list[MemoryVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered observation shown, in order; empty list if none shown.",
    )
    reads: list[PlayerRead] = Field(
        description="One read per living player other than yourself.",
    )
    updated_strategy: str
    serial_killer_target: str


class VigilanteOutput(BaseModel):
    strategy_verdicts: list[StrategyVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered strategy point shown, in order; empty list if none shown.",
    )
    memory_applicability: list[MemoryVerdict] = Field(
        default_factory=list,
        description="One verdict per numbered observation shown, in order; empty list if none shown.",
    )
    reads: list[PlayerRead] = Field(
        description="One read per living player other than yourself.",
    )
    updated_strategy: str
    vigilante_target: str


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


# Post-hoc extraction of whom a message addresses — run over a HUMAN turn's free text so the
# reactive/proactive scheduler treats human speech like an LLM's self-tagged addressed_targets.
# Reuses AddressedTarget (same form/stance vocabulary the scheduler consumes). Model-visible: no
# class docstring; the list field is required (flash-lite rejects optional/nullable fields).
class AddressingExtraction(BaseModel):
    addressed_targets: list[AddressedTarget] = Field(
        description="Every player this message addresses; empty list if it addresses no one specific.",
    )


class NoveltyJudgment(BaseModel):
    novel: bool = Field(
        description=(
            "True if the message adds a new argument, observation, piece of evidence, "
            "a changed suspicion, or a direct response to a specific player. False if it "
            "merely restates or agrees with points already made (echo/reinforcement)."
        ),
    )
    reason: str = Field(description="One-sentence justification.")

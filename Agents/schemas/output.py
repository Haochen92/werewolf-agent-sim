"""Structured-output schemas the game/judge models emit (via with_structured_output).

⚠️ MODEL-VISIBLE / FROZEN. Every class docstring and Field(description=...) here is serialized into
the JSON schema sent to the model, so it is part of the generation contract that conditions outputs
(and the Phase B gold labels). Do NOT add class docstrings or edit/add field descriptions without a
prompt-freeze review — that changes what the model sees. Document with `#` comments (never
serialized) instead; defer descriptive edits to the v5 prompt-unfreeze. The same rule covers
AddressedTarget (game_events.py), which is embedded in DayDiscussOutput.
"""

from __future__ import annotations

import json
from typing import Literal, get_origin

from pydantic import BaseModel, Field, field_validator, model_validator

from Agents.schemas.game_events import AddressedTarget
from Agents.schemas.roles import roles

# The day summary's vocabulary (v4): the roles a player may claim, and the fixed result words a
# claimed night action is transcribed into, so code can check a claim against the engine's record
# (Agents/rules/claim_ledger.py). Every role of the pool, dealt or not: the summariser transcribes
# claims and a player may claim anything.
NIGHT_RESULT_WORDS = ("not_a_wolf", "suspicious", "not_suspicious", "saved_from_attack", "no_attack", "died", "survived",
                      "no_visitors", "no_effect", "roleblocked", "not_said")
CLAIMED_ROLE_ENUM = Literal[tuple(roles)]
CLAIMED_RESULT_ENUM = Literal[(*roles, *NIGHT_RESULT_WORDS)]


def _expects_structure(annotation) -> bool:
    # A field whose declared type is a nested model / list / dict — i.e. a place where a JSON
    # string can only be an encoding accident, never a legal value.
    if get_origin(annotation) in (list, dict):
        return True
    return isinstance(annotation, type) and issubclass(annotation, BaseModel)

class LenientToolCallModel(BaseModel):

    # Base for every schema in this module. Handle models with unconstrained tool-calling backends which sometimes
    # emit a nested object or list as a JSON string. Normalising by parsing the string back before validation. Parse failures and
    # wrong shapes still fail loudly. LOSSY repairs (e.g. off-enum folding) are deliberately NOT
    # generalized — each lives as an explicit per-field validator (see PlayerRead.confidence).
    # Model-visible: NEVER add a class docstring in this module (it folds into the JSON schema
    # sent to the model → leaks); comments only.


    @model_validator(mode="before")
    @classmethod
    def _parse_stringified_structures(cls, data):
        if not isinstance(data, dict):
            # rejects non dictionary 
            return data
        for name, value in data.items():
            # find and check original field exists and type
            field = cls.model_fields.get(name)
            # Skip if value is not json-parsable string
            if field is None or not isinstance(value, str):
                continue
            if _expects_structure(field.annotation):
                try:
                    data[name] = json.loads(value)
                except ValueError:
                    pass  # leave it; the field's own validation rejects loudly
        return data


# Per-memory applicability verdict. Emitted BEFORE the action field (prospective commitment: the
# vote/message/target follows the reasoning rather than rationalising it). The "one verdict per
# numbered observation" instruction lives in the PROMPT BODY (memory-context block), not here — these
# descriptions stay terse. Model-visible: no class docstring.
class MemoryVerdict(LenientToolCallModel):
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
class StrategyVerdict(LenientToolCallModel):
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
class PlayerRead(LenientToolCallModel):
    player: str = Field(description="A living player's ID (never your own).")
    why: str = Field(description="One line of evidence for this read; write 'unchanged' if your read has not moved.")
    suspected_role: Literal[("unclear", *roles)] = Field(description="Your best guess of this player's role; 'unclear' if you cannot tell.")
    confidence: Literal["low", "high"] = Field(description="How sure you are.")

    # Tool-calling backends (DeepSeek) describe the enum but don't constrain generation to it,
    # and "medium" is the standard off-menu invention — fold it to "low" instead of burning a
    # retry. Validators never enter the JSON schema, so the model still sees a clean low|high.
    @field_validator("confidence", mode="before")
    @classmethod
    def _fold_medium_to_low(cls, value):
        if isinstance(value, str) and value.strip().lower() == "medium":
            return "low"
        return value


class Accusation(LenientToolCallModel):
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


class RoleClaim(LenientToolCallModel):
    player: str = Field(description="Player ID who made the claim")
    claimed_role: str = Field(description="The role claimed")
    evidence: str = Field(
        description=(
            "Evidence supporting the claim: describe public corroboration "
            "if any, otherwise 'unverified'"
        ),
    )


class Alliance(LenientToolCallModel):
    players: list[str] = Field(description="Player IDs in this alliance or bloc")
    basis: str = Field(description="What the alignment is based on (1 sentence)")


class VillageDynamics(LenientToolCallModel):
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


class DaySummaryOutput(LenientToolCallModel):
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


# The discussion-evidence pass (P2): the summary stops asking who stayed quiet — its answer fed the
# next day's prompts. Same keys as the originals, so stored summaries read the same downstream.
# Model-visible: no class docstring.
class VillageDynamicsV2(VillageDynamics):
    drivers: str = Field(
        description=(
            "Who is driving the discussion, and what evidence are they using? "
            "Name specific player IDs. 1-2 sentences."
        ),
    )


class DaySummaryOutputV2(DaySummaryOutput):
    village_dynamics: VillageDynamicsV2


# Day summary v3 (audit 2026-10-03; discussion_evidence.md §6.4): every claim attributed to whoever
# made it and checked against the game master's record, with claimed results as fields so code can
# keep a running claim record across days. Keeps v1's four top-level keys and their sub-fields, so
# stored summaries and the frontend read it unchanged. Model-visible: no class docstrings.
class AccusationV3(Accusation):
    reasoning: str = Field(
        description=(
            "The accusers' stated reasoning, written as what they argued (e.g. 'player_8 argued "
            "that player_2 survived an attack'), never as fact. 1-2 sentences."
        ),
    )
    disputed_by: str = Field(
        description=(
            "Who, besides the target, disputed this accusation and why, in one sentence. "
            "Empty string if no one did."
        ),
    )
    record_check: str = Field(
        description=(
            "If the accusation rests on an event that the game master's record contradicts or never "
            "announced, say so and cite the record (e.g. 'no attack on player_2 was ever announced'). "
            "Empty string otherwise."
        ),
    )


class ClaimedResult(LenientToolCallModel):
    night: int = Field(description="The night the claimed action happened; 0 if the player did not say")
    target: str = Field(description="Player ID the claimed action was on")
    result: str = Field(
        description=(
            "What the player says happened, in a few words (e.g. 'is a wolf', 'protected, was "
            "attacked', 'shot, survived')"
        ),
    )


class RoleClaimV3(RoleClaim):
    evidence: str = Field(
        description=(
            "The claim checked against the game master's record: 'supported: ...' or "
            "'contradicted: ...' citing the record, or 'unverified' if the record says nothing either way"
        ),
    )
    claimed_results: list[ClaimedResult] = Field(
        default_factory=list,
        description=(
            "Every result this player claimed today (investigations, protections, shots), one entry "
            "each. Empty list if none."
        ),
    )
    status: Literal["new", "repeated", "changed", "retracted"] = Field(
        description=(
            "new = the player's first claim; repeated = the same claim as on record; changed = a "
            "different role or different results from what is on record; retracted = withdrawn"
        ),
    )


class DaySummaryOutputV3(LenientToolCallModel):
    accusations: list[AccusationV3] = Field(
        default_factory=list,
        description="All distinct accusations from the discussion. List every accusation separately.",
    )
    role_claims: list[RoleClaimV3] = Field(
        default_factory=list,
        description="Any role claims made during discussion, including repeated ones. Empty list if none.",
    )
    alliances: list[Alliance] = Field(
        default_factory=list,
        description="Any alliances or voting blocs that formed. Empty list if none.",
    )
    village_dynamics: VillageDynamicsV2


# Day summary v4 (2026-10-04; discussion_evidence.md §6.6): the summariser only transcribes. It records
# the day's accusations and each role claim with its claimed night actions in fixed words; code folds
# the claims into the running ledger and checks them against the engine's record. Alliances, village
# dynamics and the summariser's own verdict on a claim are gone. Keeps the `accusations` and
# `role_claims` keys (with `player` / `claimed_role`), which the frontend and the tagger read.
# Model-visible: no class docstrings.
class ClaimedNightAction(LenientToolCallModel):
    night: int = Field(description="The night the action happened; 0 if the player did not say")
    action: Literal["investigate", "protect", "shoot", "kill", "watch", "follow", "sigil", "block", "conceal", "bet", "pick", "no_action"] = Field(
        description=(
            "What the player says they already did that night (not a plan for a coming night); no_action "
            "when they say they did not act or visited no one that night (held fire, kept a watch or a "
            "sigil, stayed home, did not visit someone)"
        ),
    )
    target: str = Field(description="Player ID the action was on; for no_action, the player they say they did not visit, or empty string")
    result: CLAIMED_RESULT_ENUM = Field(
        description=(
            "What the player says came of it. investigate: suspicious or not_suspicious (or the role "
            "they say they found). protect: saved_from_attack or no_attack. shoot / kill: died or "
            "survived. watch: no_visitors if they say no one visited; follow: no_visitors if they say the "
            "player visited no one. sigil: no_effect if they say it had no effect. Any action: roleblocked "
            "if they say they were blocked and it was not carried out. not_said if they did not say, or said "
            "it only vaguely."
        ),
    )
    reason: str = Field(
        description=(
            "If this differs from a plan the player stated earlier for that night (see the claims "
            "already on record), the reason they gave for the difference, briefly in their words. "
            "Empty string if it does not differ or they gave none."
        ),
    )
    seen: list[str] = Field(
        default_factory=list,
        description=(
            "watch / follow only: the exact player_ids the player says they saw (visitors of the watched "
            "player, or where the followed player went). Empty list otherwise, or if they say they saw no one."
        ),
    )


class PlannedNightAction(LenientToolCallModel):
    action: Literal["investigate", "protect", "shoot", "kill", "watch", "follow", "sigil", "block", "conceal", "bet", "pick"] = Field(
        description="What the player says they will do tonight",
    )
    target: str = Field(description="Player ID they say they will do it on")


class RoleClaimV4(LenientToolCallModel):
    player: str = Field(description="Player ID who made the claim")
    claimed_role: Literal[(*roles, "none")] = Field(
        description='The role claimed (or withdrawn); "none" when the player claims no role but says what they did or did not do at night',
    )
    kind: Literal["claimed", "retracted"] = Field(
        description="claimed = the player claims this role today (also when repeating it); retracted = they withdrew it",
    )
    night_actions: list[ClaimedNightAction] = Field(
        default_factory=list,
        description="Every night action this player claimed today, one entry each. Empty list if none.",
    )
    planned_actions: list[PlannedNightAction] = Field(
        default_factory=list,
        description=(
            "What the player said they will do tonight, one entry per action; if they changed it "
            "during the day, only their final word. Empty list if none."
        ),
    )


class AccusationV4(AccusationV3):
    # Every written field is capped at 30 words (2026-10-04): DeepSeek wrote a median of 40 and up to
    # 92 per field, and agents read all of it every day. 3.5 flash-lite already writes about 20.
    reasoning: str = Field(
        description=(
            "The accusers' stated reasoning, written as what they argued (e.g. 'player_8 argued "
            "that player_2 survived an attack'), never as fact. At most 30 words."
        ),
    )
    defense: str = Field(
        description="How the target responded, at most 30 words. Empty string if no defense given.",
    )
    disputed_by: str = Field(
        description=(
            "Who, besides the target, disputed this accusation and why, at most 30 words. "
            "Empty string if no one did."
        ),
    )
    # v3's record_check flagged a claimed investigation as "never announced", but private night results
    # never are: only an event the game master would have announced counts.
    record_check: str = Field(
        description=(
            "If the accusation rests on a public event that the game master's record contradicts, or one "
            "the game master would have announced but did not (a death, a healer save, a vote), say so and "
            "cite the record, at most 30 words. Investigation results, protections and other private night "
            "actions are never announced, and nor is an attack on a player who cannot be killed at night, so "
            "their absence is not a conflict. Empty string otherwise."
        ),
    )


class DaySummaryOutputV4(LenientToolCallModel):
    accusations: list[AccusationV4] = Field(
        default_factory=list,
        description="All distinct accusations from the discussion. List every accusation separately.",
    )
    role_claims: list[RoleClaimV4] = Field(
        default_factory=list,
        description="Every role claim made today, including repeats of earlier ones. Empty list if none.",
    )


class SituationEntry(LenientToolCallModel):
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


class SituationSummary(LenientToolCallModel):
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
class AddressingExtraction(LenientToolCallModel):
    addressed_targets: list[AddressedTarget] = Field(
        description="Every player this message addresses; empty list if it addresses no one specific.",
    )


# The echo gate's verdict on one new line against the day so far (Phase 2). Model-visible: field
# descriptions only, every field required (flash-lite fails on optional fields).
class LineEchoVerdict(LenientToolCallModel):
    new_point: str = Field(
        description="The new line's point in one sentence: what it says about the game.",
    )
    adds: str = Field(
        description=(
            "What the new line says that no earlier line said: a reason, a fact, a name, a conclusion, "
            "a next step, a question put to a player, an answer to a player. Crediting an earlier "
            "speaker and then adding to their point counts as adding. Write exactly 'nothing' only if "
            "every part of the new line's point was already said by an earlier line."
        ),
    )
    same_point_as: str = Field(
        description=(
            "Empty string unless adds is 'nothing'. Then the player id of the FIRST earlier line that "
            "already made the whole point: the same observation, the same suspicion of the same player "
            "for the same reason, or the same proposal."
        ),
    )


# The opening filter's verdict on one opening line (Phase 2). Model-visible: field descriptions
# only, every field required.
class OpeningVerdict(LenientToolCallModel):
    player: str = Field(description="The player id whose line this verdict is about.")
    kind: Literal["claim", "night_action", "challenge", "repeat", "other"] = Field(
        description=(
            "claim = the speaker claims a role for themselves, or claims a role someone else claimed "
            "(a counterclaim); night_action = the speaker states their OWN night action or its result "
            "(whom they protected, investigated, shot, or that they held fire, and what they learned); "
            "challenge = the speaker disputes a claim made on an earlier day, giving a reason; "
            "repeat = the line only repeats an earlier line in this list that is not a claim; "
            "other = anything else: a deduction, a suspicion, advice, a general remark."
        ),
    )
    why: str = Field(description="One sentence: what the line does.")


class OpeningVerdicts(LenientToolCallModel):
    verdicts: list[OpeningVerdict] = Field(
        description="Exactly one verdict per line in the list, in the same order.",
    )



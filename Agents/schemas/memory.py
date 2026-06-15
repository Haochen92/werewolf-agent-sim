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
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from Agents.schemas.roles import ActionPhase, VALID_ACTION_PHASES_BY_ROLE, roles


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


def _compose_outcome(impact_on_final_game_outcome: str, immediate_response: str | None) -> str:
    """Fold the two outcome halves into one stored string, NET EFFECT FIRST so a skimming reader
    absorbs the end-of-game verdict before the immediate effect — the myopic-framing fix (extraction
    led with the immediate result and buried the deferred cost in a trailing clause). See
    evidence/memory_system/effectiveness/paired_ab/nethorizon_design.md."""
    parts = [impact_on_final_game_outcome]
    if immediate_response:
        parts.append(immediate_response)
    return " ".join(parts)


# ── v6 dimension schema (Phase B cell build) ────────────────────────────────────────────────
# A per-cell `SituationSchema` mixin DAG (build spec: evidence/phase_b/dimension_schema_build_spec.md).
# `_Embed` marks which dimension fields fold into the searchable embedding string; the unmarked
# numeric/enum fields (criticality numbers, direction enums) are reranker-only — the embedding
# bi-encoder mangles magnitudes/signs, so they are pulled out (their *implication* is phrased into a
# marked free-text field for recall instead). The marker lives in Annotated metadata, which Pydantic
# does NOT serialize into the model-visible JSON schema (verified) — so it never reaches a model.
class _Embed:
    """Annotated marker: this field's value is folded into the composed embedding string at `order`,
    prefixed with `label` (empty label = lead, no prefix)."""

    def __init__(self, label: str = "", order: int = 0) -> None:
        self.label = label
        self.order = order


def compose_situation_embed(obj: BaseModel) -> str:
    """Generic prefix serializer: walk the instance's `_Embed`-marked fields, in marker order,
    prefix-label each present (non-empty) field, join. Auto-tailors per cell because the marked
    field set does — query and storage compositions cannot diverge because both are the same
    `SituationSchema` subclass run through this one function."""
    parts: list[tuple[int, str]] = []
    for name, field in type(obj).model_fields.items():
        mark = next((m for m in field.metadata if isinstance(m, _Embed)), None)
        if mark is None:
            continue
        val = getattr(obj, name, None)
        if val is None or (isinstance(val, str) and not val.strip()):
            continue
        parts.append((mark.order, f"{mark.label}: {val}" if mark.label else str(val)))
    parts.sort(key=lambda t: t[0])
    return " ".join(text for _, text in parts)


class Observation(BaseModel):
    perspective: str = Field(
        description=(
            "The role this observation is most useful for: wolf, villager, "
            "healer, investigator, vigilante, or serial_killer"
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
    impact_on_final_game_outcome: str = Field(
        description=(
            "The NET effect of this approach on THIS role's win condition, judged "
            "from the END of the game (you know the final result). An action that "
            "helped in the moment but contributed to this role's later elimination "
            "or the faction's loss is a NET NEGATIVE — say so explicitly and name "
            "the causal chain (what it led to). If the net effect is genuinely "
            "untraceable, write 'unclear' and why. May reveal actual roles. 1-2 sentences."
        )
    )
    immediate_response: str = Field(
        description=(
            "How others responded in the moment — the immediate, same- or next-turn "
            "effect, before the longer-term consequence. 1 sentence."
        )
    )
    net_verdict: Literal["positive", "negative", "mixed", "unclear"] = Field(
        description=(
            "This approach's net effect on the role's win condition in one word: "
            "positive, negative, mixed, or unclear. Use 'unclear' honestly when the "
            "game does not let you trace the consequence — do not force a guess."
        )
    )

    @computed_field
    @property
    def outcome(self) -> str:
        """Stored outcome string, NET EFFECT FIRST then immediate response. Computed (not a
        model field) so it stays out of the extraction schema sent to the model while every
        downstream `.outcome` reader (dedup / store write / prefilter) keeps working unchanged."""
        return _compose_outcome(self.impact_on_final_game_outcome, self.immediate_response)

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
            "healer, investigator, vigilante, or serial_killer"
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


# ── Villager·day cell (v6, cheap-first slice) ───────────────────────────────────────────────
# Concrete cell = BaseSituation + WithConsensus + WithHeat + WithTargetLandscape, per the build
# spec §2 cell table. Additive: the legacy Observation/StrategyPoint above stay live (other roles +
# the v5 pipeline); the full DAG rebuild + live-path rewiring is gated behind the criticality screen.
# Model-visible (extraction output) → keep Field(description=), NO class docstring (folds into the
# JSON schema → leak). Criticality numbers + the direction enum carry NO _Embed marker (reranker-only).
# Field(description=) is a SHORT what-it-is label (model-visible/FROZEN → keep minimal); the rich
# how-to-fill guidance + examples live in the prompt (RULES + situation_quality + driver_horizon).
class BaseSituation(BaseModel):
    situation: Annotated[str, _Embed("", 10)] = Field(
        description="The core game dynamic — the concrete event or conflict and who is involved."
    )
    information_landscape: Annotated[str, _Embed("Information landscape", 20)] = Field(
        description="What evidence exists and its type (information-rich vs information-starved)."
    )
    players_alive: int = Field(description="How many players are alive right now — a plain count.")
    distance_to_parity: int = Field(
        description="Eliminations until the leading remaining evil faction can win (0 = next result can end it)."
    )
    is_swing: bool = Field(description="True if a single vote or kill here flips which faction is winning.")
    criticality_stakes: Annotated[str, _Embed("Stakes", 30)] = Field(
        description="What the criticality numbers imply for this decision, as board reality (not a bare label)."
    )


class WithConsensus(BaseModel):
    consensus_text: Annotated[str, _Embed("Consensus", 40)] = Field(
        description="How aligned the village is and on what basis (the room, not who is under pressure)."
    )
    my_position: Annotated[str, _Embed("My position", 50)] = Field(
        description="Where the agent stands vs the forming consensus (driving / with majority / holding out)."
    )
    consensus_direction: Literal["aligns_with_my_read", "opposes_my_read", "no_clear_direction"] = Field(
        description="Consensus vs the agent's expressed read: aligns_with_my_read / opposes_my_read / no_clear_direction."
    )


class WithHeat(BaseModel):
    heat_now: Annotated[str, _Embed("Heat", 60)] = Field(
        description="How much suspicion is on the agent right now, and on what basis."
    )


class WithTargetLandscape(BaseModel):
    target_landscape: Annotated[str, _Embed("Target landscape", 70)] = Field(
        description="The candidates this decision chooses among, their public role status, and evidence-vs-behavior basis."
    )


class VillagerDaySituation(WithTargetLandscape, WithHeat, WithConsensus, BaseSituation):
    pass


class VillagerDayObservation(VillagerDaySituation):
    perspective: Literal["villager"] = Field(
        description="The role this observation is for — villager."
    )
    action_phase: Literal["day_discussion", "day_vote"] = Field(
        description="The day phase this observation applies to: day_discussion or day_vote."
    )
    approach: str = Field(description="What the agent did or failed to do in that situation.")
    impact_on_final_game_outcome: str = Field(
        description="The NET effect on the villager win condition, judged from game end ('unclear' if untraceable)."
    )
    immediate_response: str = Field(description="The immediate, in-the-moment effect, before the longer-term consequence.")
    net_verdict: Literal["positive", "negative", "mixed", "unclear"] = Field(
        description="The net effect on the villager win condition in one word."
    )

    @computed_field
    @property
    def outcome(self) -> str:
        """Stored outcome string, NET EFFECT FIRST then immediate response (see _compose_outcome)."""
        return _compose_outcome(self.impact_on_final_game_outcome, self.immediate_response)

    @property
    def composed_situation(self) -> str:
        return compose_situation_embed(self)


class VillagerDayExtraction(BaseModel):
    observations: list[VillagerDayObservation] = Field(
        description=(
            "Villager-perspective observations from the day phases of the game, each "
            "with its structured situation dimensions and net outcome."
        )
    )


# ── Full DAG mixins (step 4) ────────────────────────────────────────────────────────────────
# Remaining dimension mixins + conditioners + the shared observation payload, so the 11 concrete
# cells (spec §2 table) compose by multiple inheritance. Model-visible → Field(description=) only,
# NO class docstrings. Numeric/enum fields carry NO _Embed marker (reranker-only).
class WithForwardExposure(BaseModel):
    forward_exposure: Annotated[str, _Embed("Forward exposure", 65)] = Field(
        description="What a contemplated visible move would reveal or commit the agent to, and its reversibility."
    )


class WithPublicPrivate(BaseModel):
    public_private_text: Annotated[str, _Embed("Public vs private", 80)] = Field(
        description="The gap between what the agent privately knows and the public read."
    )
    divergence_sign: Literal["confirms", "contradicts", "no_divergence"] = Field(
        description="Private knowledge vs the public read: confirms / contradicts / no_divergence."
    )


class WithBulletsLeft(BaseModel):
    bullets_left: int = Field(
        description="How many vigilante shots remain (0 = plays as a regular villager)."
    )


class WithAllyRevealed(BaseModel):
    ally_revealed: bool = Field(
        description="Whether the agent's wolf partner has been publicly revealed or eliminated."
    )


class CellObservationMixin(BaseModel):
    approach: str = Field(description="What the agent did or failed to do in that situation.")
    impact_on_final_game_outcome: str = Field(
        description="The NET effect on this role's win condition, judged from game end ('unclear' if untraceable)."
    )
    immediate_response: str = Field(description="The immediate, in-the-moment effect, before the longer-term consequence.")
    net_verdict: Literal["positive", "negative", "mixed", "unclear"] = Field(
        description="The net effect on this role's win condition in one word."
    )

    @computed_field
    @property
    def outcome(self) -> str:
        """Stored outcome string, NET EFFECT FIRST then immediate response (see _compose_outcome)."""
        return _compose_outcome(self.impact_on_final_game_outcome, self.immediate_response)

    @property
    def composed_situation(self) -> str:
        return compose_situation_embed(self)


# ── Concrete cells (spec §2: 11 cells; day = day_discussion+day_vote merged) ──────────────────
# Day cells (all carry the villager·day spine: criticality + consensus + heat + target). Power/
# deceiver day cells add forward_exposure (F) + public_private (G); wolf adds ally_revealed, vig
# adds bullets_left. Night cells drop consensus/heat (day phenomena) -> criticality + target (+ F on
# observable kills, + bullets_left for vigilante). VillagerDayObservation above is the villager·day cell.
_DAY_PHASES = Literal["day_discussion", "day_vote"]


class HealerDayObservation(
    BaseSituation, WithConsensus, WithHeat, WithTargetLandscape,
    WithForwardExposure, WithPublicPrivate, CellObservationMixin,
):
    perspective: Literal["healer"] = Field(description="The role this observation is for — healer.")
    action_phase: _DAY_PHASES = Field(description="day_discussion or day_vote.")


class InvestigatorDayObservation(
    BaseSituation, WithConsensus, WithHeat, WithTargetLandscape,
    WithForwardExposure, WithPublicPrivate, CellObservationMixin,
):
    perspective: Literal["investigator"] = Field(description="The role this observation is for — investigator.")
    action_phase: _DAY_PHASES = Field(description="day_discussion or day_vote.")


class VigilanteDayObservation(
    BaseSituation, WithConsensus, WithHeat, WithTargetLandscape,
    WithForwardExposure, WithPublicPrivate, WithBulletsLeft, CellObservationMixin,
):
    perspective: Literal["vigilante"] = Field(description="The role this observation is for — vigilante.")
    action_phase: _DAY_PHASES = Field(description="day_discussion or day_vote.")


class WolfDayObservation(
    BaseSituation, WithConsensus, WithHeat, WithTargetLandscape,
    WithForwardExposure, WithPublicPrivate, WithAllyRevealed, CellObservationMixin,
):
    perspective: Literal["wolf"] = Field(description="The role this observation is for — wolf.")
    action_phase: _DAY_PHASES = Field(description="day_discussion or day_vote.")


class SerialKillerDayObservation(
    BaseSituation, WithConsensus, WithHeat, WithTargetLandscape,
    WithForwardExposure, WithPublicPrivate, CellObservationMixin,
):
    perspective: Literal["serial_killer"] = Field(description="The role this observation is for — serial_killer.")
    action_phase: _DAY_PHASES = Field(description="day_discussion or day_vote.")


class HealerNightObservation(BaseSituation, WithTargetLandscape, CellObservationMixin):
    perspective: Literal["healer"] = Field(description="The role this observation is for — healer.")
    action_phase: Literal["night_action"] = Field(description="night_action.")


class InvestigatorNightObservation(BaseSituation, WithTargetLandscape, CellObservationMixin):
    perspective: Literal["investigator"] = Field(description="The role this observation is for — investigator.")
    action_phase: Literal["night_action"] = Field(description="night_action.")


class VigilanteNightObservation(
    BaseSituation, WithTargetLandscape, WithForwardExposure, WithBulletsLeft, CellObservationMixin
):
    perspective: Literal["vigilante"] = Field(description="The role this observation is for — vigilante.")
    action_phase: Literal["night_action"] = Field(description="night_action.")


class WolfNightObservation(
    BaseSituation, WithTargetLandscape, WithForwardExposure, CellObservationMixin
):
    perspective: Literal["wolf"] = Field(description="The role this observation is for — wolf.")
    action_phase: Literal["night_action"] = Field(description="night_action.")


class SerialKillerNightObservation(
    BaseSituation, WithTargetLandscape, WithForwardExposure, CellObservationMixin
):
    perspective: Literal["serial_killer"] = Field(description="The role this observation is for — serial_killer.")
    action_phase: Literal["night_action"] = Field(description="night_action.")


# (role, action_phase) -> concrete cell schema. Day phases share a cell per role (the v6 merge).
_CELL_REGISTRY: dict[tuple[str, str], type[BaseModel]] = {}
for _r, _cls in (
    ("villager", VillagerDayObservation),
    ("healer", HealerDayObservation),
    ("investigator", InvestigatorDayObservation),
    ("vigilante", VigilanteDayObservation),
    ("wolf", WolfDayObservation),
    ("serial_killer", SerialKillerDayObservation),
):
    _CELL_REGISTRY[(_r, "day_discussion")] = _cls
    _CELL_REGISTRY[(_r, "day_vote")] = _cls
for _r, _cls in (
    ("healer", HealerNightObservation),
    ("investigator", InvestigatorNightObservation),
    ("vigilante", VigilanteNightObservation),
    ("wolf", WolfNightObservation),
    ("serial_killer", SerialKillerNightObservation),
):
    _CELL_REGISTRY[(_r, "night_action")] = _cls


def cell_observation_schema_for(role: str, action_phase: str) -> type[BaseModel] | None:
    """The per-cell v6 extraction schema for a (role, action_phase), or None for combinations the
    game has no decision at (e.g. villager night)."""
    return _CELL_REGISTRY.get((role, action_phase))


# ── Per-cell SITUATION schemas (dims only, no outcome payload) — the LIVE query schema (step 4C). ──
# Same dimension mixins as the Observation cells, so `compose_situation_embed` produces the IDENTICAL
# embed string for the same field values — that is the load-bearing symmetry that lets a live query
# match the stored observations. Model-visible (the situation-summary LLM emits these).
class _SituationCell(BaseModel):
    @property
    def composed_situation(self) -> str:
        return compose_situation_embed(self)


# villager·day situation cell already exists as VillagerDaySituation; give it the composed property.
class VillagerDaySituationCell(VillagerDaySituation, _SituationCell):
    pass


class PowerDaySituationCell(
    BaseSituation, WithConsensus, WithHeat, WithTargetLandscape,
    WithForwardExposure, WithPublicPrivate, _SituationCell,
):
    pass  # healer / investigator day (PowerRoleDay dims)


class VigilanteDaySituationCell(
    BaseSituation, WithConsensus, WithHeat, WithTargetLandscape,
    WithForwardExposure, WithPublicPrivate, WithBulletsLeft, _SituationCell,
):
    pass


class WolfDaySituationCell(
    BaseSituation, WithConsensus, WithHeat, WithTargetLandscape,
    WithForwardExposure, WithPublicPrivate, WithAllyRevealed, _SituationCell,
):
    pass


class SerialKillerDaySituationCell(
    BaseSituation, WithConsensus, WithHeat, WithTargetLandscape,
    WithForwardExposure, WithPublicPrivate, _SituationCell,
):
    pass


class PowerNightSituationCell(BaseSituation, WithTargetLandscape, _SituationCell):
    pass  # healer / investigator night (criticality + target)


class VigilanteNightSituationCell(
    BaseSituation, WithTargetLandscape, WithForwardExposure, WithBulletsLeft, _SituationCell
):
    pass


class DeceiverNightSituationCell(
    BaseSituation, WithTargetLandscape, WithForwardExposure, _SituationCell
):
    pass  # wolf / serial_killer night (criticality + target + forward_exposure)


_SITUATION_CELL_REGISTRY: dict[tuple[str, str], type[BaseModel]] = {}
for _r, _cls in (
    ("villager", VillagerDaySituationCell),
    ("healer", PowerDaySituationCell),
    ("investigator", PowerDaySituationCell),
    ("vigilante", VigilanteDaySituationCell),
    ("wolf", WolfDaySituationCell),
    ("serial_killer", SerialKillerDaySituationCell),
):
    _SITUATION_CELL_REGISTRY[(_r, "day_discussion")] = _cls
    _SITUATION_CELL_REGISTRY[(_r, "day_vote")] = _cls
for _r, _cls in (
    ("healer", PowerNightSituationCell),
    ("investigator", PowerNightSituationCell),
    ("vigilante", VigilanteNightSituationCell),
    ("wolf", DeceiverNightSituationCell),
    ("serial_killer", DeceiverNightSituationCell),
):
    _SITUATION_CELL_REGISTRY[(_r, "night_action")] = _cls


def cell_situation_schema_for(role: str, action_phase: str) -> type[BaseModel] | None:
    """The per-cell v6 LIVE-query situation schema (dims only). Mirrors the observation cell's
    dimensions so query and stored embeddings compose identically."""
    return _SITUATION_CELL_REGISTRY.get((role, action_phase))


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
    net_verdict: str = ""
    """Extraction's one-word net judgment (positive/negative/mixed/unclear); metadata only — not
    embedded, not injected to the agent. Its unclear-rate doubles as an extraction-reliability metric.
    Empty on legacy entries written before the net-horizon schema."""
    source_game_winner: Optional[str] = None
    """Objective game_id -> batch-record winner join, stamped at build/dump time (no LLM). Soft
    analysis / rerank signal ONLY — never a hard filter (the role winning != the action being good)."""
    role_faction_won: Optional[bool] = None
    """Whether this observation's perspective-role shared the winning faction in its source game."""
    players_alive: Optional[int] = None
    """v6 criticality number — players alive when the lesson applies. Reranker/conditioned-retrieval
    signal only (never embedded; the embedding mangles magnitudes). None on legacy v5 entries."""
    distance_to_parity: Optional[int] = None
    """v6 criticality number — eliminations until a game-ending parity. Reranker-only. None on legacy."""
    is_swing: Optional[bool] = None
    """v6 criticality flag — whether a single result here flips who is winning. Reranker-only. None on legacy."""
    consensus_direction: Optional[str] = None
    """v6 enum — consensus aligns_with / opposes / no_clear_direction vs the agent's read. Reranker-only."""


class StoredStrategyPoint(BaseModel):
    """A deduped strategy point as persisted: situation + action, plus usage counters
    (retrieved/used and positive/neutral/negative outcome tallies) for impact analysis."""

    observation_count: int
    """How many source strategy points deduped into this stored record."""
    last_observed: datetime
    game_id: Optional[str] = ""
    situation: str
    action: str
    retrieved_count: int = 0
    """Times this point was returned by retrieval (denominator for impact)."""
    used_count: int = 0
    """Times an agent actually adopted it after retrieval."""
    positive_count: int = 0
    """Adoptions whose game outcome was scored positive."""
    neutral_count: int = 0
    """Adoptions whose game outcome was scored neutral."""
    negative_count: int = 0
    """Adoptions whose game outcome was scored negative."""


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

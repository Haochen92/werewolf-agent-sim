"""The wire contract: every event a client can ever receive, as one flat discriminated union.

Transcribed from the ruled derivation in frontend/docs/event_derivation.md — every non-IGNORED table
row is one frozen model here; nothing else may reach a client. Two ruled structures:

- DurableEvent vs EphemeralEvent base classes: durable events carry the global `seq`, are
  persisted to the event log, and replay; ephemeral events (pacing) exist only on the live
  stream — the exporter's signature takes DurableEvent, so an ephemeral event cannot be
  persisted by construction.
- EVENT_TIERS registry: the LIVE delivery audience per event type lives server-side (the router
  consumes it), never as a wire field. The import-time check below makes a union member without
  a registry entry a startup error — the exhaustiveness alarm.

These models are client-visible, not LLM-visible: the Agents/schemas leak rules do not apply,
and this module must stay import-independent of Agents/ (the wire contract feeds OpenAPI → TS
codegen and must not drag engine internals with it — shapes shared with the engine are
deliberately duplicated).
"""

from enum import Enum
from typing import Annotated, Any, Literal, Union, get_args

from pydantic import BaseModel, Field


# Vocabularies the engine owns and this module repeats on purpose (it must not import Agents/):
# tests/server/test_engine_sync.py checks the copies against the role registry. The pool is the
# ten-seat game's twelve roles; villager and wolf are the nine-seat game's, kept so archived
# replays still validate, never dealt.
PoolRole = Literal[
    "investigator", "sentinel", "trailseer", "vigilante", "sigilist", "healer",
    "chanteuse", "illusionist", "serial_killer", "necromancer", "speculator", "fortune_teller",
]
Role = Literal[
    "investigator", "sentinel", "trailseer", "vigilante", "sigilist", "healer",
    "chanteuse", "illusionist", "serial_killer", "necromancer", "speculator", "fortune_teller",
    "villager", "wolf",
]
PACK_ROLES = ("chanteuse", "illusionist", "wolf")
"""The roles that share the pack's chat (the faction tier)."""
Winner = Literal["villagers", "wolves", "serial_killer", "necromancer"]
AttackerType = Literal["wolves", "serial_killer", "vigilante", "sigilist", "reanimated_wolves", "reanimated_vigilante", "reanimated_sigilist"]


class Tier(str, Enum):
    """LIVE routing audience. Everything lands in the durable log regardless; at game_over the
    client's entitlement flips to observer and the server streams the withheld backlog."""

    PUBLIC = "public"
    """Delivered to every connected client."""
    FACTION = "faction"
    """Delivered to wolf seats (the only faction with a channel)."""
    SEAT = "seat"
    """Delivered to the single recipient seat named by the event's `player` field."""
    OBSERVER = "observer"
    """Delivered to nobody live; log-only until the game_over unlock."""


class DurableEvent(BaseModel, frozen=True):
    """Base for every persisted, replayable event."""

    seq: int
    """Global per-game ordering, assigned by the translator; the reconnect cursor."""
    day: int
    """Game day the event belongs to."""


class EphemeralEvent(BaseModel, frozen=True):
    """Base for live-stream-only events: no seq, never persisted, absent from replay."""

    day: int


# --- lifecycle ---------------------------------------------------------------


class GameStarted(DurableEvent, frozen=True):
    type: Literal["game_started"] = "game_started"
    seats: list[str]
    """Player ids at the table, in seating order."""
    cast_role_counts: dict[str, int]
    """Public casting: role -> count. The client derives the alive-role census from this."""
    lineup: list[str] = Field(default_factory=list)
    """The ten roles dealt, in the rules block's order (public). Empty on a nine-seat record."""


class RoleAssigned(DurableEvent, frozen=True):
    """Seat-private deal: one per seat at game start."""

    type: Literal["role_assigned"] = "role_assigned"
    player: str
    """Recipient seat (the router key for every SEAT-tier event)."""
    role: Role
    pack: list[str] | None = None
    """Fellow wolves — wolves only."""
    bullets: int | None = None
    """Starting bullets — vigilante only (nine-seat records; the ten-seat game sends uses)."""
    uses: int | None = None
    """What a limited ability starts with: bullets, sigils, conceals, self-bets, the one pick."""


class RolesAssigned(DurableEvent, frozen=True):
    """O-tier full deal at game start: nobody receives it live; exists so the game_over
    backlog replay has survivor roles from minute zero."""

    type: Literal["roles_assigned"] = "roles_assigned"
    roles: dict[str, str]
    """player -> role, the complete deal."""


class PhaseChange(DurableEvent, frozen=True):
    """Node-identity marker: anchored on initialize_game/one_more_day (day), START_VOTING
    (voting), and NIGHT_START (night)."""

    type: Literal["phase_change"] = "phase_change"
    phase: Literal["day", "voting", "night"]


class GameOver(DurableEvent, frozen=True):
    """Thin by ruling: an entitlement flip, not a data package — the server follows it with
    the withheld observer-tier backlog from the durable log."""

    type: Literal["game_over"] = "game_over"
    winner: Winner | None = None
    """None for a drawn game."""
    neutral_result: str | None = None
    """How the neutral fared, beside the winner ("won", "lost", "won (2 points)"); None on a
    nine-seat record."""


# --- day: discussion ---------------------------------------------------------


class TurnStarted(DurableEvent, frozen=True):
    """Edge-emitted (route_speaker): who is about to speak. Not a promise of speech."""

    type: Literal["turn_started"] = "turn_started"
    player: str


DayRound = Literal["opening", "discussion", "proactive", "closing"]


class RoundOpened(DurableEvent, frozen=True):
    """A round of the day begins: its players are all given a turn at once (START_OPENING,
    START_CLOSING). Their lines follow as speech events once the round is collected; a player
    of the round with no speech passed, so there is no pass event for a round (the X-ray's
    pass_marker still arrives, observer-only)."""

    type: Literal["round_opened"] = "round_opened"
    round: Literal["opening", "closing"]
    players: list[str]
    """Who is in the round, in the order their lines will be played."""


class Speech(DurableEvent, frozen=True):
    type: Literal["speech"] = "speech"
    channel_seq: int
    """Position in the day's public transcript (the state-side DayChannel seq) — the join key
    annotations reference; distinct from the global `seq`."""
    player: str
    message: str
    claim: str = "none"
    """The role the speaker's own output claimed in this line, or "none". The claim ledger's
    role lines are built from these; a record from before the field has "none" throughout."""


class PassMarker(DurableEvent, frozen=True):
    """A discussion turn that produced no speech — hidden from the table, observer-only."""

    type: Literal["pass_marker"] = "pass_marker"
    channel_seq: int
    player: str
    pass_reason: Literal["voluntary", "novelty_gated", "generation_failed", "round_echo",
                         "opening_filtered"] | None = None
    """None only on legacy records predating the typed reasons."""
    gated: bool = False
    gated_candidate: str | None = None
    """The suppressed draft message when the novelty gate fired."""


class FiringReasonAnnotation(DurableEvent, frozen=True):
    """Scheduler trace for a turn: why it fired. Joins the speech/pass via about_channel_seq."""

    type: Literal["firing_reason"] = "firing_reason"
    about_channel_seq: int
    player: str
    tier: Literal["reactive", "proactive"]
    owes: list[str] = Field(default_factory=list)


class WireAddressedTarget(BaseModel, frozen=True):
    target: str
    addressed_form: Literal["question", "response", "mention"]
    stance: Literal["accusation", "defense", "agreement", "neutral"]


class AddressedTargetsAnnotation(DurableEvent, frozen=True):
    """Structured who-this-addresses tags. Joins the speech via about_channel_seq."""

    type: Literal["addressed_targets"] = "addressed_targets"
    about_channel_seq: int
    player: str
    targets: list[WireAddressedTarget]


class StrategyUpdate(DurableEvent, frozen=True):
    type: Literal["strategy_update"] = "strategy_update"
    player: str
    strategy: str


class WireLesson(BaseModel, frozen=True):
    index: int
    """1-based position in the numbered list the agent saw; a verdict points at it."""
    key: str
    """The store record's key: the same lesson keeps its key across games."""
    situation: str
    action: str
    dimensions: dict[str, Any] | None = None
    """The lesson's situation broken into its labelled parts (the separate descriptions, the
    counts, and the fixed categories such as info_rich / info_starved or safe / exposed),
    copied as the store keeps them. `situation` is these parts joined into one sentence. Absent
    for lessons stored before the parts were kept."""


class WireLessonVerdict(BaseModel, frozen=True):
    strategy_index: int
    verdict: Literal["follow", "override", "not_relevant"]
    why: str


class WireObservation(BaseModel, frozen=True):
    index: int
    key: str
    situation: str
    outcome: str
    dimensions: dict[str, Any] | None = None
    """The observation's situation broken into its labelled parts, copied as the store keeps
    them. Absent for observations stored before the parts were kept."""


class WireObservationVerdict(BaseModel, frozen=True):
    memory_index: int
    verdict: Literal["fully_applies", "partly_applies", "does_not_apply"]
    why: str


class MemoryConsulted(DurableEvent, frozen=True):
    """What one AI decision weighed from past games: the lessons and observations
    retrieved for it, and the agent's verdict on each. Only memory-on games emit it, and
    only from day 2 (day 1 never retrieves). Streamed from inside the acting node, so a
    re-run fires it again; the translator sends one per (player, day, round, phase)."""

    type: Literal["memory_consulted"] = "memory_consulted"
    player: str
    role: Role
    round: int
    action_phase: Literal["day_discussion", "day_vote", "night_action"]
    lessons: list[WireLesson]
    verdicts: list[WireLessonVerdict]
    observations: list[WireObservation]
    applicability: list[WireObservationVerdict]


class WireRead(BaseModel, frozen=True):
    player: str
    """The player being read (never the reader)."""
    suspected_role: str
    """The reader's best guess, or "unclear"."""
    confidence: Literal["low", "high"]
    why: str


class PlayerReads(DurableEvent, frozen=True):
    """One AI seat's suspicions at one decision: who it reads as what, how sure, and why.
    Every decision that produced reads, memory on or off. Streamed from inside the acting
    node, so a re-run fires it again; the translator sends one per (player, day, round,
    phase). Private by nature — observer tier."""

    type: Literal["player_reads"] = "player_reads"
    player: str
    role: Role
    round: int
    action_phase: Literal["day_discussion", "day_vote", "night_action"]
    reads: list[WireRead]


class WireExtractedObservation(BaseModel, frozen=True):
    perspective: Role
    """The role the observation is a lesson for."""
    action_phase: Literal["day_discussion", "day_vote", "night_action"]
    situation: str
    approach: str
    outcome: str
    net_verdict: str
    dimensions: dict[str, Any] | None = None
    """Every labelled part the extraction filled in for this observation (the same parts the
    store keeps). Absent when the extraction wrote only the plain sentences."""


class WireExtractedLesson(BaseModel, frozen=True):
    perspective: Role
    action_phase: Literal["day_discussion", "day_vote", "night_action"]
    situation: str
    action: str
    dimensions: dict[str, Any] | None = None
    """Every labelled part the extraction filled in for this lesson (the same parts the store
    keeps). Absent when the extraction wrote only the plain sentences."""


class MemoryExtracted(DurableEvent, frozen=True):
    """What the finished game taught: the observations and lessons extracted from it,
    raw (before any dedup against the store — a served game never writes the store).
    Memory-on games only; streamed from the post-game node, after game_over, so every
    viewer is already an observer when it arrives."""

    type: Literal["memory_extracted"] = "memory_extracted"
    observations: list[WireExtractedObservation]
    strategy_points: list[WireExtractedLesson]


class InputRequest(DurableEvent, frozen=True):
    """The human seat's turn prompt (interrupt surface). Night instances fire inside a
    parallel superstep — resume semantics gated on the spike verification."""

    type: Literal["input_request"] = "input_request"
    player: str
    action_kind: Literal[
        "discuss",
        "vote",
        "wolf_discuss",
        "wolf_vote",
        "carrier_kill",
        "healer_target",
        "investigator_target",
        "sentinel_target",
        "trailseer_target",
        "serial_killer_target",
        "vigilante_target",
        "sigil_target",
        "block_target",
        "conceal",
        "necromancer_target",
        "speculator_pick",
        "bet_target",
    ]
    candidates: list[str] = Field(default_factory=list)
    """Legal targets where the action needs one; empty for free-text turns."""
    bodies: list[str] = Field(default_factory=list)
    """A necromancer's turn: the dead players it may act through tonight, one of which the
    answer names beside its target. Empty for every other turn."""
    round: DayRound | None = None
    """For a discuss ask, the round of the day it belongs to, so the composer can label it
    (an opening, the open floor, a last word); None for every other kind."""
    deadline: str | None = None
    """When the AFK timer will delegate this turn to the seat's agent (ISO-8601 UTC),
    the client's countdown source. None = no timer armed (solo games — the lone human
    may think forever). Additive optional field, ruled 2026-08-20."""


class DaySummary(DurableEvent, frozen=True):
    """Shown next morning — client render rule, no buffer (buffers gate entitlement;
    render timing gates pacing)."""

    type: Literal["day_summary"] = "day_summary"
    summary: str


class DaySummaryStructured(DurableEvent, frozen=True):
    """Structured form of the summary (accusations / role claims; older games also alliances and
    village dynamics). Public, like the text: it only transcribes the public discussion, and the
    browser's Record tab shows it during the day (2026-10-04; it was observer-only before)."""

    type: Literal["day_summary_structured"] = "day_summary_structured"
    data: dict
    """The summarizer's structured output, verbatim. PROVISIONAL shape — typed sub-models
    once the summarizer's output schema is stable enough to freeze into the wire contract."""


# --- day: voting -------------------------------------------------------------


class VoteCast(DurableEvent, frozen=True):
    """Ballot content, released as a batch at COLLECT_VOTES from the translator buffer."""

    type: Literal["vote_cast"] = "vote_cast"
    voter: str
    votee: str


class GmMessage(DurableEvent, frozen=True):
    """Verbatim GM narration (record fidelity outranks derivability for authored text)."""

    type: Literal["gm_message"] = "gm_message"
    channel_seq: int
    text: str


class LynchResult(DurableEvent, frozen=True):
    """The day death atom (= the dead_roster delta) + the free-rider fields the node computed."""

    type: Literal["lynch_result"] = "lynch_result"
    outcome: Literal["lynched", "tie", "abstain", "no_vote"]
    player: str | None = None
    role: Role | None = None
    """Publicly revealed on death — both fields None unless outcome == "lynched"."""
    vote_counts: dict[str, int]
    no_lynch_streak: int


class RosterUpdate(DurableEvent, frozen=True):
    """Union only: the translator merges the wolf-partitioned survivor lists before the
    public tier ever sees them."""

    type: Literal["roster_update"] = "roster_update"
    surviving_players: list[str]


class PackRosterUpdate(DurableEvent, frozen=True):
    type: Literal["pack_roster_update"] = "pack_roster_update"
    surviving_wolves: list[str]


# --- night -------------------------------------------------------------------


class NightAction(DurableEvent, frozen=True):
    """O-tier committed target of a single-target night actor. No seat ack by ruling —
    the seat re-learns its act from dawn's gm_message; the live client echoes locally."""

    type: Literal["night_action"] = "night_action"
    actor: str
    role: Role
    target: str


class WolfMessage(DurableEvent, frozen=True):
    """Wolf-channel talk. wolf == "game_master" for the server-authored SK-whiff note."""

    type: Literal["wolf_message"] = "wolf_message"
    round: int
    wolf: str
    message: str
    passed: bool = False
    """A chat round the wolf passed: nothing to add (the ten-seat chat)."""


class WolfVote(DurableEvent, frozen=True):
    """Binding kill vote — buffered by the translator until the tally (blind voting +
    wire/state parity), then flushed together with wolf_kill_decided."""

    type: Literal["wolf_vote"] = "wolf_vote"
    wolf: str
    votee: str


class WolfKillDecided(DurableEvent, frozen=True):
    """The pack's kill: the carrier's choice in the ten-seat game (the plurality tally in a
    nine-seat record) — the only way a wolf seat learns it before dawn."""

    type: Literal["wolf_kill_decided"] = "wolf_kill_decided"
    target: str
    carrier: str | None = None
    """The wolf who carries the kill; None on a nine-seat record."""


class NightDeath(BaseModel, frozen=True):
    player: str
    role: str
    """Publicly revealed on death; "" when an illusionist hid it."""
    attacker_types: list[AttackerType]
    """Attacker TYPE is public flavor; attacker identity never is."""
    concealed: bool = False


class NightSave(BaseModel, frozen=True):
    player: str
    attacker_types: list[AttackerType]


class NightResult(DurableEvent, frozen=True):
    """The night death atom (= the dead_roster delta) + free-riders. Empty deaths = quiet
    night. Silent whiffs (an immune target) appear NOWHERE here — absence is the design."""

    type: Literal["night_result"] = "night_result"
    deaths: list[NightDeath]
    save: NightSave | None = None
    saves: list[NightSave] = Field(default_factory=list)
    """Every announced save (the ten-seat game can have several); `save` keeps the first."""
    pick: str | None = None
    """The side the speculator picked tonight, announced without the seat."""


class InvestigationResult(DurableEvent, frozen=True):
    """Survival-gated in the engine node: no committed delta -> this event never exists."""

    type: Literal["investigation_result"] = "investigation_result"
    player: str
    """Recipient seat (the investigator)."""
    target: str
    role: Role


class VigilanteConfirmation(DurableEvent, frozen=True):
    """Private immune-whiff confirmation: the shot target is the serial killer."""

    type: Literal["vigilante_confirmation"] = "vigilante_confirmation"
    player: str
    """Recipient seat (the vigilante)."""
    target: str


class BulletsRemaining(DurableEvent, frozen=True):
    type: Literal["bullets_remaining"] = "bullets_remaining"
    player: str
    """Recipient seat (the vigilante)."""
    count: int


class UsesRemaining(DurableEvent, frozen=True):
    """What is left of a limited ability after the night: bullets, sigils, conceals, self-bets,
    the speculator's pick."""

    type: Literal["uses_remaining"] = "uses_remaining"
    player: str
    """Recipient seat (the holder)."""
    role: Role
    count: int


class NightRecord(DurableEvent, frozen=True):
    """One seat's private record of its night action and what it may know of the result, as
    the engine wrote it (Agents/rules/night_record.py): the sentinel's visitors, the sigil's
    outcome, the investigator's read, the pack's kill for each wolf."""

    type: Literal["night_record"] = "night_record"
    player: str
    """Recipient seat."""
    actor: str
    """The acting seat, or "wolves" for the pack's kill."""
    action: str
    target: str | None = None
    result: str
    """The fixed result word."""
    outcome: str
    """The result in plain words, as the seat reads it."""
    seen: list[str] = Field(default_factory=list)


# --- ephemeral (pacing) ------------------------------------------------------


class PhaseProgress(EphemeralEvent, frozen=True):
    """Anonymous pacing snapshot, one mechanism for both waits. `total` derives from PUBLIC
    knowledge only — night: alive-role census (wolf pack = 1) with padded ~20-30s completions
    for non-actors, NEVER the real fan-out list; day_vote: the surviving roster (no padding
    needed). Snapshot semantics: duplicates are harmless, the client applies monotonic-max."""

    type: Literal["phase_progress"] = "phase_progress"
    stage: Literal["night", "day_vote"]
    done: int
    total: int


# --- unions + tier registry --------------------------------------------------

DurableGameEvent = Annotated[
    Union[
        GameStarted,
        RoleAssigned,
        RolesAssigned,
        PhaseChange,
        GameOver,
        TurnStarted,
        RoundOpened,
        Speech,
        PassMarker,
        FiringReasonAnnotation,
        AddressedTargetsAnnotation,
        StrategyUpdate,
        MemoryConsulted,
        MemoryExtracted,
        PlayerReads,
        InputRequest,
        DaySummary,
        DaySummaryStructured,
        VoteCast,
        GmMessage,
        LynchResult,
        RosterUpdate,
        PackRosterUpdate,
        NightAction,
        WolfMessage,
        WolfVote,
        WolfKillDecided,
        NightResult,
        InvestigationResult,
        VigilanteConfirmation,
        BulletsRemaining,
        UsesRemaining,
        NightRecord,
    ],
    Field(discriminator="type"),
]

EphemeralGameEvent = PhaseProgress

EVENT_TIERS: dict[str, Tier] = {
    "game_started": Tier.PUBLIC,
    "role_assigned": Tier.SEAT,
    "roles_assigned": Tier.OBSERVER,
    "phase_change": Tier.PUBLIC,
    "game_over": Tier.PUBLIC,
    "turn_started": Tier.PUBLIC,
    "round_opened": Tier.PUBLIC,
    "speech": Tier.PUBLIC,
    "pass_marker": Tier.OBSERVER,
    "firing_reason": Tier.OBSERVER,
    "addressed_targets": Tier.OBSERVER,
    "strategy_update": Tier.OBSERVER,
    "memory_consulted": Tier.OBSERVER,
    "memory_extracted": Tier.OBSERVER,
    "player_reads": Tier.OBSERVER,
    "input_request": Tier.SEAT,
    "day_summary": Tier.PUBLIC,
    "day_summary_structured": Tier.PUBLIC,
    "vote_cast": Tier.PUBLIC,
    "gm_message": Tier.PUBLIC,
    "lynch_result": Tier.PUBLIC,
    "roster_update": Tier.PUBLIC,
    "pack_roster_update": Tier.FACTION,
    "night_action": Tier.OBSERVER,
    "wolf_message": Tier.FACTION,
    "wolf_vote": Tier.FACTION,
    "wolf_kill_decided": Tier.FACTION,
    "night_result": Tier.PUBLIC,
    "investigation_result": Tier.SEAT,
    "vigilante_confirmation": Tier.SEAT,
    "bullets_remaining": Tier.SEAT,
    "uses_remaining": Tier.SEAT,
    "night_record": Tier.SEAT,
}


def _durable_types() -> set[str]:
    return {
        get_args(member.model_fields["type"].annotation)[0]
        for member in get_args(get_args(DurableGameEvent)[0])
    }


# The exhaustiveness alarm: a union member without a tier (or a stale registry key) is a
# startup error, not a silently unrouted event.
_missing = _durable_types() - set(EVENT_TIERS)
_stale = set(EVENT_TIERS) - _durable_types()
assert not _missing, f"durable events missing a tier: {sorted(_missing)}"
assert not _stale, f"EVENT_TIERS names unknown events: {sorted(_stale)}"

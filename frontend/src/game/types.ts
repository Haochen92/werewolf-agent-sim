/**
 * `GameView` — what `foldEvents` produces and every presentational component reads.
 *
 * Derived from the completeness table in `docs/ux_journeys.md` §8: each field exists
 * because a row of that table needs it. Nothing speculative — if no render consumes it,
 * it is not here.
 *
 * Three facts about the wire drove the shape (all verified against the 593-event seed,
 * not assumed):
 *
 * 1. **The day channel is one dense counter per day, shared by `speech`, `pass_marker`
 *    AND `gm_message`** — 0..N with no gaps and no duplicates. So a day's transcript is
 *    an ordered list of SLOTS, each occupied by exactly one of the three, and the O-tier
 *    annotations (`firing_reason`, `addressed_targets`) attach to a slot by
 *    `(day, channel_seq)`. All 149 annotations in the seed join cleanly; 18 of them join
 *    to a PASS, not a speech — the annotation model must not assume speeches.
 * 2. **Night N is tagged `day: N`** and its narration occupies day N's channel, so the
 *    fold keys nights by their own day. Where a night's outcome *renders* (bottom of day
 *    N per D19, or a dawn band atop day N+1 per D20) is the view layer's call — both read
 *    the same `DayView.night`. Same for `day_summary`, which fires at the END of day N
 *    and renders next morning (the wire docstring says so explicitly).
 * 3. **Not every day has all three phases.** Day 1 of the seed goes day → night with no
 *    `voting` phase change at all (three passes, then `lynch_result: no_vote`). The
 *    scrubber's steps come from the `phase_change` events that actually happened.
 */
import type {
  ActionKind,
  AddressedTarget,
  AttackerType,
  DurableGameEvent,
  FiringReason,
  InputRequest,
  LynchOutcome,
  NightDeath,
  NightSave,
  PassReason,
  Phase,
  Winner,
} from '@/types/contracts';

// --- transcript ------------------------------------------------------------

/** O-tier annotations attached to whichever slot `about_channel_seq` points at. */
export interface SlotAnnotations {
  /** Why the scheduler fired this turn (reactive/proactive + who it owes). */
  firing: { tier: FiringReason['tier']; owes: string[] } | null;
  /** Structured who-this-addresses tags. */
  addressed: AddressedTarget[];
}

interface SlotBase {
  day: number;
  /** Position in the day channel — the join key into `DayView.annotations`. */
  channelSeq: number;
  /** Global durable seq — the ordering authority and the store's live-vs-folded key. */
  seq: number;
  /** Seq of the `turn_started` this slot resolved (X-ray turn markers, D12). */
  turnStartedSeq: number | null;
}

export interface SpeechSlot extends SlotBase {
  kind: 'speech';
  player: string;
  message: string;
}

/**
 * A turn that produced no speech. Observer-tier: absent entirely for live players, which
 * is why day 1 of the seed looks empty with X-ray off — it is a real quiet day, not a bug.
 */
export interface PassSlot extends SlotBase {
  kind: 'pass';
  player: string;
  passReason: PassReason | null;
  gated: boolean;
  /** The vetoed speech — what the agent WOULD have said. The differentiator (11 in the seed). */
  gatedCandidate: string | null;
}

export interface GmSlot extends SlotBase {
  kind: 'gm';
  text: string;
}

export type ChannelSlot = SpeechSlot | PassSlot | GmSlot;

/** `turn_started` — who was about to speak. Not a promise of speech (it may resolve to a pass). */
export interface TurnMarker {
  seq: number;
  day: number;
  player: string;
  /** channelSeq of the slot it resolved into; null = never resolved (live tail, or dropped). */
  resolvedChannelSeq: number | null;
}

// --- votes, nights, deaths -------------------------------------------------

export interface Ballot {
  seq: number;
  voter: string;
  votee: string;
}

export interface DayVote {
  /** Released as one batch at the tally — render as a single vote block (D14), not a drip. */
  ballots: Ballot[];
  outcome: LynchOutcome | null;
  /** Null for tie / abstain / no_vote. */
  lynched: string | null;
  lynchedRole: string | null;
  voteCounts: Record<string, number>;
  /** Consecutive dayless days; phrase it in words only when > 1 (D15). */
  noLynchStreak: number;
}

export interface WolfEntry {
  seq: number;
  round: number;
  /** `"game_master"` for the server-authored SK-whiff note — render as a GM line inside the tint. */
  wolf: string;
  message: string;
}

export interface NightView {
  day: number;
  wolfChannel: WolfEntry[];
  wolfVotes: { seq: number; wolf: string; votee: string }[];
  wolfKill: string | null;
  /** O-tier committed targets of every single-target actor. */
  actions: { seq: number; actor: string; role: string; target: string }[];
  deaths: NightDeath[];
  save: NightSave | null;
  /** `night_result` seen — distinguishes "quiet night" from "night still running". */
  resolved: boolean;
}

export type DeathCause = 'lynch' | AttackerType;

export interface DeathRecord {
  player: string;
  /** Deaths are role-revealing on the wire, in both directions (lynch and night). */
  role: string | null;
  day: number;
  seq: number;
  causes: DeathCause[];
}

// --- day page --------------------------------------------------------------

export interface DayView {
  day: number;
  /** Dense, ordered by channelSeq. */
  slots: ChannelSlot[];
  /**
   * channelSeq → O-tier annotations. Kept as a side map rather than a field on the slot so
   * the join is order-independent by construction: an annotation that somehow arrived
   * before its slot still lands correctly, with no pending-buffer machinery. This also
   * mirrors the wire ("annotations join the speech via about_channel_seq") at the read site.
   */
  annotations: Record<number, SlotAnnotations>;
  turnMarkers: TurnMarker[];
  vote: DayVote;
  night: NightView | null;
  /** Emitted at the end of this day; renders atop day+1 (D13). */
  summary: string | null;
  /** The phases this day actually entered, in order — the scrubber's steps. */
  phases: Phase[];
}

// --- seat-private ----------------------------------------------------------

export interface RoleCard {
  role: string;
  /** Wolves only. */
  pack: string[] | null;
  /** Vigilante only. */
  bullets: number | null;
}

export type PrivateResult =
  | { kind: 'investigation'; seq: number; day: number; target: string; role: string }
  | { kind: 'vigilante_confirmation'; seq: number; day: number; target: string }
  | { kind: 'bullets'; seq: number; day: number; count: number };

export interface MeView {
  /** From the caller (`GameStatus.you`), never guessed — see the fold options. */
  seat: string | null;
  role: RoleCard | null;
  pending: {
    seq: number;
    day: number;
    actionKind: ActionKind;
    /** The server's list is the ONLY source of legal targets — never derive eligibility. */
    candidates: string[];
    deadline: string | null;
  } | null;
  privateResults: PrivateResult[];
  alive: boolean;
}

// --- observer tier ---------------------------------------------------------

export interface AgentXray {
  /** In emission order — the strategy timeline. */
  strategy: { seq: number; day: number; text: string }[];
}

export interface XrayView {
  /**
   * Whether any observer-tier event has arrived. NOT a client-side gate: the server
   * withholds O-tier until R7, so this is simply "is there anything to show". True for a
   * whole replay from the first fold; flips mid-game exactly when the backlog lands.
   */
  available: boolean;
  /** player → role, merged from `roles_assigned` (O) and any `role_assigned` (S) seen. */
  roles: Record<string, string>;
  agents: Record<string, AgentXray>;
}

// --- the view --------------------------------------------------------------

export interface GameView {
  seats: string[];
  castRoleCounts: Record<string, number>;
  /** The newest day seen — the live view pins here; the replay scrubber picks any. */
  day: number;
  phase: Phase;
  /** Every phase entered, in order: the scrubber's step list. */
  timeline: { day: number; phase: Phase; seq: number }[];
  winner: Winner | null;
  alive: string[];
  dead: DeathRecord[];
  /** Wolf pack survivors (faction tier). */
  packRoster: string[];
  days: Record<number, DayView>;
  /**
   * The `turn_started` that has not yet resolved into a slot — D12's "Ralph is thinking…"
   * row. Always null at the end of a finished replay fold; only ever populated at a live
   * tail (or mid-scrub, if a view is folded to a partial log).
   */
  thinking: { seq: number; day: number; player: string } | null;
  me: MeView;
  xray: XrayView;
  /** Highest durable seq folded — the SSE resume cursor and the store's ordering guard. */
  lastSeq: number;
  /** Events the reducer knowingly dropped (`day_summary_structured`), for the test to assert on. */
  droppedEventTypes: string[];
}

export interface FoldOptions {
  /**
   * Which seat is "me". Supplied by the caller from `GameStatus.you` — never inferred from
   * `role_assigned`, because a REPLAY carries every seat's role_assigned (9 in the seed) and
   * inference would make `me` whichever seat was dealt last.
   */
  mySeat?: string | null;
}

export type { DurableGameEvent, InputRequest, Phase, Winner };

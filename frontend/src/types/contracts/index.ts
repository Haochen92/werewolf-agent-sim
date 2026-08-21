/**
 * The hand façade over generated `api.ts` — the ONLY contracts module app code imports.
 *
 * Everything here is an alias or a narrowing, never a redefinition: a regenerated `api.ts`
 * must break this file (loudly, at compile time) rather than leak a renamed shape into a
 * hundred components. The one exception is `PhaseProgress`, which is SSE-only and so never
 * reaches /openapi.json — it is transcribed from `server/schemas/events.py` and marked below.
 */
import type { components } from './api';

type S = components['schemas'];

// --- replay archive ---------------------------------------------------------

export type ReplaySummary = S['ReplayBase'];
export type ReplayGame = S['ReplayGame'];

// --- durable event union ----------------------------------------------------

/**
 * Derived from ReplayGame rather than re-listed: the union is 27 members and the server
 * owns its membership. Deriving means a new event type on the wire appears here for free
 * and the reducer's exhaustive switch fails to compile until it is handled.
 */
export type DurableGameEvent = ReplayGame['events'][number];

export type EventType = DurableGameEvent['type'];

/** Narrow the union by its `type` tag: `EventOf<'speech'>` → Speech. */
export type EventOf<T extends EventType> = Extract<DurableGameEvent, { type: T }>;

export type GameStarted = EventOf<'game_started'>;
export type RoleAssigned = EventOf<'role_assigned'>;
export type RolesAssigned = EventOf<'roles_assigned'>;
export type PhaseChange = EventOf<'phase_change'>;
export type GameOver = EventOf<'game_over'>;
export type TurnStarted = EventOf<'turn_started'>;
export type Speech = EventOf<'speech'>;
export type PassMarker = EventOf<'pass_marker'>;
export type FiringReason = EventOf<'firing_reason'>;
export type AddressedTargets = EventOf<'addressed_targets'>;
export type StrategyUpdate = EventOf<'strategy_update'>;
export type InputRequest = EventOf<'input_request'>;
export type DaySummary = EventOf<'day_summary'>;
export type VoteCast = EventOf<'vote_cast'>;
export type GmMessage = EventOf<'gm_message'>;
export type LynchResult = EventOf<'lynch_result'>;
export type RosterUpdate = EventOf<'roster_update'>;
export type PackRosterUpdate = EventOf<'pack_roster_update'>;
export type NightAction = EventOf<'night_action'>;
export type WolfMessage = EventOf<'wolf_message'>;
export type WolfVote = EventOf<'wolf_vote'>;
export type WolfKillDecided = EventOf<'wolf_kill_decided'>;
export type NightResult = EventOf<'night_result'>;
export type InvestigationResult = EventOf<'investigation_result'>;
export type VigilanteConfirmation = EventOf<'vigilante_confirmation'>;
export type BulletsRemaining = EventOf<'bullets_remaining'>;

// `day_summary_structured` is deliberately NOT aliased. The schema exists but the engine
// never emits it (build_plan §4: "schema-only, provisional — do not build on it"), and the
// 593-event seed confirms zero occurrences. The reducer drops it.

export type NightDeath = S['NightDeath'];
export type NightSave = S['NightSave'];
export type AddressedTarget = S['WireAddressedTarget'];
export type Winner = GameOver['winner'];
export type Phase = PhaseChange['phase'];
export type ActionKind = InputRequest['action_kind'];
export type PassReason = NonNullable<PassMarker['pass_reason']>;
export type AttackerType = NightDeath['attacker_types'][number];
export type LynchOutcome = LynchResult['outcome'];

// --- ephemeral (SSE-only, absent from OpenAPI) -------------------------------

/**
 * Transcribed by hand from `server/schemas/events.py::PhaseProgress`. Ephemeral events ride
 * the `pacing` SSE channel and never enter the durable log, so codegen cannot see them.
 * Snapshot semantics — the store applies monotonic-max, duplicates are harmless.
 */
export interface PhaseProgress {
  type: 'phase_progress';
  day: number;
  stage: 'night' | 'day_vote';
  done: number;
  total: number;
}

// --- live game / rooms (P2–P3 surfaces; typed now so the wire layer is complete) ---

export type GameStatus = S['GameStatus'];
/** `GameStatus.state` is a bare `str` server-side; these are its three registry values. */
export type GameState = 'waiting' | 'running' | 'finished';
export type GameCreated = S['GameCreated'];
export type SeatJoined = S['SeatJoined'];
export type RoomSummary = S['RoomSummary'];
export type RoomCreated = S['RoomCreated'];
export type NewGame = S['NewGame'];
export type NewRoom = S['NewRoom'];
export type JoinGame = S['JoinGame'];
export type RejoinGame = S['RejoinGame'];
export type TurnAccepted = S['TurnAccepted'];
export type ModelsMenu = S['ModelsMenu'];
export type ModelRow = S['ModelRow'];

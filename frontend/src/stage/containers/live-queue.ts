/**
 * Live pacing, the pure half (docs/beat_sheet.md §12). A live game has no transport: beats
 * play as events arrive, one after another, each at its normal hold. The rules, in order:
 *
 * - Every beat plays at normal speed, however many are queued (ruled 2026-10-01). A solo game's
 *   agents play at machine speed, so the stage plays at reading pace and lags the server; that
 *   is the design. (Until 2026-10-01 a backlog of three or more drained at fast speed, and so
 *   did everything before the seated human's prompt.)
 * - The dock never waits for the stage, but the stage does not hurry for it either: when the
 *   seated human's prompt is further down the queue, the beat on stage is cut short once (that
 *   is live-state.ts's business), and the rest play at normal speed.
 * - The winners' stand needs the roles, which arrive in the backlog after `game_over`, so that
 *   beat waits until they have landed. The verdict covers the wait.
 * - A catch-up (refresh, reconnect) shows the latest beat still and plays nothing.
 */
import type { SceneBeat } from '@/stage/beats/types';

export interface LiveStep {
  index: number;
  /** Always normal live; the type keeps the replay's speeds. */
  speed: 'normal' | 'fast';
}

export interface LiveContext {
  /** The seated human's seat, if any. */
  me: string | null;
  /** `roles_assigned` has landed (the backlog after game_over). */
  rolesLanded: boolean;
}

/**
 * The next beat to show after `shown`, at normal speed, or null to wait (nothing queued, or
 * the next beat is held for data that has not arrived).
 */
export function nextLiveStep(
  beats: readonly SceneBeat[],
  shown: number,
  ctx: LiveContext,
): LiveStep | null {
  const next = shown + 1;
  if (next >= beats.length) return null;
  if (beats[next].id === 'over.winners-stand' && !ctx.rolesLanded) return null;
  return { index: next, speed: 'normal' };
}

/** Where a client that just hydrated history lands: the latest beat, still. */
export function catchUpIndex(beats: readonly SceneBeat[]): number {
  return Math.max(0, beats.length - 1);
}

/**
 * Live pacing, the pure half (docs/beat_sheet.md §12). A live game has no transport: beats
 * play as events arrive, and the only question is how fast to play the ones the stage has not
 * shown yet. The rules, in order:
 *
 * - The dock never waits for the stage. If a prompt for the seated human is in the queue, the
 *   beats before it drain at fast speed so the stage catches up to the turn.
 * - Anything queued more than one beat behind the stream drains at fast speed; a single queued
 *   beat plays at normal speed.
 * - The winners' stand needs the roles, which arrive in the backlog after `game_over`, so that
 *   beat waits until they have landed. The verdict covers the wait.
 * - A catch-up (refresh, reconnect) shows the latest beat still and plays nothing.
 */
import type { SceneBeat } from '@/stage/beats/types';

export interface LiveStep {
  index: number;
  speed: 'normal' | 'fast';
}

export interface LiveContext {
  /** The seated human's seat, if any. */
  me: string | null;
  /** `roles_assigned` has landed (the backlog after game_over). */
  rolesLanded: boolean;
}

/**
 * The next beat to show after `shown`, and how fast, or null to wait (nothing queued, or the
 * next beat is held for data that has not arrived).
 */
export function nextLiveStep(
  beats: readonly SceneBeat[],
  shown: number,
  ctx: LiveContext,
): LiveStep | null {
  const next = shown + 1;
  if (next >= beats.length) return null;
  const beat = beats[next];
  if (beat.id === 'over.winners-stand' && !ctx.rolesLanded) return null;

  const prompt = beats.findIndex(
    (b, i) => i > shown && b.liveOnly === true && b.seat === ctx.me,
  );
  const behind = beats.length - 1 - shown;
  const fast = (prompt !== -1 && prompt > next) || behind > 1;
  return { index: next, speed: fast ? 'fast' : 'normal' };
}

/** Where a client that just hydrated history lands: the latest beat, still. */
export function catchUpIndex(beats: readonly SceneBeat[]): number {
  return Math.max(0, beats.length - 1);
}

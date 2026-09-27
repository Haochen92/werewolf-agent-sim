/**
 * A prompt's countdown, as the stage writes it: the day's dock, the ballot and the night
 * room's plate all read the same `m:ss` from the request's real time left, so the countdown
 * never waits for the stage.
 */

/** The last stretch of a turn, when the plate's bar turns red (ms). */
export const URGENT_MS = 10_000;

/** The time left as `m:ss`, rounded up so it shows 0:00 only when time is up; `-:--` with none. */
export function countText(remainingMs: number | null | undefined): string {
  if (remainingMs == null) return '-:--';
  const s = Math.max(0, Math.ceil(remainingMs / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

/** How much of the turn is left, 0–1; null without a deadline (a solo game, the workbench). */
export function countLeft(
  clock: { remainingMs: number; totalMs: number } | null | undefined,
): number | null {
  if (!clock || !(clock.totalMs > 0)) return null;
  return Math.max(0, Math.min(1, clock.remainingMs / clock.totalMs));
}

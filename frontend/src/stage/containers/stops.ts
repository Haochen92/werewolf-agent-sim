/**
 * The replay's stops (owner, 2026-09-30): with the X-ray on, the play pauses where the viewer
 * has a choice to make, and waits for it. Three of them:
 *
 * - the night hub (`rnight.hub`, a night with rooms to visit): tap a lit seat to visit that
 *   actor's room, watch them all in order, or end the night;
 * - the ballots in (`vote.closes`: every ballot has dropped, the count not begun): tap a seat to
 *   read what it voted on, then count the votes;
 * - the opening (`day.opening-prepares`; owner, 2026-10-16): every seat writes it at once, so
 *   tap a seat to read what it wrote (its line, or why it passed), then play it or skip it.
 *
 * A stop is a playback rule, nothing more: arrived at by the play, a step or a seek, the play
 * pauses there; play (the notice's ▶) moves on from it at once. A room visited by a tap plays
 * its steps and rests on its last (owner, 2026-09-30; it returned to the hub by itself), and
 * "Back to the night" is the way back. Nothing here is kept past the page.
 */
import type { SceneBeat } from '@/stage/beats/types';

/** The vote's stop: every ballot in and the lid down, before the count begins. */
export const VOTE_STOP = 'vote.closes';

/** The opening's stop: the round being written, before its first line plays. */
export const OPENING_STOP = 'day.opening-prepares';

/** Whether the beat at `index` is a stop in this cut (only the X-ray's cut has them). */
export function isStop(beats: readonly SceneBeat[], index: number, xray: boolean): boolean {
  const b = beats[index];
  if (!xray || !b) return false;
  if (b.id === VOTE_STOP || b.id === OPENING_STOP) return true;
  // a night with no room to visit has nothing to choose: the hub plays on
  return (
    b.id === 'rnight.hub' && beats.some((x) => x.id === 'rnight.spoke' && x.day === b.day)
  );
}

/** Which actor's room a spoke is in, that night: `2:pack`, `2:player_4`. */
export function branchOf(b: SceneBeat | undefined): string | null {
  return b?.id === 'rnight.spoke' && b.spoke ? `${b.day}:${b.spoke.actor}` : null;
}

/** The spoke is its room's last step: its mark landing (or the pack's last line). */
export function endsRoom(b: SceneBeat | undefined): boolean {
  return !!b?.spoke && b.id === 'rnight.spoke' && b.spoke.step === b.spoke.steps - 1;
}

/** Night `day`'s hub in the X-ray's cut, or -1. */
export function hubOf(beats: readonly SceneBeat[], day: number): number {
  return beats.findIndex((b) => b.id === 'rnight.hub' && b.day === day);
}

/**
 * "End the night": the first beat after night `day`'s whole (the morning), or, for a night
 * the log never finished, the first beat past its rooms. -1 when nothing follows.
 */
export function afterNight(beats: readonly SceneBeat[], day: number): number {
  const hub = hubOf(beats, day);
  if (hub < 0) return -1;
  const whole = beats.findIndex(
    (b, i) => i > hub && b.id === 'rnight.whole' && b.day === day,
  );
  if (whole >= 0) return whole + 1 < beats.length ? whole + 1 : -1;
  for (let i = hub + 1; i < beats.length; i++)
    if (!beats[i].id.startsWith('rnight.')) return i;
  return -1;
}

/**
 * "Skip the opening": the first beat after the round whose stop is at `index` (its lines and
 * its passes' placard), or -1 when nothing follows or the round is still being written.
 */
export function afterRound(beats: readonly SceneBeat[], index: number): number {
  const until = beats[index]?.roundUntil;
  if (until === undefined) return -1;
  return beats.findIndex((b, i) => i > index && b.seq >= until);
}

/** The actors visited on night `day`, from the `day:actor` keys the reducer keeps. */
export function visitedOn(keys: readonly string[], day: number): string[] {
  const at = `${day}:`;
  return keys.filter((k) => k.startsWith(at)).map((k) => k.slice(at.length));
}

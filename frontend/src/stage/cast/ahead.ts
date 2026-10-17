/**
 * The pictures the next turn will need, so the day's arrival finds them decoded. On iPhone
 * Safari a figure's picture is decoded when it is first painted, on the main thread, in the
 * same frames as the puppet's rise; decoded a turn ahead, the rise's first frames are its own
 * (build log §8.9). Only the next speaker's two poses: a held decode is memory, so one pair.
 * The pair is the turn's: a line ends talking, a pass ends at rest (`base`), whose picture was
 * otherwise first fetched as the puppet changed into it (the X-ray's passes popped, 2026-10-16).
 */
import type { Character } from '@/assets/manifest';
import type { SceneBeat } from '../beats/types';
import { seatNumber } from '../roles';

export type Pose = 'thinking' | 'talking' | 'base';

/** The next day turn after `index` with a puppet at the stand, and its speaker. */
function nextTurn(
  beats: readonly SceneBeat[],
  index: number,
  cast: readonly Character[],
): { beat: SceneBeat; character: Character } | null {
  for (let i = index + 1; i < beats.length; i++) {
    const b = beats[i];
    if (b.scene !== 'day') continue;
    const seat = b.subject ?? b.seat;
    if (!seat) continue;
    const n = seatNumber(seat);
    const c = cast[n - 1];
    if (c) return { beat: b, character: c };
  }
  return null;
}

/** The next day turn's speaker after `index`, if the beats ahead hold one. */
export function nextSpeaker(
  beats: readonly SceneBeat[],
  index: number,
  cast: readonly Character[],
): Character | null {
  return nextTurn(beats, index, cast)?.character ?? null;
}

/** The sources to decode ahead: the next speaker's arriving pose and the one it ends in, via `src`. */
export function spritesAhead(
  beats: readonly SceneBeat[],
  index: number,
  cast: readonly Character[],
  src: (character: Character, pose: Pose) => string,
): string[] {
  const next = nextTurn(beats, index, cast);
  if (!next) return [];
  const c = next.character;
  return [src(c, 'thinking'), src(c, next.beat.id === 'day.pass' ? 'base' : 'talking')];
}

/**
 * Which stretch of a game the landing's carriage plays (review §F7): day 3's vote through the
 * lynched seat's card going to the wing, in the public cut. Found by the beats' ids and days,
 * never by fixed numbers, so the fallback game (the newest, when the featured one is gone) gets
 * its own window: its first vote through that vote's end (the card to the wing after a lynch,
 * or the table going down after a tie), else the game's opening beats.
 */
import type { SceneBeat } from '@/stage/beats/types';

export interface FeaturedWindow {
  /** Indices into the beat list, both played. */
  from: number;
  to: number;
  /** The day the window is on, for the caption; null for the opening fallback. */
  day: number | null;
}

/** The featured day: the owner's pick for game 9369a5c1 (a wolf voted out, the truth shown). */
export const FEATURED_DAY = 3;

/** How many beats the last-resort window plays, from the top. */
const OPENING = 31;

/** The vote on `day` through the end of what it decided, or null if that day has no vote. */
function voteWindow(beats: readonly SceneBeat[], day: number): FeaturedWindow | null {
  const from = beats.findIndex((b) => b.id === 'vote.opens' && b.day === day);
  if (from === -1) return null;
  const lastOf = (id: SceneBeat['id']) =>
    beats.findLastIndex((b, i) => i > from && b.id === id && b.day === day);
  const wing = lastOf('lynch.card-to-wing');
  if (wing !== -1) return { from, to: wing, day };
  const down = lastOf('vote.table-down');
  if (down !== -1) return { from, to: down, day };
  return null;
}

export function featuredWindow(
  beats: readonly SceneBeat[],
  day: number = FEATURED_DAY,
): FeaturedWindow {
  const featured = voteWindow(beats, day);
  if (featured) return featured;
  const first = beats.find((b) => b.id === 'vote.opens');
  const fallback = first ? voteWindow(beats, first.day) : null;
  if (fallback) return fallback;
  return { from: 0, to: Math.max(0, Math.min(OPENING - 1, beats.length - 1)), day: null };
}

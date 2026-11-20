/**
 * What the landing's carriage plays (owner, 2026-10-22): a reel of the game's moments in the
 * X-ray's cut, not one vote. The deal done, its cards in place and face up, arrived at, not
 * played (the cards' drop and turn lagged on the owner's iPhone in this window); the first
 * night's hub and the pack's room, its chat read line by line; that night's morning, its bodies; the featured lines said by day; and
 * the featured day's vote through the voted-out seat's card going to the wing. Each part is
 * found by the beats' ids and days (and the lines by their events' seqs), never by fixed
 * indices, so the fallback game (the newest, when the featured one is gone) gets its own reel:
 * the same parts without the lines, its first vote for the vote. A part a game lacks is left
 * out; a game with none of them plays its opening.
 */
import type { SceneBeat } from '@/stage/beats/types';

export interface FeaturedReel {
  /** Indices into the X-ray's cut, in order. */
  reel: number[];
  /** The day of the reel's vote; null when it has none. */
  day: number | null;
}

/**
 * The featured game's own moments: game e45eda20 (owner's pick, 2026-10-22). On day 3 seat 10,
 * the Illusionist, says the real Investigator's claim came too late (`speech` seq 335); seat 1,
 * the real one, answers that it checked seat 10 and found it Suspicious (seq 341); the table
 * votes seat 1 out.
 */
export const FEATURED = { day: 3, lines: [335, 341] } as const;

/** How many beats the last-resort reel plays, from the top. */
const OPENING = 31;

const range = (from: number, to: number) =>
  from < 0 || to < from ? [] : Array.from({ length: to - from + 1 }, (_, i) => from + i);

/** The vote on `day` through the end of what it decided, or nothing if that day has no vote. */
function voteOn(beats: readonly SceneBeat[], day: number): number[] {
  const from = beats.findIndex((b) => b.id === 'vote.opens' && b.day === day);
  if (from === -1) return [];
  const lastOf = (id: SceneBeat['id']) =>
    beats.findLastIndex((b, i) => i > from && b.id === id && b.day === day);
  const wing = lastOf('lynch.card-to-wing');
  return range(from, wing !== -1 ? wing : lastOf('vote.table-down'));
}

/** The first night: its hub, then the pack's room, every step of it. */
function firstNight(beats: readonly SceneBeat[]): number[] {
  const hub = beats.findIndex((b) => b.id === 'rnight.hub');
  if (hub === -1) return [];
  const day = beats[hub].day;
  const pack = beats.flatMap((b, i) =>
    b.id === 'rnight.spoke' && b.day === day && b.spoke?.actor === 'pack' ? [i] : [],
  );
  return [hub, ...pack];
}

/** The first night's morning: the shutter down through its last card laid down. */
function firstMorning(beats: readonly SceneBeat[]): number[] {
  const from = beats.findIndex((b) => b.id === 'morning.shutter-down');
  if (from === -1) return [];
  const day = beats[from].day;
  return range(
    from,
    beats.findLastIndex((b) => b.id === 'morning.card-down' && b.day === day),
  );
}

export function featuredReel(
  beats: readonly SceneBeat[],
  featured?: { day: number; lines: readonly number[] },
): FeaturedReel {
  const firstVote = beats.find((b) => b.id === 'vote.opens')?.day ?? null;
  let day = featured && voteOn(beats, featured.day).length ? featured.day : firstVote;
  let vote = day === null ? [] : voteOn(beats, day);
  if (!vote.length) [day, vote] = [null, []];
  const lines = featured
    ? beats.flatMap((b, i) =>
        b.id === 'day.speech' && featured.lines.includes(b.seq) ? [i] : [],
      )
    : [];
  // the deal done: the X-ray's cards face up, or (a cut without them) the cards dealt
  const faceUp = beats.findIndex((b) => b.id === 'deal.face-up');
  const dealt =
    faceUp !== -1 ? faceUp : beats.findIndex((b) => b.id === 'deal.cards-dealt');
  const reel = [
    ...(dealt !== -1 ? [dealt] : []),
    ...firstNight(beats),
    ...firstMorning(beats),
    ...lines,
    ...vote,
  ];
  if (!reel.length)
    return { reel: range(0, Math.min(OPENING, beats.length) - 1), day: null };
  return { reel: [...new Set(reel)].sort((a, b) => a - b), day };
}

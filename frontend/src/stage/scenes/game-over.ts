/**
 * The facts the ending is drawn from, read out of the folded view (beat sheet §10): who won
 * and who of them is still standing, where the game stopped, how the stand is set for one,
 * two or three winners, and how each seat went.
 *
 * `game_over` itself says only who won. Everything else the ending shows (the survivors, the
 * roles, the fates) is what the log already held, so it is worked out here rather than sent.
 */
import type { GameView } from '@/game/types';
import type { Phase } from '../paint/materials';
import { factionOf, seatNumber, type Faction } from '../roles';

export type EndedAt = 'morning' | 'lynch';

/** The hour the shutter rises on for each winner: the village's day, the wolves' night. */
export const WINNERS_HOUR: Record<Faction, Phase> = {
  villagers: 'day',
  wolves: 'night',
  serial_killer: 'dusk',
};

export const WINNER_LINE: Record<Faction, string> = {
  villagers: 'The village has won',
  wolves: 'The wolves have won',
  serial_killer: 'The serial killer has won',
};

/** The sigil a winning side is shown by. */
export const WINNER_SIGIL: Record<Faction, string> = {
  villagers: 'villager',
  wolves: 'wolf',
  serial_killer: 'serial_killer',
};

/**
 * Where the game stopped: at a morning (the night of the last day was resolved) or at a
 * lynch (the vote took the last one out, and no night began).
 */
export function endedAt(view: GameView): EndedAt {
  return view.days[view.day]?.night?.resolved ? 'morning' : 'lynch';
}

/**
 * A seat's role as far as this viewer knows it: the observer's roles once they are out, the
 * seated human's own card, a wolf's packmates.
 */
export function knownRole(view: GameView, seat: string): string | null {
  if (view.xray.roles[seat]) return view.xray.roles[seat];
  if (seat === view.me.seat && view.me.role) return view.me.role.role;
  if (view.packRoster.includes(seat) && view.me.role?.role === 'wolf') return 'wolf';
  return null;
}

/** The winning side's survivors, in seat order: the ones who take the stand. */
export function winnersOf(view: GameView): string[] {
  if (!view.winner) return [];
  return view.seats.filter(
    (s) => view.alive.includes(s) && factionOf(knownRole(view, s)) === view.winner,
  );
}

export interface StandSet {
  /** Each figure's size (1 = a day speaker's). */
  scale: number;
  /** Each figure's offset from the stand's centre, as a fraction of the puppet box's width. */
  offsets: number[];
  /** How much wider the stand's box is than a single speaker's. */
  widen: number;
}

/**
 * The stand for n figures side by side (bench 73): one at full size, two at 0.78, three at
 * 0.6, the box widened ×1.36 and ×1.6 to hold them; all of it at 0.84 when the side slot is
 * open, so three still fit the narrower room. More than three is not a case the game produces
 * (a side wins with at most three standing); they would be squeezed at the three's size.
 */
export function standSet(n: number, side = false): StandSet {
  const kk = side ? 0.84 : 1;
  const scale = (n <= 1 ? 1 : n === 2 ? 0.78 : 0.6) * kk;
  const spread = (n <= 1 ? 0 : n === 2 ? 0.5 : 0.52) * kk;
  const widen = n <= 1 ? 1 : (n === 2 ? 1.36 : 1.6) * kk;
  const k = n > 3 ? 3 / n : 1;
  return {
    scale: scale * (n > 3 ? k : 1),
    offsets: Array.from(
      { length: Math.max(1, n) },
      (_, i) => (i - (n - 1) / 2) * spread * k,
    ),
    widen,
  };
}

/** "3", "3 and 8", "1, 7 and 9". */
export function seatList(seats: readonly string[]): string {
  const ns = seats.map(seatNumber);
  return ns.length <= 1
    ? String(ns[0] ?? '')
    : `${ns.slice(0, -1).join(', ')} and ${ns[ns.length - 1]}`;
}

/** "Seat 8 is the last of them standing" · "Seats 3 and 8 are the last of them standing". */
export function lastStanding(seats: readonly string[]): string {
  if (seats.length === 0) return 'None of them is left standing';
  return seats.length === 1
    ? `Seat ${seatList(seats)} is the last of them standing`
    : `Seats ${seatList(seats)} are the last of them standing`;
}

const BY: Record<string, string> = {
  wolves: 'the wolves',
  serial_killer: 'the serial killer',
  vigilante: 'the vigilante',
};

/** How a seat went: "survived", "day 3, voted out", "night 4, the wolves". */
export function fateOf(view: GameView, seat: string): string {
  const d = view.dead.find((x) => x.player === seat);
  if (!d) return 'survived';
  if (d.causes.includes('lynch')) return `day ${d.day}, voted out`;
  return `night ${d.day}, ${d.causes.map((c) => BY[c] ?? c).join(' and ')}`;
}

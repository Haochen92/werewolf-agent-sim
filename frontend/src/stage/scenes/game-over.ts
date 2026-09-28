/**
 * The facts the ending is drawn from, read out of the folded view (beat sheet §10): who won
 * and who of them is still standing, where the game stopped, how the stand is set for one,
 * two or three winners, and how each seat went.
 *
 * `game_over` itself says only who won. Everything else the ending shows (the survivors, the
 * roles, the fates) is what the log already held, so it is worked out here rather than sent.
 */
import { REACH, type Character } from '@/assets/manifest';
import type { GameView } from '@/game/types';
import type { Phase } from '../paint/materials';
import { factionOf, seatNumber, type Faction } from '../roles';
import { standBox, type StageGeometry } from '../units';

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
  /** The centre of the place kept on the rail right of two or more (`aside`), as `offsets`. */
  beside?: number;
}

/** The share of the widened stand the figures may span, and the room kept either side of it. */
const FILL = 0.92,
  AIR = 40;

/**
 * The stand for one, two or three figures side by side (bench 73): one at full size, two at 0.78,
 * three at 0.6, all of it at 0.84 when the side slot is open. Neighbours stand so their widest
 * reaches (REACH) just meet, and the box widens to hold them; if that box would not fit the room,
 * every figure shrinks together until it does. `aside` (units) keeps a place on the rail right of
 * two or more for an instrument (the replay's night). More than three is not a case the game makes.
 */
export function standSet(
  cast: readonly Character[],
  g: StageGeometry,
  side = false,
  aside = 0,
): StandSet {
  const n = cast.length;
  const standW = standBox(g).w;
  let scale = (n <= 1 ? 1 : n === 2 ? 0.78 : n === 3 ? 0.6 : 1.8 / n) * (side ? 0.84 : 1);
  if (n <= 1) return { scale, offsets: [0], widen: 1 };
  // the group's span in body heights, and each centre's place along it
  const at: number[] = [];
  let run = 0;
  cast.forEach((c, i) => {
    run += i === 0 ? REACH[c].left : REACH[cast[i - 1]].right + REACH[c].left;
    at.push(run);
  });
  const span = run + REACH[cast[n - 1]].right;
  const body = g.ph * 0.98;
  const room = (g.room - 2 * AIR) * FILL;
  if (span * body * scale + aside > room) scale = (room - aside) / (span * body);
  const unit = body * scale,
    total = span * unit + aside;
  return {
    scale,
    offsets: at.map((x) => (x * unit - total / 2) / g.pwid),
    widen: Math.max(1, total / (standW * FILL)),
    ...(aside ? { beside: (total / 2 - aside / 2) / g.pwid } : {}),
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

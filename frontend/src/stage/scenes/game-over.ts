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
import {
  factionOf,
  isPackRole,
  ROLE_NAME,
  seatNumber,
  winnerKey,
  type Faction,
  type WinnerKey,
} from '../roles';
import { standBox, type StageGeometry } from '../units';

export type EndedAt = 'morning' | 'lynch';

/**
 * The hour the shutter rises on for each winner: the town's day, the wolves' night, the lone
 * killer's dusk (the serial killer's or the necromancer's), and for a draw, which nobody won, a
 * grey dawn.
 */
export const WINNERS_HOUR: Record<WinnerKey, Phase> = {
  villagers: 'day',
  wolves: 'night',
  serial_killer: 'dusk',
  necromancer: 'dusk',
  draw: 'dawn',
};

export const WINNER_LINE: Record<WinnerKey, string> = {
  villagers: 'The town has won',
  wolves: 'The wolves have won',
  serial_killer: 'The serial killer has won',
  necromancer: 'The necromancer has won',
  draw: 'No side has won',
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
 * seated human's own card. A wolf's pack mates have no role here (the wire lists the pack's
 * seats, never a mate's role): `knownSide` has them.
 */
export function knownRole(view: GameView, seat: string): string | null {
  if (view.xray.roles[seat]) return view.xray.roles[seat];
  if (seat === view.me.seat && view.me.role) return view.me.role.role;
  return null;
}

/** A seat's side as far as this viewer knows it: its known role's, or the pack's for a mate. */
export function knownSide(view: GameView, seat: string): Faction | null {
  const role = knownRole(view, seat);
  if (role) return factionOf(role);
  if (view.packRoster.includes(seat) && isPackRole(view.me.role?.role)) return 'wolves';
  return null;
}

/**
 * Whether a role won: the town's and the pack's by side, a lone killer by its own role (the
 * serial killer's win is not the necromancer's), nobody in a draw. A neutral (the speculator,
 * the fortune teller) wins or loses on its own result beside the winner (`neutral_result`,
 * "won", "won (2 points)", "lost").
 */
export function roleWon(
  role: string | null,
  winner: WinnerKey,
  neutralResult: string | null = null,
): boolean {
  const side = factionOf(role);
  if (side === 'neutral_benign') return !!neutralResult?.startsWith('won');
  if (winner === 'draw' || !role) return false;
  if (winner === 'villagers' || winner === 'wolves') return side === winner;
  return role === winner;
}

/** The winners' survivors, in seat order: the ones who take the stand. A draw has none. */
export function winnersOf(view: GameView): string[] {
  if (!view.over) return [];
  const winner = winnerKey(view.winner);
  if (winner === 'draw') return [];
  return view.seats.filter((s) => {
    if (!view.alive.includes(s)) return false;
    const role = knownRole(view, s);
    // a neutral never takes the stand: its result is the line under the winner's
    if (role) return factionOf(role) !== 'neutral_benign' && roleWon(role, winner);
    // a pack mate, known by side only
    return winner === 'wolves' && knownSide(view, s) === 'wolves';
  });
}

/**
 * How each neutral's result reads under the winner line; `{the}` is "The" and the role's name
 * as the game writes it (`ROLE_NAME`, "The fortune teller"), `{n}` the points, when given.
 * These lines are the client's own; the engine's (the pick at dawn) are left as it writes them.
 */
const NEUTRAL_WORDS: Record<string, { won: string; lost: string }> = {
  speculator: { won: '{the}’s pick won', lost: '{the} lost' },
  fortune_teller: { won: '{the} won, with {n}', lost: '{the} lost, with {n}' },
};

/**
 * The neutral's result as the second line under the winner's: "The speculator’s pick won",
 * "The fortune teller won, with 2 points", "The speculator lost". The neutral is the lineup's
 * (the cast counts' in a game without one); null when none was dealt or the engine gave no
 * result (every nine-seat game).
 */
export function neutralLine(
  view: Pick<GameView, 'neutralResult' | 'lineup' | 'castRoleCounts'>,
): string | null {
  const result = view.neutralResult?.trim();
  if (!result) return null;
  const role = [...view.lineup, ...Object.keys(view.castRoleCounts)].find(
    (r) => factionOf(r) === 'neutral_benign',
  );
  const words = role ? NEUTRAL_WORDS[role] : undefined;
  if (!role || !words) return `The neutral ${result}`;
  const won = result.startsWith('won');
  const points = /\((\d+) points?\)/.exec(result)?.[1];
  const the = `The ${(ROLE_NAME[role] ?? role).toLowerCase()}`;
  const line = (won ? words.won : words.lost).replace('{the}', the);
  if (line.includes('{n}'))
    return points !== undefined
      ? line.replace('{n}', `${points} ${points === '1' ? 'point' : 'points'}`)
      : line.replace(/, with \{n\}$/, '');
  return line;
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
  sigilist: 'a sigil',
  reanimated_wolves: 'a reanimated wolf',
  reanimated_vigilante: 'a reanimated vigilante',
  reanimated_sigilist: 'a reanimated sigil',
};

/** How a seat went: "survived", "day 3, voted out", "night 4, the wolves". */
export function fateOf(view: GameView, seat: string): string {
  const d = view.dead.find((x) => x.player === seat);
  if (!d) return 'survived';
  if (d.causes.includes('lynch')) return `day ${d.day}, voted out`;
  return `night ${d.day}, ${d.causes.map((c) => BY[c] ?? c).join(' and ')}`;
}

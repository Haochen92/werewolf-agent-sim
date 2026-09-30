/**
 * The role set as the stage names and colours it. The wire only ever says `wolf` or
 * `serial_killer`; the stage says "Wolf" and colours it by the side it plays for. Faction
 * colour is the card-back rule's business (stage_architecture.md §4): it appears only where
 * the role is known to this viewer, so these helpers are handed a role, never guess one.
 */
import type { MeView } from '@/game/types';

export type Faction = 'villagers' | 'wolves' | 'serial_killer';

export const ROLE_NAME: Record<string, string> = {
  villager: 'Villager',
  healer: 'Healer',
  investigator: 'Investigator',
  vigilante: 'Vigilante',
  wolf: 'Wolf',
  serial_killer: 'Serial killer',
};

const FACTION: Record<string, Faction> = {
  villager: 'villagers',
  healer: 'villagers',
  investigator: 'villagers',
  vigilante: 'villagers',
  wolf: 'wolves',
  serial_killer: 'serial_killer',
};

/** The side a role plays for; null for a role the stage does not know. */
export function factionOf(role: string | null | undefined): Faction | null {
  return (role && FACTION[role]) || null;
}

/** `player_7` → 7. The wire's seats are `player_1..player_9`; the stage shows the numeral. */
export function seatNumber(seat: string): number {
  const n = Number(seat.replace(/^player_/, ''));
  return Number.isFinite(n) ? n : 0;
}

/** The agents write `player_2` (or "Player 2"); the table reads "seat 2". */
export function seatify(text: string): string {
  return text
    .replace(/\bplayer[_ ](\d+)/g, 'seat $1')
    .replace(/\bPlayer[_ ](\d+)/g, 'Seat $1');
}

/** A role this seat already knows on another living seat: a pack mate's, or one it has read. */
export interface KnownRole {
  role: string;
  /** `pack`: a wolf's pack mate, from its card; `seen`: named by its own investigation. */
  how: 'pack' | 'seen';
}

/**
 * What a seat already knows of the others, from its own view only (the card it was dealt and
 * the results sent to it), never the X-ray's: a spectator knows nothing here. The wing shows
 * it as the card's band ("Your pack", "Seen · Wolf").
 */
export function knownRoles(
  me: string | null,
  mine: Pick<MeView, 'role' | 'privateResults'>,
): Map<string, KnownRole> {
  const known = new Map<string, KnownRole>();
  if (!me) return known;
  for (const r of mine.privateResults)
    if (r.kind === 'investigation' && r.player === me && r.target !== me)
      known.set(r.target, { role: r.role, how: 'seen' });
  for (const p of mine.role?.pack ?? [])
    if (p !== me) known.set(p, { role: 'wolf', how: 'pack' });
  return known;
}

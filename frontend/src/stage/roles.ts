/**
 * The role set as the stage names and colours it. The wire only ever says `wolf` or
 * `serial_killer`; the stage says "Wolf" and colours it by the side it plays for. Faction
 * colour is the card-back rule's business (stage_architecture.md §4): it appears only where
 * the role is known to this viewer, so these helpers are handed a role, never guess one.
 *
 * The eight 1920s roles (the owner's sigil set, 2026-10-07) are named and sided here ahead of
 * the engine, which does not deal them yet; their ids are the engine's style (`fortune_teller`
 * like `serial_killer`) and will follow the engine's word when it lands.
 */
import type { MeView } from '@/game/types';

/**
 * The four sides. The first three are the wire's winners; `serial_killer` is also the
 * neutral-evil side as a whole (the necromancer, when it lands, plays for itself the same way).
 * `neutral_benign` (the speculator, the fortune teller) has no engine winner yet.
 */
export type Faction = 'villagers' | 'wolves' | 'serial_killer' | 'neutral_benign';

export const ROLE_NAME: Record<string, string> = {
  villager: 'Villager',
  healer: 'Healer',
  investigator: 'Investigator',
  vigilante: 'Vigilante',
  sentinel: 'Sentinel',
  trailseer: 'Trailseer',
  sigilist: 'Sigilist',
  wolf: 'Wolf',
  chanteuse: 'Chanteuse',
  illusionist: 'Illusionist',
  serial_killer: 'Serial killer',
  necromancer: 'Necromancer',
  speculator: 'Speculator',
  fortune_teller: 'Fortune teller',
};

/** The side's name, as the table says it. */
export const FACTION_NAME: Record<Faction, string> = {
  villagers: 'Villagers',
  wolves: 'Wolves',
  serial_killer: 'Serial killer',
  neutral_benign: 'Neutral',
};

const FACTION: Record<string, Faction> = {
  villager: 'villagers',
  healer: 'villagers',
  investigator: 'villagers',
  vigilante: 'villagers',
  sentinel: 'villagers',
  trailseer: 'villagers',
  sigilist: 'villagers',
  wolf: 'wolves',
  chanteuse: 'wolves',
  illusionist: 'wolves',
  serial_killer: 'serial_killer',
  necromancer: 'serial_killer',
  speculator: 'neutral_benign',
  fortune_teller: 'neutral_benign',
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

/**
 * The agents write `player_2` (or "Player 2"); the table reads "seat 2", capitalised where it
 * starts a sentence (the moderator's "player_4 gets a last word." after a full stop, 2026-10-07).
 */
export function seatify(text: string): string {
  return text
    .replace(/\bplayer[_ ](\d+)/g, 'seat $1')
    .replace(/\bPlayer[_ ](\d+)/g, 'Seat $1')
    .replace(/(^|[.!?]\s+)seat (\d+)/g, '$1Seat $2');
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

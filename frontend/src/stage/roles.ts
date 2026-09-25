/**
 * The role set as the stage names and colours it. The wire only ever says `wolf` or
 * `serial_killer`; the stage says "Wolf" and colours it by the side it plays for. Faction
 * colour is the card-back rule's business (stage_architecture.md §4): it appears only where
 * the role is known to this viewer, so these helpers are handed a role, never guess one.
 */
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

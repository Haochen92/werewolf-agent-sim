/**
 * The role set as the stage names and colours it. The wire only ever says `wolf` or
 * `serial_killer`; the stage says "Wolf" and colours it by the side it plays for. Faction
 * colour is the card-back rule's business (stage_architecture.md §4): it appears only where
 * the role is known to this viewer, so these helpers are handed a role, never guess one.
 *
 * The eight 1920s roles (the owner's sigil set, 2026-10-07) are named and sided here ahead of
 * the engine, which does not deal them yet; their ids are the engine's style (`fortune_teller`
 * like `serial_killer`) and will follow the engine's word when it lands.
 *
 * The necromancer has landed as a wire winner of its own, under the neutral-evil side's colour;
 * a null winner is a draw (the last wolf and the last town player killing each other, or a tie
 * at the day cap), which no side wins.
 */
import type { MeView } from '@/game/types';
import type { Winner } from '@/types/contracts';

/**
 * The four sides. The first three are the wire's winners; `serial_killer` is also the
 * neutral-evil side as a whole (the necromancer plays for itself the same way).
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

/**
 * The roles in the role sheet's order (the pool, `Agents/schemas/roles.py`), with the nine-seat
 * archives' villager and wolf at the head of their sides. The cast plate and the notebook's role
 * list read in this order.
 */
export const ROLE_ORDER: readonly string[] = [
  'villager',
  'investigator',
  'sentinel',
  'trailseer',
  'vigilante',
  'sigilist',
  'healer',
  'wolf',
  'chanteuse',
  'illusionist',
  'serial_killer',
  'necromancer',
  'speculator',
  'fortune_teller',
];

/** A role's plural, in lower case: "serial killers", "wolves". */
export const ROLE_PLURAL: Record<string, string> = {
  villager: 'villagers',
  investigator: 'investigators',
  sentinel: 'sentinels',
  trailseer: 'trailseers',
  vigilante: 'vigilantes',
  sigilist: 'sigilists',
  healer: 'healers',
  wolf: 'wolves',
  chanteuse: 'chanteuses',
  illusionist: 'illusionists',
  serial_killer: 'serial killers',
  necromancer: 'necromancers',
  speculator: 'speculators',
  fortune_teller: 'fortune tellers',
};

/**
 * The side's name, as the table says it. The `serial_killer` side is the lone killer's (the
 * role sheet's word: the serial killer or the necromancer, whichever was dealt); a winner keeps
 * its role's name (`WINNER_NAME`).
 */
export const FACTION_NAME: Record<Faction, string> = {
  villagers: 'Town',
  wolves: 'Wolves',
  serial_killer: 'Lone killer',
  neutral_benign: 'Neutral',
};

/** A winner as a record key: the wire's four, or `draw` for a game no side won. */
export type WinnerKey = NonNullable<Winner> | 'draw';

export const winnerKey = (winner: Winner): WinnerKey => winner ?? 'draw';

/** Who won, as the table says it. A draw has no winner; it is `DRAW_NAME`. */
export const WINNER_NAME: Record<NonNullable<Winner>, string> = {
  villagers: 'Town',
  wolves: 'Wolves',
  serial_killer: 'Serial killer',
  necromancer: 'Necromancer',
};

export const DRAW_NAME = 'Draw';

const WINNER_FACTION: Record<WinnerKey, Faction | null> = {
  villagers: 'villagers',
  wolves: 'wolves',
  serial_killer: 'serial_killer',
  necromancer: 'serial_killer',
  draw: null,
};

/** The side whose colour a winner wears; null for a draw, which wears none. */
export function winnerFaction(winner: Winner | WinnerKey): Faction | null {
  return winner ? WINNER_FACTION[winner] : null;
}

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

/**
 * The pack is a role set, not a role (ten-seat pass §1): every pack role shares the wolves'
 * chat, kill and room. Nine-seat games deal plain `wolf` only.
 */
export const PACK_ROLES = ['wolf', 'chanteuse', 'illusionist'] as const;

export function isPackRole(role: string | null | undefined): boolean {
  return !!role && (PACK_ROLES as readonly string[]).includes(role);
}

/** The lone killer seat: one of the two is dealt, and it plays for itself. */
export const LONE_KILLER_ROLES = ['serial_killer', 'necromancer'] as const;

export function isLoneKiller(role: string | null | undefined): boolean {
  return !!role && (LONE_KILLER_ROLES as readonly string[]).includes(role);
}

/** The neutral seat: one of the two is dealt, and it wins or loses beside the winner. */
export const NEUTRAL_ROLES = ['speculator', 'fortune_teller'] as const;

export type NeutralRole = (typeof NEUTRAL_ROLES)[number];

/**
 * The game's neutral if it won, from the roles dealt and its result (`won`, `won (2 points)`);
 * null when it lost, or in a nine-seat game, which dealt none.
 */
export function neutralWinner(
  castRoleCounts: Record<string, number>,
  neutralResult: string | null | undefined,
): NeutralRole | null {
  if (!neutralResult?.startsWith('won')) return null;
  return NEUTRAL_ROLES.find((role) => castRoleCounts[role]) ?? null;
}

/**
 * The roles with a night of their own, each a turn that ticks the night's pace once; the pack's
 * turn is one more (server/game/pacing.py `_SOLO_NIGHT_ROLES`).
 */
export const SOLO_NIGHT_ROLES = [
  'healer',
  'investigator',
  'sentinel',
  'trailseer',
  'vigilante',
  'sigilist',
  'serial_killer',
  'necromancer',
  'speculator',
  'fortune_teller',
] as const;

export function isSoloNightRole(role: string | null | undefined): boolean {
  return !!role && (SOLO_NIGHT_ROLES as readonly string[]).includes(role);
}

/**
 * The roles whose body gives the necromancer an ability, mirroring the engine's table
 * (`Agents/schemas/roles.py` `BORROWED_ABILITY`; `Agents/rules/night.py` `usable_bodies`): a
 * pack body attacks or blocks, a town body gives its own ability. A lone killer's, a neutral's,
 * a plain villager's or a plain wolf's body gives nothing, and nor does a concealed one.
 */
export const BORROWED_ROLES = [
  'illusionist',
  'chanteuse',
  'vigilante',
  'healer',
  'sigilist',
  'investigator',
  'sentinel',
  'trailseer',
] as const;

/** The dead a necromancer may act through tonight: revealed, with an ability to give. */
export function usableBodies(
  dead: readonly { player: string; role: string | null }[],
): string[] {
  return dead
    .filter((d) => !!d.role && (BORROWED_ROLES as readonly string[]).includes(d.role))
    .map((d) => d.player);
}

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
 * Seats in seat order, then whatever is not a seat (abstain, a no-action word, a side) as it
 * came. The server's roster sorts its ids as text (`player_10` before `player_2`), so the fold
 * puts every list of seats it keeps through here.
 */
export function inSeatOrder(list: readonly string[]): string[] {
  const isSeat = (s: string) => /^player_\d+$/.test(s);
  return [
    ...list.filter(isSeat).sort((a, b) => seatNumber(a) - seatNumber(b)),
    ...list.filter((s) => !isSeat(s)),
  ];
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

/**
 * What this seat already knows of another living seat. `pack`: a pack mate, from its card — the
 * deal lists the pack's seats, not their roles, so a mate has none here. `seen`: a role named
 * by its own investigation.
 */
export type KnownRole = { how: 'pack' } | { how: 'seen'; role: string };

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
  for (const p of mine.role?.pack ?? []) if (p !== me) known.set(p, { how: 'pack' });
  return known;
}

/**
 * The roles of concealed bodies this seat was told: the pack's record names the role the
 * illusionist hid, for every wolf (owner, 2026-10-17). The wing shows it on the dead seat's card.
 */
export function hiddenRolesHeld(
  me: string | null,
  mine: Pick<MeView, 'privateResults'>,
): Map<string, string> {
  const held = new Map<string, string>();
  if (!me) return held;
  for (const r of mine.privateResults)
    if (
      r.kind === 'night_record' &&
      r.player === me &&
      r.actor === 'wolves' &&
      r.target &&
      r.seen.length
    )
      held.set(r.target, r.seen[0]);
  return held;
}

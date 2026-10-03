/**
 * Which character plays which seat.
 *
 * Since 2026-10-03 the server draws the cast when the engine deals the seats and records it
 * with the game (the status snapshot's and the replay's `cast`, in seat order), so a player's
 * pick holds and a replay shows the same puppets the live game did. `resolveCast` takes that
 * record when it is whole, and otherwise falls back to the way every earlier game was cast:
 * a hash of the game id shuffling the eleven characters of that day. That list is frozen
 * here on purpose, apart from the manifest's growing one, because reordering or extending
 * it would recast every game recorded before casts were stored. Ported unchanged from the
 * design bundle's puppet kit: the same id must give the same cast here as in the benches.
 *
 * Both return nine characters; index 0 is seat 1 (`player_1`).
 */
import { CHARACTERS, type Character } from '@/assets/manifest';

/** The cast pool as it was before the server stored casts. Never reorder or extend. */
export const LEGACY_CHARACTERS: readonly Character[] = [
  'owl',
  'hare',
  'cat',
  'badger',
  'cyclops',
  'threeEyes',
  'dragon',
  'onion',
  'whale',
  'polarBear',
  'shade',
];

/**
 * The cast the server recorded, when it recorded one this build can show (nine ids the
 * manifest knows); otherwise the legacy hash. A game that predates stored casts sends an
 * empty list; a game cast with a character this build has no sprites for falls back too,
 * rather than leaving a seat blank.
 */
export function resolveCast(
  stored: readonly string[] | null | undefined,
  gameId: string,
  seats = 9,
): Character[] {
  if (stored && stored.length === seats && stored.every(isCharacter)) {
    return [...stored];
  }
  return castForGame(gameId, seats);
}

/**
 * The platform's cast while a room waits, by place on the roster (`picks` lines up with it).
 * Whoever picked a puppet this build can show wears it; everyone else keeps their place's
 * puppet from the hash, unless a pick took it, and then the next puppet nobody wears stands in.
 */
export function castForRoom(
  picks: readonly (string | null)[],
  gameId: string,
  seats = 9,
): Character[] {
  const drawn = castForGame(gameId, LEGACY_CHARACTERS.length);
  const chosen = drawn
    .slice(0, seats)
    .map((_, i) => (picks[i] && isCharacter(picks[i]) ? picks[i] : null));
  const worn = new Set(chosen.filter((c) => c !== null));
  const kept = chosen.map((c, i) => c ?? (worn.has(drawn[i]) ? null : drawn[i]));
  const spare = drawn.filter((c) => !kept.includes(c));
  return kept.map((c) => c ?? spare.shift()!);
}

/** A character this build has sprites for (the catalogue may list ones it does not yet). */
export function isCharacter(id: string): id is Character {
  return (CHARACTERS as readonly string[]).includes(id);
}

export function castForGame(gameId: string, seats = 9): Character[] {
  // FNV-1a over the id's UTF-16 code units, then a mulberry32 stream for a Fisher–Yates shuffle.
  let h = 2166136261;
  for (let i = 0; i < gameId.length; i++) {
    h ^= gameId.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  let s = h >>> 0;
  const rnd = () => {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const pool: Character[] = LEGACY_CHARACTERS.slice();
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool.slice(0, seats);
}

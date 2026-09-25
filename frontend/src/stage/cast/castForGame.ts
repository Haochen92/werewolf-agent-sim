/**
 * Which character plays which seat. The cast is drawn from a hash of the game id, so a
 * replay shows the same puppets as the live game did, without the server having to send
 * anything. Ported unchanged from the design bundle's puppet kit: the same id must give the
 * same cast here as it did in the benches.
 *
 * Returns nine of the eleven characters; index 0 is seat 1 (`player_1`).
 */
import { CHARACTERS, type Character } from '@/assets/manifest';

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
  const pool: Character[] = CHARACTERS.slice();
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool.slice(0, seats);
}

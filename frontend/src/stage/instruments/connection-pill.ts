/**
 * What the connection pill under the top strip says (owner, 2026-10-17, board 3): while the
 * stream reconnects, that it does and whether anything runs meanwhile; once it has been down
 * past a blip (`BLIP_MS`) or the browser says it is offline, that the page is offline, with
 * "Try now". Nothing while the stream is up, or while the page has none (a waiting room).
 */
import type { ConnectionState } from '@/game/store';

export type PillState = 'reconnecting' | 'offline';

/**
 * Whose page it is, for what runs while it is away: a seat in a game for one (no clocks: the
 * game waits), a seat in a room (its clock runs on the server), or a watcher (neither).
 */
export type PillTable = 'solo' | 'room' | 'watching';

export function pillState(
  connection: ConnectionState,
  online: boolean,
  /** Down past a blip. */
  long: boolean,
): PillState | null {
  // no stream to lose (a waiting room, a page leaving): nothing to say
  if (connection === 'idle') return null;
  if (!online) return 'offline';
  if (connection !== 'reconnecting') return null;
  return long ? 'offline' : 'reconnecting';
}

export function pillLine(state: PillState, table: PillTable): string {
  if (state === 'reconnecting')
    return table === 'solo'
      ? 'Reconnecting… the game waits for you'
      : table === 'room'
        ? 'Reconnecting… your seat’s clock is running'
        : 'Reconnecting…';
  return table === 'solo'
    ? 'You’re offline. The game waits.'
    : table === 'room'
      ? 'You’re offline. Your seat’s clock is running.'
      : 'You’re offline.';
}

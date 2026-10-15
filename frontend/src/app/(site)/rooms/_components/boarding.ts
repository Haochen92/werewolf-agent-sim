/**
 * What a row of the departures board says about one room, worked out from its `RoomSummary`.
 *
 * A room is boarding (anyone may join), locked, or full. When a room is both locked and full it
 * reads as locked, because the server checks the lock first and refuses with the lock's words
 * (`server/game/lobby.py`, `Room.join`). A locked room admits nobody, invite link included, until
 * its host unlocks it (review §F6).
 */
import type { RoomSummary } from '@/types/contracts';

export type BoardingState = 'boarding' | 'locked' | 'full';

export interface RowFace {
  state: BoardingState;
  /** The status on the split-flap tiles. */
  flap: 'BOARDING' | 'LOCKED' | 'FULL';
  /** `hot` lights the tiles amber; a room nobody can board is dimmed. */
  tone: 'hot' | 'dim';
  joinable: boolean;
  /** Why the Board button is off, or null while it is on. */
  reason: string | null;
}

export const LOCKED_REASON = 'Locked — ask the host to unlock it.';
export const FULL_REASON = 'Full — every place at this table is taken.';

export function rowFace(
  room: Pick<RoomSummary, 'locked' | 'players' | 'max_seats'>,
): RowFace {
  if (room.locked) {
    return {
      state: 'locked',
      flap: 'LOCKED',
      tone: 'dim',
      joinable: false,
      reason: LOCKED_REASON,
    };
  }
  if (room.players.length >= room.max_seats) {
    return {
      state: 'full',
      flap: 'FULL',
      tone: 'dim',
      joinable: false,
      reason: FULL_REASON,
    };
  }
  return { state: 'boarding', flap: 'BOARDING', tone: 'hot', joinable: true, reason: null };
}

/** "3 of 9 aboard, 6 places open"; "9 of 9 aboard" once nobody else fits. */
export function aboardLine(aboard: number, places: number): string {
  const open = Math.max(places - aboard, 0);
  const head = `${aboard} of ${places} aboard`;
  if (open === 0) return head;
  return `${head}, ${open} ${open === 1 ? 'place' : 'places'} open`;
}

/** The host's name, or a dash while the room is empty (the first seat stands in for the host). */
export function hostName(room: Pick<RoomSummary, 'host'>): string {
  return room.host?.trim() || '—';
}

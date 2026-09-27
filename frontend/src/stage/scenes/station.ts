/**
 * The waiting room's rules, the pure half (beat sheet §1a): which beat the platform is on, what
 * the ledge says, whether the host may depart, and how long the departure and the curtain take.
 * `StationScene` draws from these; `LiveTheatre` times the hand-off to the deal with them.
 */
import { BEAT_LABELS, type SceneBeat } from '../beats/types';
import type { RoomInput } from './types';

/**
 * The fewest aboard that Depart needs. The server sets no minimum (a room with nobody aboard
 * starts as a game of agents only: `GameLobby.run_config` asks for `len(seats)` humans); this is
 * the client's rule, kept from the old lobby card (its Start was off below one player): a room
 * nobody has boarded has nobody to play it, and an all-agent game has its own door (`/play`).
 */
export const MIN_ABOARD = 1;

/**
 * The departure at normal speed, in seconds (scaled by the motion speed like every other beat):
 * the people step aboard and the blinds come down on the agents' places, then the train pulls
 * out. `total` is when the platform is empty; the container drops the curtain after it.
 */
export const DEPART = { pullAt: 2.4, pull: 4.6, total: 7.0 } as const;

/** The curtain between the platform and the deal: falling, then lifting off the deal's first beat. */
export const CURTAIN = { close: 1.2, open: 1.0 } as const;

export type StationBeatId = 'station.waiting' | 'station.locked' | 'station.departing';

/** The beat the room is on: departing once the host has pressed (or the game has begun). */
export function stationBeatId(
  room: Pick<RoomInput, 'locked'>,
  departing: boolean,
): StationBeatId {
  if (departing) return 'station.departing';
  return room.locked ? 'station.locked' : 'station.waiting';
}

/**
 * A platform beat as the stage takes it. Nothing on the wire anchors it (a room has no log), so
 * `seq` and `end` are 0 and it holds until the room changes (`holdMs` 0).
 */
export function stationBeat(id: StationBeatId): SceneBeat {
  return {
    id,
    scene: 'station',
    label: BEAT_LABELS[id],
    day: 0,
    seq: 0,
    end: 0,
    sees: 'public',
    holdMs: 0,
    liveOnly: true,
  };
}

/** Why Depart is off for the host, in the words the ledge shows; null when it may be pressed. */
export function departBlock(room: Pick<RoomInput, 'aboard' | 'minAboard'>): string | null {
  if (room.aboard.length >= room.minAboard) return null;
  return room.minAboard === 1
    ? 'Nobody is aboard yet: Depart needs one person on the platform.'
    : `Depart needs ${room.minAboard} people on the platform.`;
}

/** The host may press Depart now: the key is here, enough are aboard, nothing is on its way. */
export function canDepart(
  room: Pick<RoomInput, 'isHost' | 'aboard' | 'minAboard' | 'busy'>,
): boolean {
  return room.isHost && !room.busy && departBlock(room) === null;
}

/**
 * The ledge's notice: the headline ("3 of 9 aboard · waiting for the host") and the line under
 * it, for this viewer (the host, a guest aboard, or someone watching).
 */
export function ledgeLine(
  room: RoomInput,
  departing = false,
): { head: string; sub: string } {
  if (departing)
    return { head: 'All aboard', sub: 'The cards are dealt in the dining car.' };
  const n = room.aboard.length;
  const open = Math.max(room.places - n, 0);
  const head = `${n} of ${room.places} aboard · ${room.isHost ? 'ready when you are' : 'waiting for the host'}`;
  // short enough for one line on a phone: the sign's plate says what locked means, and the
  // name tag and the wing say which one is you
  const lock = room.locked ? 'Locked. ' : '';
  let sub: string;
  if (room.isHost) {
    sub =
      departBlock(room) ??
      (open === 0
        ? 'Every place has a person in it.'
        : `Depart now and agents take the ${open === 1 ? 'empty place' : `${open} empty places`}.`);
  } else if (room.seated) {
    sub = 'Seats and roles are dealt when the train departs.';
  } else {
    sub =
      open === 0
        ? 'Every place is taken; you are watching.'
        : 'You are watching. The game plays here once the train departs.';
  }
  return { head, sub: lock + sub };
}

import { describe, expect, it } from 'vitest';
import {
  MIN_ABOARD,
  canDepart,
  departBlock,
  ledgeLine,
  stationBeat,
  stationBeatId,
} from './station';
import type { RoomInput } from './types';

const room = (over: Partial<RoomInput> = {}): RoomInput => ({
  name: 'Night shift',
  aboard: ['mira', 'kei', 'sol'],
  places: 9,
  host: 'mira',
  locked: false,
  isHost: false,
  seated: false,
  you: null,
  minAboard: MIN_ABOARD,
  link: 'https://example.test/games/x',
  ...over,
});

describe('the platform’s beat', () => {
  it('is waiting, locked, or departing', () => {
    expect(stationBeatId(room(), false)).toBe('station.waiting');
    expect(stationBeatId(room({ locked: true }), false)).toBe('station.locked');
    expect(stationBeatId(room({ locked: true }), true)).toBe('station.departing');
  });

  it('is a live-only beat of the station scene that holds until the room changes', () => {
    expect(stationBeat('station.locked')).toMatchObject({
      scene: 'station',
      label: 'The room is locked',
      holdMs: 0,
      liveOnly: true,
      sees: 'public',
    });
  });
});

describe('Depart', () => {
  it('needs one aboard, and says so', () => {
    expect(MIN_ABOARD).toBe(1);
    expect(departBlock(room({ aboard: [] }))).toBe(
      'Nobody is aboard yet: Depart needs one person on the platform.',
    );
    expect(departBlock(room({ aboard: ['mira'] }))).toBeNull();
    expect(departBlock(room({ aboard: ['a'], minAboard: 2 }))).toBe(
      'Depart needs 2 people on the platform.',
    );
  });

  it('is the host’s alone, and not while a press is on its way', () => {
    expect(canDepart(room({ isHost: true }))).toBe(true);
    expect(canDepart(room())).toBe(false);
    expect(canDepart(room({ isHost: true, aboard: [] }))).toBe(false);
    expect(canDepart(room({ isHost: true, busy: 'lock' }))).toBe(false);
  });
});

describe('the ledge’s notice', () => {
  it('tells a guest how many are aboard and who they wait for', () => {
    expect(ledgeLine(room({ seated: true, you: 2 }))).toEqual({
      head: '3 of 9 aboard · waiting for the host',
      sub: 'Seats and roles are dealt when the train departs.',
    });
  });

  it('tells the host what Depart does, or why it cannot yet', () => {
    expect(ledgeLine(room({ isHost: true }))).toEqual({
      head: '3 of 9 aboard · ready when you are',
      sub: 'Depart now and agents take the 6 empty places.',
    });
    const eight = room({
      isHost: true,
      aboard: Array.from({ length: 8 }, (_, i) => `p${i}`),
    });
    expect(ledgeLine(eight).sub).toBe('Depart now and agents take the empty place.');
    const nine = room({
      isHost: true,
      aboard: Array.from({ length: 9 }, (_, i) => `p${i}`),
    });
    expect(ledgeLine(nine).sub).toBe('Every place has a person in it.');
    expect(ledgeLine(room({ isHost: true, aboard: [] })).sub).toBe(
      departBlock(room({ aboard: [] })),
    );
  });

  it('tells a watcher they are watching, and everyone that the room is locked', () => {
    expect(ledgeLine(room()).sub).toBe(
      'You are watching. The game plays here once the train departs.',
    );
    const full = room({ aboard: Array.from({ length: 9 }, (_, i) => `p${i}`) });
    expect(ledgeLine(full)).toEqual({
      head: '9 of 9 aboard · waiting for the host',
      sub: 'Every place is taken; you are watching.',
    });
    expect(ledgeLine(room({ locked: true })).sub).toMatch(/^Locked\. /);
  });

  it('says all aboard once the train is leaving', () => {
    expect(ledgeLine(room({ isHost: true }), true)).toEqual({
      head: 'All aboard',
      sub: 'The cards are dealt in the dining car.',
    });
  });
});

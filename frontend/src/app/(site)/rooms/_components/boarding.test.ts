import { describe, expect, it } from 'vitest';
import { FULL_REASON, LOCKED_REASON, aboardLine, hostName, rowFace } from './boarding';

const room = (players: number, locked = false) => ({
  players: Array.from({ length: players }, (_, i) => `p${i}`),
  max_seats: 9,
  locked,
});

describe('rowFace', () => {
  it('an open room with places left is boarding, and its Board button is on', () => {
    expect(rowFace(room(3))).toEqual({
      state: 'boarding',
      flap: 'BOARDING',
      tone: 'hot',
      joinable: true,
      reason: null,
    });
  });

  it('a locked room is off, with the server’s reason', () => {
    const face = rowFace(room(2, true));
    expect(face.state).toBe('locked');
    expect(face.joinable).toBe(false);
    expect(face.reason).toBe(LOCKED_REASON);
    expect(face.reason).toMatch(/ask the host to unlock it/);
  });

  it('a room with every place taken is full', () => {
    expect(rowFace(room(9))).toMatchObject({
      state: 'full',
      flap: 'FULL',
      tone: 'dim',
      joinable: false,
      reason: FULL_REASON,
    });
  });

  it('locked and full reads as locked, the server’s first refusal', () => {
    expect(rowFace(room(9, true)).state).toBe('locked');
  });
});

describe('aboardLine', () => {
  it('counts the places still open', () => {
    expect(aboardLine(3, 9)).toBe('3 of 9 aboard, 6 places open');
    expect(aboardLine(8, 9)).toBe('8 of 9 aboard, 1 place open');
    expect(aboardLine(0, 9)).toBe('0 of 9 aboard, 9 places open');
  });

  it('says only the count once the room is full', () => {
    expect(aboardLine(9, 9)).toBe('9 of 9 aboard');
  });
});

describe('hostName', () => {
  it('is the host, or a dash while the room is empty', () => {
    expect(hostName({ host: 'mira' })).toBe('mira');
    expect(hostName({ host: null })).toBe('—');
    expect(hostName({})).toBe('—');
    expect(hostName({ host: '  ' })).toBe('—');
  });
});

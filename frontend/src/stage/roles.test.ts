import { describe, expect, it } from 'vitest';
import { factionOf, seatNumber, seatify } from './roles';

describe('the stage’s role and seat words', () => {
  it('rewrites the agents’ seat names for the table', () => {
    expect(seatify('Player_2, calling it a pivot. player_6 and Player 8’s point')).toBe(
      'Seat 2, calling it a pivot. seat 6 and Seat 8’s point',
    );
  });
  it('reads seat numbers and factions', () => {
    expect(seatNumber('player_7')).toBe(7);
    expect(factionOf('healer')).toBe('villagers');
    expect(factionOf('serial_killer')).toBe('serial_killer');
    expect(factionOf('necromancer')).toBe('serial_killer');
    expect(factionOf('speculator')).toBe('neutral_benign');
    expect(factionOf(null)).toBeNull();
  });
});

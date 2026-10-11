import { describe, expect, it } from 'vitest';
import {
  factionOf,
  isLoneKiller,
  isPackRole,
  inSeatOrder,
  isSoloNightRole,
  seatNumber,
  seatify,
} from './roles';

describe('the stage’s role and seat words', () => {
  it('rewrites the agents’ seat names for the table', () => {
    expect(seatify('Player_2, calling it a pivot. player_6 and Player 8’s point')).toBe(
      // a seat that starts a sentence is capitalised (the moderator's line, 2026-10-07)
      'Seat 2, calling it a pivot. Seat 6 and Seat 8’s point',
    );
  });
  it('capitalises a seat that starts a sentence, and only there', () => {
    expect(seatify('player_4 gets a last word.')).toBe('Seat 4 gets a last word.');
    expect(
      seatify(
        'Before the vote: player_5 has been accused by player_2. player_5 gets a last word.',
      ),
    ).toBe('Before the vote: seat 5 has been accused by seat 2. Seat 5 gets a last word.');
    expect(seatify('Is it player_3? player_3 says no! player_3 left.')).toBe(
      'Is it seat 3? Seat 3 says no! Seat 3 left.',
    );
    // mid-sentence and after a comma or colon it stays lower case
    expect(seatify('I trust player_2, not player_7: player_7 lied.')).toBe(
      'I trust seat 2, not seat 7: seat 7 lied.',
    );
  });
  it('reads seat numbers and factions', () => {
    expect(seatNumber('player_7')).toBe(7);
    // seats by number, the words after them as they came
    expect(
      inSeatOrder(['player_1', 'player_10', 'abstain', 'player_2', 'hold_fire']),
    ).toEqual(['player_1', 'player_2', 'player_10', 'abstain', 'hold_fire']);
    expect(factionOf('healer')).toBe('villagers');
    expect(factionOf('serial_killer')).toBe('serial_killer');
    expect(factionOf('necromancer')).toBe('serial_killer');
    expect(factionOf('speculator')).toBe('neutral_benign');
    expect(factionOf(null)).toBeNull();
  });
});

describe('the role sets', () => {
  it('the pack is three roles, the lone killer two, and the solo night ten', () => {
    expect(['wolf', 'chanteuse', 'illusionist'].every(isPackRole)).toBe(true);
    expect(isPackRole('serial_killer')).toBe(false);
    expect(isPackRole(null)).toBe(false);
    expect(['serial_killer', 'necromancer'].every(isLoneKiller)).toBe(true);
    expect(isLoneKiller('wolf')).toBe(false);
    expect(isSoloNightRole('fortune_teller')).toBe(true);
    // the pack acts together, and a villager has no night
    expect(isSoloNightRole('chanteuse')).toBe(false);
    expect(isSoloNightRole('villager')).toBe(false);
  });
});

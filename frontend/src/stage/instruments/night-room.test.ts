import { describe, expect, it } from 'vitest';
import { countLeft, countText, URGENT_MS } from '../countdown';
import { LONE_WOLF_SEALED, plateLabel, sealedLabel } from '../scenes/ShelfRoomScene';
import { packEntries } from '../scenes/PackScene';
import type { NightView } from '@/game/types';

describe('the countdown on the plate', () => {
  it('reads m:ss, rounding up, and -:-- with no deadline', () => {
    expect(countText(120_000)).toBe('2:00');
    expect(countText(74_000)).toBe('1:14');
    expect(countText(9_001)).toBe('0:10');
    expect(countText(500)).toBe('0:01');
    expect(countText(0)).toBe('0:00');
    expect(countText(null)).toBe('-:--');
  });

  it('drains the bar with the time left, and has none without a deadline', () => {
    expect(countLeft({ totalMs: 120_000 }, 120_000)).toBe(1);
    expect(countLeft({ totalMs: 120_000 }, 30_000)).toBe(0.25);
    expect(countLeft({ totalMs: 120_000 }, -5)).toBe(0);
    expect(countLeft({ totalMs: 120_000 }, 180_000)).toBe(1);
    expect(countLeft(null, 1000)).toBeNull();
    expect(countLeft({ totalMs: 120_000 }, null)).toBeNull();
    expect(countLeft({ totalMs: 0 }, 1000)).toBeNull();
    expect(URGENT_MS).toBe(10_000);
  });
});

describe('the plate', () => {
  it('asks, then names the act', () => {
    expect(plateLabel('healer_target', null)).toBe('Choose a seat to protect');
    expect(plateLabel('healer_target', 'player_1')).toBe('Protect seat 1');
    expect(plateLabel('investigator_target', 'player_4')).toBe('Check seat 4');
    expect(plateLabel('vigilante_target', 'player_2')).toBe('Shoot seat 2');
    expect(plateLabel('serial_killer_target', 'player_5')).toBe('Kill seat 5');
  });
});

describe('the sealed plate', () => {
  it('says what was done tonight, one line per act', () => {
    expect(sealedLabel('healer_target', 'player_3')).toBe('Seat 3 is protected tonight');
    expect(sealedLabel('investigator_target', 'player_3')).toBe('You check seat 3 tonight');
    expect(sealedLabel('vigilante_target', 'player_3')).toBe('You shoot seat 3 tonight');
    expect(sealedLabel('vigilante_target', null)).toBe('You hold fire tonight');
    expect(sealedLabel('serial_killer_target', 'player_3')).toBe(
      'Seat 3 is marked tonight',
    );
    expect(sealedLabel('wolf_vote', 'player_4')).toBe('You vote seat 4 tonight');
    expect(LONE_WOLF_SEALED(4)).toBe('Seat 4 is your kill tonight');
    // a remount that lost the seat still says the act is in
    expect(sealedLabel('healer_target', undefined)).toBe('Your act is in');
  });
});

describe('the pack chat', () => {
  it('orders talk, votes and the decision, with the morning note after', () => {
    const night = {
      wolfChannel: [
        { seq: 33, round: 1, wolf: 'player_3', message: 'a' },
        { seq: 271, round: 2, wolf: 'game_master', message: 'failed' },
      ],
      wolfVotes: [
        { seq: 55, wolf: 'player_8', votee: 'player_1' },
        { seq: 54, wolf: 'player_3', votee: 'player_1' },
      ],
      wolfKill: 'player_1',
    } as unknown as NightView;
    expect(packEntries(night).map((e) => e.kind)).toEqual([
      'line',
      'vote',
      'vote',
      'decided',
      'gm',
    ]);
    expect(packEntries(null)).toEqual([]);
  });
});

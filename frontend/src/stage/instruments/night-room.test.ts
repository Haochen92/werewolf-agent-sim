import { describe, expect, it } from 'vitest';
import { countLeft, countText, URGENT_MS } from '../countdown';
import { plateLabel } from '../scenes/ShelfRoomScene';
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
    expect(countLeft({ remainingMs: 120_000, totalMs: 120_000 })).toBe(1);
    expect(countLeft({ remainingMs: 30_000, totalMs: 120_000 })).toBe(0.25);
    expect(countLeft({ remainingMs: -5, totalMs: 120_000 })).toBe(0);
    expect(countLeft(null)).toBeNull();
    expect(countLeft({ remainingMs: 1000, totalMs: 0 })).toBeNull();
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

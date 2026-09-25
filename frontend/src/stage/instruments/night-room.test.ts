import { describe, expect, it } from 'vitest';
import { clockHand, flapText } from './CarriageClock';
import { plateLabel } from '../scenes/ShelfRoomScene';
import { packEntries } from '../scenes/PackScene';
import type { NightView } from '@/game/types';

describe('the carriage clock', () => {
  it('points the hand at the time left, clockwise from twelve', () => {
    expect(clockHand(120_000, 120_000)).toEqual({ f: 1, deg: 360 });
    expect(clockHand(60_000, 120_000)).toEqual({ f: 0.5, deg: 180 });
    expect(clockHand(30_000, 120_000)).toEqual({ f: 0.25, deg: 90 });
    expect(clockHand(0, 120_000)).toEqual({ f: 0, deg: 0 });
    expect(clockHand(-5, 120_000)).toEqual({ f: 0, deg: 0 });
    expect(clockHand(74_000, 120_000)?.deg).toBeCloseTo(222);
  });

  it('has no hand without a deadline', () => {
    expect(clockHand(null, 120_000)).toBeNull();
    expect(clockHand(1000, null)).toBeNull();
  });

  it('reads the counter in m:ss, rounding up', () => {
    expect(flapText(120_000)).toBe('2:00');
    expect(flapText(74_000)).toBe('1:14');
    expect(flapText(9_001)).toBe('0:10');
    expect(flapText(500)).toBe('0:01');
    expect(flapText(0)).toBe('0:00');
    expect(flapText(null)).toBe('-:--');
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

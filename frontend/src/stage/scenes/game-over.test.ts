import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import type { GameView } from '@/game/types';
import { FIXTURE_EVENTS } from '../workbench/fixture';
import { endedAt, fateOf, lastStanding, standSet, winnersOf } from './game-over';

const over = FIXTURE_EVENTS.findIndex((e) => e.type === 'game_over') + 1;
const view = foldEvents(FIXTURE_EVENTS.slice(0, over));

describe('the ending, from the fixture (the wolves win at the morning of day 4)', () => {
  it('stands the winning side’s survivors only: seat 8, not the vigilante beside it', () => {
    expect(view.winner).toBe('wolves');
    expect(view.alive).toEqual(['player_7', 'player_8']);
    expect(winnersOf(view)).toEqual(['player_8']);
  });

  it('stands every survivor of the side, and none of the fallen', () => {
    const v: GameView = { ...view, winner: 'villagers' };
    expect(winnersOf(v)).toEqual(['player_7']);
    const all: GameView = {
      ...view,
      winner: 'villagers',
      alive: ['player_1', 'player_7', 'player_8', 'player_9'],
    };
    expect(winnersOf(all)).toEqual(['player_1', 'player_7', 'player_9']);
  });

  it('knows where it stopped', () => {
    expect(endedAt(view)).toBe('morning');
    const lynch = FIXTURE_EVENTS.findIndex((e) => e.type === 'lynch_result' && e.day === 4);
    expect(endedAt(foldEvents(FIXTURE_EVENTS.slice(0, lynch + 1)))).toBe('lynch');
  });

  it('says how each seat went', () => {
    expect(fateOf(view, 'player_8')).toBe('survived');
    expect(fateOf(view, 'player_2')).toBe('day 4, voted out');
    expect(fateOf(view, 'player_3')).toBe('night 2, the serial killer');
    expect(fateOf(view, 'player_9')).toBe('night 4, the vigilante');
  });

  it('names the last standing', () => {
    expect(lastStanding(['player_8'])).toBe('Seat 8 is the last of them standing');
    expect(lastStanding(['player_3', 'player_8'])).toBe(
      'Seats 3 and 8 are the last of them standing',
    );
    expect(lastStanding(['player_1', 'player_7', 'player_9'])).toBe(
      'Seats 1, 7 and 9 are the last of them standing',
    );
  });
});

describe('the stand for the winners', () => {
  it('sizes one, two and three figures at 1, 0.78 and 0.6, the box ×1, ×1.36, ×1.6', () => {
    expect(standSet(1)).toEqual({ scale: 1, offsets: [0], widen: 1 });
    const two = standSet(2);
    expect([two.scale, two.widen]).toEqual([0.78, 1.36]);
    expect(two.offsets).toEqual([-0.25, 0.25]);
    const three = standSet(3);
    expect([three.scale, three.widen]).toEqual([0.6, 1.6]);
    expect(three.offsets.map((x) => Math.round(x * 100) / 100)).toEqual([-0.52, 0, 0.52]);
  });

  it('sets it all at 0.84 beside the open film', () => {
    expect(standSet(1, true)).toEqual({ scale: 0.84, offsets: [0], widen: 1 });
    const three = standSet(3, true);
    expect([three.scale, three.widen].map((x) => Math.round(x * 1000) / 1000)).toEqual([
      0.504, 1.344,
    ]);
  });
});

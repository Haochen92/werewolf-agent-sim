import { describe, expect, it } from 'vitest';
import type { SceneBeat } from '../beats/types';
import { nextSpeaker, spritesAhead } from './ahead';

const CAST = ['owl', 'hare', 'cat'] as const;
const beat = (o: Partial<SceneBeat>): SceneBeat =>
  ({ scene: 'day', id: 'day.speech', ...o }) as SceneBeat;

describe('spritesAhead', () => {
  it('names the next day turn speaker after the index, skipping other scenes', () => {
    const beats = [
      beat({ scene: 'vote', id: 'vote.opens' }),
      beat({ id: 'day.speech', subject: 'player_2' }),
      beat({ id: 'day.speech', subject: 'player_3' }),
    ];
    expect(nextSpeaker(beats, 0, CAST)).toBe('hare');
    expect(nextSpeaker(beats, 1, CAST)).toBe('cat');
    expect(nextSpeaker(beats, 2, CAST)).toBeNull();
  });
  it('reads the seat of a human turn and gives both poses', () => {
    const beats = [beat({ id: 'day.your-turn', seat: 'player_1' })];
    expect(spritesAhead(beats, -1, CAST, (c, p) => `${c}/${p}`)).toEqual([
      'owl/thinking',
      'owl/talking',
    ]);
  });
  it('gives nothing when no day turn is ahead', () => {
    expect(
      spritesAhead([beat({ scene: 'over', id: 'over.curtain' })], -1, CAST, () => 'x'),
    ).toEqual([]);
  });
});

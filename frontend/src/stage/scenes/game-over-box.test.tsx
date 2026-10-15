import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import { PHASE3_GAME } from '../workbench/fixture';
import { EndBox } from './GameOverScene';
import { neutralLine } from './game-over';

describe('the game over’s box: a draw with a neutral’s win under it', () => {
  it('says no side won, then the fortune teller’s points, with no side’s pennant', () => {
    // the ten-seat golden's fortune teller (won, 2 points), its game made a draw
    const view = { ...foldEvents(PHASE3_GAME.events), winner: null };
    const neutral = neutralLine(view);
    expect(neutral).toBe('The fortune teller won, with 2 points');
    const out = renderToStaticMarkup(
      <EndBox
        winner="draw"
        neutral={neutral}
        won={false}
        winners={[]}
        me={null}
        myRole={null}
        myDead={false}
        cast={[]}
        truth={false}
        way={false}
        arrive={false}
      />,
    );
    expect(out).toMatch(
      /No side has won[\s\S]*data-neutral[^>]*>The fortune teller won, with 2 points/,
    );
    expect(out).not.toContain('No one');
    expect(out).not.toContain('data-faction');
  });
});

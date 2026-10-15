import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { CastLine, castOrder } from './Notice';

describe('the cast plate', () => {
  it('reads a ten-seat lineup in the role sheet’s order, whatever order the counts came in', () => {
    // the phase-3 fixture's counts, alphabetical as the wire sends them
    const counts = {
      chanteuse: 1,
      fortune_teller: 1,
      healer: 1,
      illusionist: 1,
      investigator: 1,
      sentinel: 1,
      serial_killer: 1,
      sigilist: 1,
      trailseer: 1,
      vigilante: 1,
    };
    expect(castOrder(counts)).toEqual([
      'investigator',
      'sentinel',
      'trailseer',
      'vigilante',
      'sigilist',
      'healer',
      'chanteuse',
      'illusionist',
      'serial_killer',
      'fortune_teller',
    ]);
    const out = renderToStaticMarkup(<CastLine counts={counts} />);
    expect(out).toContain('fortune teller');
    expect(out.match(/data-sigil=/g)).toHaveLength(10);
  });

  it('keeps a nine-seat archive’s villagers and wolves at the head of their sides, in plurals', () => {
    const counts = {
      wolf: 2,
      serial_killer: 1,
      villager: 3,
      healer: 1,
      investigator: 1,
      vigilante: 1,
    };
    expect(castOrder(counts)).toEqual([
      'villager',
      'investigator',
      'vigilante',
      'healer',
      'wolf',
      'serial_killer',
    ]);
    const out = renderToStaticMarkup(<CastLine counts={counts} />);
    expect(out).toContain('villagers');
    expect(out).toContain('wolves');
  });

  it('puts a role the stage does not know last', () => {
    expect(castOrder({ jester: 1, healer: 1 })).toEqual(['healer', 'jester']);
  });
});

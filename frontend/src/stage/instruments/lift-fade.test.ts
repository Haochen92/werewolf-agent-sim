import { describe, expect, it } from 'vitest';
import { loadOpacity } from './lift-fade';

describe('the load’s fade on the lift', () => {
  // a table at rest: the line that starts its fade 100 units above the lip, the one that ends it 400 above
  const lip = 700,
    lines = [600, 300] as const;

  it('is whole at rest and until the starting line reaches the lip', () => {
    expect(loadOpacity(0, lip, lines)).toBe(1);
    expect(loadOpacity(100, lip, lines)).toBe(1);
  });

  it('is gone once the higher line reaches the lip, and stays gone below it', () => {
    expect(loadOpacity(400, lip, lines)).toBe(0);
    expect(loadOpacity(800, lip, lines)).toBe(0);
  });

  it('fades evenly with the distance in between', () => {
    expect(loadOpacity(250, lip, lines)).toBeCloseTo(0.5, 9);
    expect(loadOpacity(175, lip, lines)).toBeCloseTo(0.75, 9);
  });

  it('is already fading at rest if its starting line starts under the lip', () => {
    expect(loadOpacity(0, lip, [750, 300])).toBeCloseTo(400 / 450, 9);
  });

  it('cuts cleanly where the line meets the lip when the two lines are one', () => {
    expect(loadOpacity(99, lip, [600, 600])).toBe(1);
    expect(loadOpacity(100, lip, [600, 600])).toBe(0);
  });
});

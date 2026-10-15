import { describe, expect, it } from 'vitest';
import { STAGE_H, WING_N } from '../units';
import { RAIL_GAP, RAIL_MAX_ROWS, RAIL_PAD, railLayout } from './rail-layout';

const NS = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14];

describe('railLayout', () => {
  it.each(NS)('N = %i: every seat has a cell, and the rows fill the height', (n) => {
    const L = railLayout(n);
    expect(L.cols * L.rows).toBeGreaterThanOrEqual(n);
    // no empty row: the last row holds at least one seat
    expect((L.rows - 1) * L.cols).toBeLessThan(n);
    const used = 2 * RAIL_PAD + L.rows * L.cardH + (L.rows - 1) * RAIL_GAP;
    expect(used).toBeCloseTo(STAGE_H, 6);
  });

  it('two columns up to six rows', () => {
    for (const n of [5, 6, 7, 8, 9, 10, 11, 12]) expect(railLayout(n).cols).toBe(2);
    expect(railLayout(12).rows).toBe(RAIL_MAX_ROWS);
  });

  it('more than six rows: a third column and a wider rail', () => {
    for (const n of [13, 14]) {
      const L = railLayout(n);
      expect(L.cols).toBe(3);
      expect(L.rows).toBe(5);
      expect(L.target).toBeGreaterThan(railLayout(12).target);
    }
  });

  it('one card alone takes the whole rail', () => {
    expect(railLayout(1)).toMatchObject({ cols: 1, rows: 1 });
    expect(railLayout(2).cols).toBe(2);
  });

  it('nine seats: the numbers the stage is drawn with', () => {
    const L = railLayout(9);
    expect(L).toMatchObject({ cols: 2, rows: 5 });
    expect(L.width).toBe(WING_N);
    expect(L.cardH).toBeCloseTo(166.4, 1);
    expect(L.cardW).toBeCloseTo(77, 6);
    // on a phone held sideways the rail is ~128 css px (iPhone 14: 0.433 css px per unit)
    expect(L.target * (693.25 / 1600)).toBeGreaterThan(120);
    expect(L.target * (693.25 / 1600)).toBeLessThan(135);
  });

  it('cards stay a tap target on an iPhone 14 held sideways (44 css px) up to twelve', () => {
    const k = 693.25 / 1600;
    for (const n of NS.filter((x) => x <= 12)) {
      const L = railLayout(n);
      expect(L.cardH * k).toBeGreaterThanOrEqual(44);
      expect(L.targetCardW * k).toBeGreaterThanOrEqual(44);
    }
  });
});

import { describe, expect, it } from 'vitest';
import { STAGE_H, WING_N } from '../units';
import { RAIL_GAP, RAIL_MAX_ROWS, RAIL_PAD, RAIL_STRIP, railLayout } from './rail-layout';

const NS = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14];

describe('railLayout', () => {
  it.each(NS)('N = %i: every seat has a cell, and the rows fill the height', (n) => {
    const L = railLayout(n);
    expect(L.cols * L.rows).toBeGreaterThanOrEqual(n);
    // no empty row: the last row holds at least one seat
    expect((L.rows - 1) * L.cols).toBeLessThan(n);
    const strip = L.suspect?.kind === 'strip' ? RAIL_STRIP + RAIL_GAP : 0;
    const used = 2 * RAIL_PAD + strip + L.rows * L.cardH + (L.rows - 1) * RAIL_GAP;
    expect(used).toBeCloseTo(STAGE_H, 6);
  });

  it.each(NS)('N = %i: the suspect takes the spare cell, else a strip', (n) => {
    const L = railLayout(n);
    const spare = L.rows * L.cols - n;
    if (spare > 0) {
      expect(L.suspect).toEqual({
        kind: 'cell',
        row: Math.floor(n / L.cols),
        col: n % L.cols,
      });
      // the cell is right after the last seat, in the last row
      expect((L.suspect as { row: number }).row).toBe(L.rows - 1);
    } else expect(L.suspect).toEqual({ kind: 'strip' });
  });

  it('two columns up to six rows: odd counts a cell, even counts a strip', () => {
    for (const n of [5, 7, 9, 11]) {
      expect(railLayout(n).cols).toBe(2);
      expect(railLayout(n).suspect?.kind).toBe('cell');
    }
    for (const n of [6, 8, 10, 12]) {
      expect(railLayout(n).cols).toBe(2);
      expect(railLayout(n).suspect?.kind).toBe('strip');
    }
    expect(railLayout(12).rows).toBe(RAIL_MAX_ROWS);
  });

  it('more than six rows: a third column and a wider rail', () => {
    for (const n of [13, 14]) {
      const L = railLayout(n);
      expect(L.cols).toBe(3);
      expect(L.rows).toBe(5);
      expect(L.suspect?.kind).toBe('cell');
      expect(L.target).toBeGreaterThan(railLayout(12).target);
    }
  });

  it('nine seats: the numbers the stage is drawn with', () => {
    const L = railLayout(9);
    expect(L).toMatchObject({
      cols: 2,
      rows: 5,
      suspect: { kind: 'cell', row: 4, col: 1 },
    });
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

  it('without the suspect slot: no strip, and the spare cell stays empty', () => {
    expect(railLayout(8, { suspect: false }).suspect).toBeNull();
    expect(railLayout(8, { suspect: false }).cardH).toBeGreaterThan(railLayout(8).cardH);
    expect(railLayout(9, { suspect: false }).cardH).toBeCloseTo(railLayout(9).cardH, 6);
  });
});

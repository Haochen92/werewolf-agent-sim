import { describe, expect, it } from 'vitest';
import { geometry } from '../units';
import { homography, project, type Pt } from './homography';
import {
  GLASS_PX,
  TABLE_PX,
  countShot,
  jarGeometry,
  pileSpots,
  plateSpots,
  stackPos,
  voteGeometry,
} from './vote-geometry';

describe('the wood’s homography', () => {
  const quad: [Pt, Pt, Pt, Pt] = [
    [455, 488],
    [390, 543],
    [1298, 543],
    [1233, 488],
  ];

  it('carries the box’s four corners onto the table’s top', () => {
    const [w, h] = [320, 907];
    const corners: Pt[] = [
      [0, 0],
      [w, 0],
      [w, h],
      [0, h],
    ];
    corners.forEach((c, i) => {
      const [x, y] = project(w, h, quad, c);
      expect(x).toBeCloseTo(quad[i][0], 6);
      expect(y).toBeCloseTo(quad[i][1], 6);
    });
  });

  it('writes a CSS matrix3d', () => {
    expect(homography(320, 907, quad)).toMatch(/^matrix3d\((-?[\d.e-]+,){15}-?[\d.e-]+\)$/);
  });
});

describe('the vote’s geometry', () => {
  const v = voteGeometry(geometry('live'));

  it('sizes the table as the bench does, and stands it whole, its feet near the frame’s foot', () => {
    // 0.6 of the room right of the wing
    expect(v.tw).toBeCloseTo(0.6 * geometry('live').room, 6);
    const s = v.tw / (TABLE_PX.right - TABLE_PX.left);
    expect(v.footY).toBeLessThan(900);
    expect(v.footY - v.topY).toBeCloseTo((TABLE_PX.feet - TABLE_PX.front) * s, 6);
    expect(v.drop).toBeCloseTo(TABLE_PX.drop * s, 6);
  });

  it('caps a tower at four chips and starts a second one beside it', () => {
    const [p] = plateSpots(v, ['player_6', 'player_7'], { player_6: 6, player_7: 1 });
    expect(p.towers).toBe(2);
    const [x0] = stackPos(v, p, 0),
      [x3, y3] = stackPos(v, p, 3),
      [x4, y4] = stackPos(v, p, 4);
    expect(x3).toBe(x0);
    expect(x4).toBeGreaterThan(x0);
    expect(y4).toBeGreaterThan(y3);
  });

  it('sizes the jar to its picture and seats the lid on the lip', () => {
    const J = jarGeometry(v);
    expect(J.w / J.h).toBeCloseTo(GLASS_PX.w / GLASS_PX.h, 9);
    // the lid's foot (its flange's) inside the neck, its dome a little wider than the lip
    expect(J.lid.ly + J.lid.lh).toBeCloseTo(v.base - J.h * 0.793, 6);
    expect(J.lid.lw / J.wN).toBeGreaterThan(1);
    expect(J.lid.lw / J.wN).toBeLessThan(1.15);
  });

  it('piles the chips on the glass bottom, inside the walls', () => {
    const J = jarGeometry(v);
    for (const [x, y] of pileSpots(v, 9)) {
      expect(y).toBeLessThan(J.floor);
      expect(Math.abs(x - v.cx) + v.r).toBeLessThanOrEqual(J.w / 2);
    }
  });

  it('keeps every plate clear of the jar standing at the table’s end', () => {
    const J = jarGeometry(v),
      jarLeft = J.aside.x - (J.w * J.aside.sc) / 2;
    for (let n = 1; n <= 8; n++) {
      const cands = Array.from({ length: n }, (_, i) => `player_${i + 1}`);
      for (const p of plateSpots(v, cands, {})) expect(p.x + p.rx).toBeLessThan(jarLeft);
    }
    // and the jar is still on the table
    expect(J.aside.x + (J.w * J.aside.sc) / 2).toBeLessThanOrEqual(v.cx + v.tw / 2);
  });

  it('pushes in by 1.32, bringing the table’s front edge to where the bench’s came', () => {
    const s = countShot(v),
      g = geometry('live');
    expect(s.scale).toBe(1.32);
    expect(s.x).toBe(v.cx);
    // the bench: scaled about (cx, edge − 0.04H), the picture then dropped 0.015H
    const edge = g.railY - 0.15 * g.ph;
    expect(s.y + 1.32 * (v.topY - s.y)).toBeCloseTo(edge + 0.32 * 0.04 * 900 + 0.015 * 900, 6);
  });
});

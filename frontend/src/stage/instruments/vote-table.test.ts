import { describe, expect, it } from 'vitest';
import { geometry } from '../units';
import { homography, project, type Pt } from './homography';
import {
  GLASS_PX,
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

  it('sizes the table a tenth narrower than the trap, as the bench does', () => {
    expect(v.trapW / v.tw).toBeCloseTo(1.1, 9);
    // the trap is 0.66 of the room right of the wing (907.2 with the kit's 88-unit wing)
    expect(v.tw).toBeCloseTo(0.6 * geometry('live').room, 6);
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
    // the lid's foot on the lip's foot, its collar a little wider than the lip
    expect(J.lid.ly + J.lid.lh).toBeCloseTo(v.base - J.h * 0.907, 6);
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

  it('pushes in by 1.32 about a point above the table', () => {
    const s = countShot(v);
    expect(s.scale).toBe(1.32);
    expect(s.x).toBe(v.cx);
    expect(s.y).toBeLessThan(v.topY);
  });
});

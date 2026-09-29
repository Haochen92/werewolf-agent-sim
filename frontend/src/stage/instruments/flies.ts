/**
 * Where things hang from the flies, in units: the row of chips, the cards under them, the one
 * chip brought down alone at the centre, the large card. The deal, the night lobby and the
 * morning all hang things on strings; keeping their measures here means a chip in the lobby
 * and the same chip at the morning are the same size, and a number can be checked against the
 * benches (rev 67 `VG`, rev 75 `render`) in one place.
 */
import type { DiningCarPlan } from '../paint/dining-car';
import { STAGE_H, STAGE_W, type StageGeometry } from '../units';

export interface ChipRow {
  /** Left end of the row and its length; chip i of n sits at x0 + span·(i + ½)/n. */
  x0: number;
  span: number;
  /** The chips' centre line. */
  rowY: number;
  /** A chip's radius. */
  cr: number;
}

/**
 * The two rows the benches hang. `low`: with nothing at the stand, across the whole room over
 * the dado (the night lobby). `high`: at the window's height, across the wall either side of it
 * (the deal, where the cards hang below it).
 */
export function chipRow(
  g: StageGeometry,
  plan: DiningCarPlan,
  kind: 'low' | 'high',
): ChipRow {
  const W = STAGE_W,
    H = STAGE_H;
  if (kind === 'low') {
    const span = g.room * 0.86;
    return {
      x0: g.wingN + g.room * 0.07,
      span,
      rowY: 0.52 * H,
      cr: Math.min(0.036 * W, (span / 9) * 0.42),
    };
  }
  const [, wy, , wh] = plan.window;
  // beside an open side slot the row keeps inside the room, as the speech box does
  const x0 = Math.max(plan.slots.L[1] - 0.01 * W, g.wingN + 0.02 * W),
    x1 = Math.min(plan.slots.R[0] + 0.01 * W, g.wingN + g.room - 0.02 * W);
  return {
    x0,
    span: x1 - x0,
    rowY: wy + wh * 0.46,
    cr: Math.min(0.027 * W, ((x1 - x0) / 9) * 0.44),
  };
}

/** The centre of the i-th of n chips in a row. */
export function rowX(row: ChipRow, i: number, n: number): number {
  return row.x0 + (row.span * (i + 0.5)) / n;
}

/** Where a string ties on to a chip: just above its rim. */
export const tieY = (y: number, r: number) => y - r - 4;

/** The small cards the deal hangs, one under each chip of the high row. */
export function smallCards(g: StageGeometry, row: ChipRow) {
  const top = row.rowY + row.cr + 0.035 * STAGE_H;
  const w = Math.min((row.span / 9) * 0.86, (g.railY - 0.04 * STAGE_H - top) * 0.72);
  return { top, w, h: w / 0.72 };
}

/** The morning's one chip, brought down alone: centred, near twice the lobby's size. */
export function featuredChip(g: StageGeometry, low: ChipRow) {
  return { x: g.cx, y: 0.34 * STAGE_H, r: low.cr * 1.9 };
}

/** The large card at the centre: your card at the deal (`deal`), a dead seat's at the morning. */
export function bigCard(g: StageGeometry, at: 'deal' | 'morning') {
  const h = (at === 'deal' ? 0.62 : 0.66) * STAGE_H,
    w = h * 0.72;
  const top = (at === 'deal' ? 0.44 : 0.5) * STAGE_H - h / 2;
  return { x: g.cx - w / 2, top, w, h };
}

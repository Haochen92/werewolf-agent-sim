/**
 * The replay's frame: a red valance across the top with a scalloped gold hem, and the dark
 * scalloped border in front of it. Live play has no frame; the replay wears it so a finished
 * game reads as a performance being shown again.
 *
 * Top only, by the owner's ruling of 2026-09-24: the side curtains and the proscenium posts
 * were taking the room the seat wing and the side slot need, so they went. It is the house's
 * frame, not part of the room, so it sits above the light overlay (the room's darkness never
 * falls on it) and under the HUD.
 *
 * Ported from `dressingTop()` on the game-over bench (revision 73); the kit's `dressing()` is
 * the older full version and is not used. It makes no ids, so it needs no prefix, except with
 * `bleed`: then it carries on past the world's sides, fading out (stage_architecture.md §3).
 */
import { BLEED_DARK, STAGE_H, STAGE_W } from '../units';
import { MATERIALS } from './materials';

/* the top-only dressing: the valance and the scalloped border, no legs, no posts (Haochen, 2026-09-24) */
export function drape(o: { id?: string; bleed?: number } = {}): string {
  const W = STAGE_W,
    H = STAGE_H,
    b = o.bleed ?? 0;
  let d = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0;width:100%;height:100%${b ? ';overflow:visible' : ''}">`;
  if (b) {
    // past the world's sides, the same valance in step with it, fading out as the bleed darkens
    const P = (o.id ?? 'drape') + '-',
      T = W + 2 * b,
      at = (x: number) => ((x + b) / T).toFixed(4),
      from = -Math.ceil(b / (0.08 * W)) * 0.08 * W;
    d += `<defs><linearGradient id="${P}dfade" gradientUnits="userSpaceOnUse" x1="${-b}" y1="0" x2="${W + b}" y2="0"><stop offset="${at(-BLEED_DARK)}" stop-color="#000"/><stop offset="${at(0)}" stop-color="#fff"/><stop offset="${at(W)}" stop-color="#fff"/><stop offset="${at(W + BLEED_DARK)}" stop-color="#000"/></linearGradient><mask id="${P}dmask" maskUnits="userSpaceOnUse" x="${-b}" y="0" width="${T}" height="${H}"><rect x="${-b}" y="0" width="${b}" height="${H}" fill="url(#${P}dfade)"/><rect x="${W}" y="0" width="${b}" height="${H}" fill="url(#${P}dfade)"/></mask></defs>`;
    d += `<g mask="url(#${P}dmask)">${valance(from, W - from)}</g>`;
  }
  return d + valance(0, W) + `</svg>`;
}

/* the valance and the border from x0 to x1, x0 on a scallop of the hem */
function valance(x0: number, x1: number): string {
  const H = STAGE_H,
    W = STAGE_W,
    s = 1,
    m = MATERIALS,
    gold = '#c9a25e';
  let d = `<rect x="${x0}" y="0" width="${x1 - x0}" height="${0.075 * H}" fill="#4a1418"/>`;
  let hem = `M${x0},${0.075 * H}`;
  for (let x = x0; x < x1; x += 0.08 * W) hem += ` q${0.04 * W},${0.025 * H} ${0.08 * W},0`;
  d += `<path d="${hem} V0 H${x0}Z" fill="#4a1418"/><path d="${hem}" fill="none" stroke="${gold}" stroke-width="${3 * s}"/><path d="M${x0},${0.012 * H} H${x1}" stroke="${gold}" stroke-width="${2 * s}" stroke-opacity=".7"/>`;
  let sc = '';
  for (let x = x0 - 80 * s; x < x1 + 160 * s; x += 160 * s)
    sc += `M${x.toFixed(0)},0 V${(30 * s).toFixed(0)} a${80 * s},${66 * s} 0 0 0 ${160 * s},0 V0Z`;
  d += `<path d="${sc}" fill="${m.border}"/>`;
  let fr = '';
  for (let x = x0 - 80 * s; x < x1 + 160 * s; x += 160 * s)
    fr += `M${x.toFixed(0)},${(30 * s).toFixed(0)} a${80 * s},${66 * s} 0 0 0 ${160 * s},0`;
  d += `<path d="${fr}" fill="none" stroke="${m.frameLine}" stroke-width="${3 * s}"/>`;
  return d;
}

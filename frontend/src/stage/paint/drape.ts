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
 * the older full version and is not used. It makes no ids, so it needs no prefix.
 */
import { STAGE_H, STAGE_W } from '../units';
import { MATERIALS } from './materials';

/* the top-only dressing: the valance and the scalloped border, no legs, no posts (Haochen, 2026-09-24) */
export function drape(): string {
  const W = STAGE_W,
    H = STAGE_H,
    s = 1,
    m = MATERIALS,
    gold = '#c9a25e';
  let d = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0;width:100%;height:100%">`;
  d += `<rect x="0" y="0" width="${W}" height="${0.075 * H}" fill="#4a1418"/>`;
  let hem = `M0,${0.075 * H}`;
  for (let x = 0; x < W; x += 0.08 * W) hem += ` q${0.04 * W},${0.025 * H} ${0.08 * W},0`;
  d += `<path d="${hem} V0 H0Z" fill="#4a1418"/><path d="${hem}" fill="none" stroke="${gold}" stroke-width="${3 * s}"/><path d="M0,${0.012 * H} H${W}" stroke="${gold}" stroke-width="${2 * s}" stroke-opacity=".7"/>`;
  let sc = '';
  for (let x = -80 * s; x < W + 160 * s; x += 160 * s)
    sc += `M${x.toFixed(0)},0 V${(30 * s).toFixed(0)} a${80 * s},${66 * s} 0 0 0 ${160 * s},0 V0Z`;
  d += `<path d="${sc}" fill="${m.border}"/>`;
  let fr = '';
  for (let x = -80 * s; x < W + 160 * s; x += 160 * s)
    fr += `M${x.toFixed(0)},${(30 * s).toFixed(0)} a${80 * s},${66 * s} 0 0 0 ${160 * s},0`;
  d += `<path d="${fr}" fill="none" stroke="${m.frameLine}" stroke-width="${3 * s}"/>`;
  return d + `</svg>`;
}

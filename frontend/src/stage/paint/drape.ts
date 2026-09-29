/**
 * The replay's frame: one walnut valance across the top, the HUD's wood, with a shallow
 * scalloped hem trimmed in a single brass line. Live play has no frame; the replay wears it so
 * a finished game reads as a performance being shown again.
 *
 * Top only, by the owner's ruling of 2026-09-24: the side curtains and the proscenium posts
 * were taking the room the seat wing and the side slot need, so they went. It is the house's
 * frame, not part of the room, so it sits above the light overlay (the room's darkness never
 * falls on it) and under the HUD.
 *
 * One edge, by the owner's ruling of 2026-09-29: the red velvet with its gold hem and the dark
 * scalloped border in front of it read as two layers, so both became this one board, in the
 * HUD's materials (materials.ts: walnut, `--hud-brass`). Vector only. With `bleed` it carries on
 * past the world's sides, fading out (stage_architecture.md §3).
 */
import { BLEED_DARK, STAGE_H, STAGE_W } from '../units';
import { MATERIALS } from './materials';

/* the top-only dressing: the valance, no legs, no posts (Haochen, 2026-09-24) */
export function drape(o: { id?: string; bleed?: number } = {}): string {
  const W = STAGE_W,
    H = STAGE_H,
    b = o.bleed ?? 0,
    P = (o.id ?? 'drape') + '-',
    m = MATERIALS;
  let d = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0;width:100%;height:100%${b ? ';overflow:visible' : ''}">`;
  // the walnut, lit from above as the HUD's boards are (walnutTop → walnutBot, opaque here)
  d += `<defs><linearGradient id="${P}wood" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="rgb(52,34,21)"/><stop offset="1" stop-color="rgb(30,19,11)"/></linearGradient></defs>`;
  if (b) {
    // past the world's sides, the same valance in step with it, fading out as the bleed darkens
    const T = W + 2 * b,
      at = (x: number) => ((x + b) / T).toFixed(4),
      from = -Math.ceil(b / (0.08 * W)) * 0.08 * W;
    d += `<defs><linearGradient id="${P}dfade" gradientUnits="userSpaceOnUse" x1="${-b}" y1="0" x2="${W + b}" y2="0"><stop offset="${at(-BLEED_DARK)}" stop-color="#000"/><stop offset="${at(0)}" stop-color="#fff"/><stop offset="${at(W)}" stop-color="#fff"/><stop offset="${at(W + BLEED_DARK)}" stop-color="#000"/></linearGradient><mask id="${P}dmask" maskUnits="userSpaceOnUse" x="${-b}" y="0" width="${T}" height="${H}"><rect x="${-b}" y="0" width="${b}" height="${H}" fill="url(#${P}dfade)"/><rect x="${W}" y="0" width="${b}" height="${H}" fill="url(#${P}dfade)"/></mask></defs>`;
    d += `<g mask="url(#${P}dmask)">${valance(from, W - from, `url(#${P}wood)`, m.brass)}</g>`;
  }
  return d + valance(0, W, `url(#${P}wood)`, m.brass) + `</svg>`;
}

/* the valance from x0 to x1, x0 on a scallop of the hem: the board, its dark reveal, the brass */
function valance(x0: number, x1: number, wood: string, brass: string): string {
  const H = STAGE_H,
    W = STAGE_W,
    y = 0.06 * H;
  let hem = `M${x0},${y}`;
  for (let x = x0; x < x1; x += 0.08 * W) hem += ` q${0.04 * W},${0.022 * H} ${0.08 * W},0`;
  return (
    `<path d="${hem} V0 H${x0}Z" fill="${wood}"/>` +
    // the dark reveal just inside the edge, then the one brass line along the hem
    `<path d="${hem}" transform="translate(0,-3)" fill="none" stroke="rgba(14,8,4,.85)" stroke-width="2.5"/>` +
    `<path d="${hem}" fill="none" stroke="${brass}" stroke-width="2.5"/>`
  );
}

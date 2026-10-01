/**
 * The replay's frame: one red velvet valance across the top, swagged, with a braided gold hem
 * and a fringe (a painted raster, `SPRITES.props.valance`). Live play has no frame; the replay
 * wears it so a finished game reads as a performance being shown again.
 *
 * Top only, by the owner's ruling of 2026-09-24: the side curtains and the proscenium posts
 * were taking the room the seat wing and the side slot need, so they went. It is the house's
 * frame, not part of the room, so it sits above the light overlay (the room's darkness never
 * falls on it) and under the HUD.
 *
 * The theatre's velvet after all (owner, 2026-09-30; from 2026-09-29 it was a walnut board with
 * a brass line, in the HUD's materials): the painting spans the world's width in one piece,
 * squashed to half its height, the swags, the braid and the fringe on the stage and the plain
 * velvet above it. Its ends do not meet, so with `bleed` it
 * carries on past the world's sides mirrored (the seam is its own edge), sinking into the
 * house's dark as the bleed does (stage_architecture.md §3): over each mirrored copy a gradient
 * of that dark, clear at the world's edge and whole BLEED_DARK units out. (Until 2026-10-01 the
 * copies faded out through an SVG mask; iPhone Safari kills a page that masks the stage, §6.
 * The bleed under them is that same dark by then, so the look is the same.) Without `src` (a
 * test) the frame draws nothing.
 */
import { BLEED_DARK, STAGE_H, STAGE_W } from '../units';

/** The house's dark, which the bleed reaches BLEED_DARK units out (bleed.ts, `PaintedBleed`). */
const HOUSE = '#0c0a07';

/** The painting's size (px) and the row its fringe's tips reach (below it, only stray threads). */
const PAINTED = { w: 2000, h: 395, tips: 385 };
/**
 * Drawn at half its height (owner, 2026-09-30: 1600 × 158 units; the folds read as tighter
 * gathers), its fringe's tips at 0.085 H, just under the strip's plaques: the whole red swags,
 * the braid and the fringe show, and the plain velvet at its top hangs off the stage.
 */
const SQUASH = 0.5;
const TIPS_AT = 0.085 * STAGE_H;

/* the top-only dressing: the valance, no legs, no posts (Haochen, 2026-09-24) */
export function drape(o: { id?: string; bleed?: number; src?: string } = {}): string {
  const W = STAGE_W,
    H = STAGE_H,
    b = o.bleed ?? 0,
    P = (o.id ?? 'drape') + '-';
  let d = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0;width:100%;height:100%${b ? ';overflow:visible' : ''}">`;
  if (!o.src) return d + `</svg>`;
  const h = ((W * PAINTED.h) / PAINTED.w) * SQUASH,
    top = TIPS_AT - (PAINTED.tips / PAINTED.h) * h;
  const img = `<image href="${o.src}" x="0" y="${top.toFixed(1)}" width="${W}" height="${h.toFixed(1)}" preserveAspectRatio="none"/>`;
  if (b) {
    // past the world's sides, the painting mirrored about each edge, sinking into the house's
    // dark as the bleed does: clear at the world's edge, the dark whole BLEED_DARK units out
    const T = W + 2 * b,
      at = (x: number) => ((x + b) / T).toFixed(4);
    d += `<defs><linearGradient id="${P}dfade" gradientUnits="userSpaceOnUse" x1="${-b}" y1="0" x2="${W + b}" y2="0"><stop offset="${at(-BLEED_DARK)}" stop-color="${HOUSE}"/><stop offset="${at(0)}" stop-color="${HOUSE}" stop-opacity="0"/><stop offset="${at(W)}" stop-color="${HOUSE}" stop-opacity="0"/><stop offset="${at(W + BLEED_DARK)}" stop-color="${HOUSE}"/></linearGradient></defs>`;
    d += `<g transform="scale(-1,1)">${img}</g><g transform="translate(${2 * W},0) scale(-1,1)">${img}</g>`;
    // the dark over the copies only, the painting's own box
    d += `<rect x="${-b}" y="${top.toFixed(1)}" width="${b}" height="${h.toFixed(1)}" fill="url(#${P}dfade)"/><rect x="${W}" y="${top.toFixed(1)}" width="${b}" height="${h.toFixed(1)}" fill="url(#${P}dfade)"/>`;
  }
  return d + img + `</svg>`;
}

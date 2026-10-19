/**
 * The dining car's window: its place in the layout, and the louvred shutter that covers it.
 * The frame, the glass and the country in it are the car's painting at the hour (CarBackdrop).
 *
 * The shutter is drawn over the painting, because it is the one part of the window that moves
 * (the Shutter instrument reuses the geometry here). At rest it is either gathered up under its
 * pelmet, which sits on the painted blind's housing, or down over the glass and its frame.
 *
 * Sources: the window's place from the design kit (kits/stage-kit.js); the shutter from the
 * cover bench (revision 66), as the game-over bench (revision 73) draws it.
 */
import { geometry, STAGE_H, STAGE_W, type Hud, type StageGeometry } from '../units';
import { brass, inkP, K2, rnd, type Rect } from './draw';
import { CAR } from './materials';
import { DARKER, walnutAcross, walnutImage } from './texture';

/** The dining car's horizontal lines, shared by the car and its window. */
export function carLines(g: StageGeometry) {
  const H = STAGE_H,
    B = g.railY;
  const floorH = 0.065 * H,
    floorY = B - floorH,
    dado = floorY - CAR.dadoH * H;
  return { floorH, floorY, dado, B };
}

/**
 * The layout the car's painting is fitted to, in its own 1600×900 pixels: the puppet's centre
 * line and the rail (the kit's car at HUD 'none'; scripts/fit_car_hours.py).
 */
export const CAR_FIT = { cx: 800, railY: 639 } as const;
/** The painting's glass in the same pixels, centred on the puppet (owner's car, 2026-10-19). */
export const CAR_GLASS = { x0: 440, y0: 77, x1: 1160, y1: 389, r: 34 } as const;

/** The window's glass, in units: the painting's, which follows the puppet and the rail. */
export function windowRect(g: StageGeometry): Rect {
  const G = CAR_GLASS;
  return [g.cx - CAR_FIT.cx + G.x0, g.railY - CAR_FIT.railY + G.y0, G.x1 - G.x0, G.y1 - G.y0];
}

/** Snow falling past the glass: two copies stacked so the loop has no seam. */
export const snowfall = (x: number, y: number, w: number, h: number, s: number): string => {
  let f = '';
  for (let i = 0; i < 40; i++)
    f += `<circle cx="${(x + rnd(i, 241) * w).toFixed(0)}" cy="${(y + rnd(i, 242) * h).toFixed(0)}" r="${((0.9 + rnd(i, 243) * 1.4) * s).toFixed(1)}" fill="#fff" fill-opacity=".8"/>`;
  return `<g class="sk-snw" style="--sh:${h.toFixed(0)}px">${f}<g transform="translate(0,${-Number(h.toFixed(0))})">${f}</g></g>`;
};

/* ---------- the shutter ---------- */
const WAL = '#3a2212',
  WAL2 = '#4a2c18',
  WALHI = '#6a4a2a';

export type ShutterState = 'open' | 'closed';

export interface ShutterOpts {
  /** Prefix for every id this drawing makes, so two stages can share a page. */
  id: string;
  hud?: Hud;
  side?: boolean;
  state: ShutterState;
  /** The walnut tile's URL: the shutter is the walls' wood, its grain along the slats. */
  walnut?: string;
  /** The painted shutter's URL (`SPRITES.props.shutter`): drawn in place of the vector louvres. */
  picture?: string;
}

/**
 * The painted shutter (px; the felt set of 2026-10-17): a burgundy felt roller blind, its cloth's
 * edges at `cloth`, the hem rod's centre on row `hem`, the rod from `rod[0]` with its brass pull
 * ring hanging below it to the picture's foot. The cloth spans the frame and its top to the
 * rod's centre the frame's height, so the rod lies along the frame's foot, the ring below it.
 */
const PAINTED_SHUTTER = { w: 1499, h: 673, cloth: [13.2, 1486.3], hem: 569.2, rod: 537.1 };

/** The shutter's pieces in units: the frame it covers, the pelmet above it, one section's height. */
export function shutterGeometry(g: StageGeometry, s = 1) {
  const [wx, wy, ww, wh] = windowRect(g);
  const f = {
    x: wx - 10 * s,
    y: wy - 10 * s,
    w: ww + 20 * s,
    h: wh + 20 * s,
    cx: wx + ww / 2,
  };
  const pel = { x: f.x - 6 * s, y: f.y - 30 * s, w: f.w + 12 * s, h: 26 * s };
  // the painted blind over the frame (its rod's ends and ring past it), and the box the moving
  // panel is clipped to: from under the pelmet down to the ring's foot, wide enough for the rod
  const P = PAINTED_SHUTTER,
    sx = f.w / (P.cloth[1] - P.cloth[0]),
    sy = f.h / P.hem;
  const picture = { x: f.x - P.cloth[0] * sx, y: f.y, w: P.w * sx, h: P.h * sy, sy };
  const top = pel.y + pel.h - 2 * s;
  const box = {
    x: Math.min(pel.x, picture.x - 2 * s),
    y: top,
    w: Math.max(pel.w, picture.w + 4 * s),
    h: picture.y + picture.h - top + 2 * s,
  };
  return { f, pel, section: f.h / 3, picture, box };
}

/**
 * The shutter's pieces as markup, for the paint above and for the Shutter instrument that
 * moves them: the clip that hides the panel under the pelmet (id `<id>-shc`), the three-section
 * panel down over the frame, the folded stack edge-on under the pelmet, and the pelmet itself.
 * Given `walnut`, the wood is textured (the clip then also carries its pattern, `<id>-shx`).
 * Given `picture` (owner, 2026-09-30; the felt roller blind since 2026-10-17), the panel is the
 * painted blind over the frame (`shutterGeometry().picture`: the cloth across it, its rod on the
 * frame's foot) and the rolled-up stack is the picture's rod and ring, the rod half under the
 * pelmet; the pelmet stays vector.
 */
export function shutterParts(
  g: StageGeometry,
  id: string,
  walnut?: string,
  picture?: string,
) {
  const s = 1,
    { f, pel, section: h3, picture: pic, box } = shutterGeometry(g, s),
    cid = id + '-shc',
    T = walnut ? id + '-shx' : null;
  // a walnut piece: flat, or the texture under a veil to the flat's value and then the ink
  const wood = (d: string, flat: string, w: number) =>
    T
      ? `<path d="${d}" fill="url(#${T})"/>${flat in DARKER ? `<path d="${d}" fill="#000" opacity="${DARKER[flat as keyof typeof DARKER]}"/>` : ''}${inkP(d, 'none', w)}`
      : inkP(d, flat, w);
  const louvre = (y: number, h: number, hinge: boolean) => {
    // a section of the shutter: stiles, slats, a hinge rail at the bottom
    const ix = f.x + 7 * s,
      iy = y + 5 * s,
      iw = f.w - 14 * s,
      ih = h - 10 * s;
    let q =
      wood(`M${f.x},${y} h${f.w} v${h} h${-f.w}Z`, WAL, 2.2 * s) +
      (T
        ? `<rect x="${ix}" y="${iy}" width="${iw}" height="${ih}" fill="url(#${T})"/><rect x="${ix}" y="${iy}" width="${iw}" height="${ih}" fill="#000" opacity="${DARKER['#2c1a0e']}"/><rect x="${ix}" y="${iy}" width="${iw}" height="${ih}" fill="none" stroke="${K2}" stroke-width="${1.2 * s}"/>`
        : `<rect x="${ix}" y="${iy}" width="${iw}" height="${ih}" fill="#2c1a0e" stroke="${K2}" stroke-width="${1.2 * s}"/>`);
    for (let yy = y + 9 * s; yy < y + h - 6 * s; yy += 8 * s) {
      const slat = `<path d="M${f.x + 9 * s},${yy.toFixed(1)} H${f.x + f.w - 9 * s}"`;
      // textured, the slat's lit edge is the walnut under its highlight, so the grain shows along it
      q += T
        ? `${slat} stroke="url(#${T})" stroke-width="${2.2 * s}"/>${slat} stroke="${WALHI}" stroke-opacity=".6" stroke-width="${2.2 * s}"/>`
        : `${slat} stroke="${WALHI}" stroke-width="${2.2 * s}"/>`;
      q += `<path d="M${f.x + 9 * s},${(yy + 2.6 * s).toFixed(1)} H${f.x + f.w - 9 * s}" stroke="#1b0f07" stroke-width="${1.4 * s}"/>`;
    }
    if (hinge)
      for (const hx of [f.x + f.w * 0.08, f.x + f.w * 0.5, f.x + f.w * 0.92])
        q += `<rect x="${hx - 5 * s}" y="${y + h - 3 * s}" width="${10 * s}" height="${6 * s}" rx="${1.5 * s}" fill="${brass}" stroke="${K2}" stroke-width="${s}"/>`;
    return q;
  };
  const P = PAINTED_SHUTTER;
  const panel = picture
    ? `<image href="${picture}" x="${pic.x}" y="${pic.y}" width="${pic.w}" height="${pic.h}" preserveAspectRatio="none"/>`
    : louvre(f.y, h3, true) +
      louvre(f.y + h3, h3, true) +
      louvre(f.y + 2 * h3, h3, false) +
      `<rect x="${f.cx - 14 * s}" y="${f.y + f.h - 12 * s}" width="${28 * s}" height="${5 * s}" rx="${2.5 * s}" fill="${brass}" stroke="${K2}" stroke-width="${s}"/>`;
  // rolled up: with the picture, the hem rod half under the pelmet, its ring hanging; without,
  // the louvres' folded sections, edge on
  let stack = '';
  if (picture) {
    const rodH = (P.hem - P.rod) * 2 * pic.sy,
      y = pel.y + pel.h - rodH / 2,
      h = (P.h - P.rod) * pic.sy;
    stack = `<svg x="${pic.x}" y="${y}" width="${pic.w}" height="${h}" viewBox="0 ${P.rod} ${P.w} ${P.h - P.rod}" preserveAspectRatio="none"><image href="${picture}" width="${P.w}" height="${P.h}"/></svg>`;
  } else
    for (let i = 0; i < 3; i++) {
      const x = f.x + 2 * s * i,
        y = pel.y + pel.h - 2 * s + i * 7 * s,
        w = f.w - 4 * s * i;
      stack += wood(`M${x},${y} h${w} v${7 * s} h${-w}Z`, i % 2 ? WAL : WAL2, 1.6 * s);
    }
  const clip =
    `<clipPath id="${cid}"><rect x="${box.x}" y="${box.y}" width="${box.w}" height="${box.h}"/></clipPath>` +
    (walnut && T
      ? `<defs>${walnutImage(id + '-shw', walnut)}${walnutAcross(T, id + '-shw')}</defs>`
      : '');
  const pelmet =
    wood(`M${pel.x},${pel.y} h${pel.w} v${pel.h} h${-pel.w}Z`, WAL2, 2.2 * s) +
    `<path d="M${pel.x + 4 * s},${pel.y + 6 * s} H${pel.x + pel.w - 4 * s}" stroke="${WALHI}" stroke-width="${2 * s}"/><path d="M${pel.x + 4 * s},${pel.y + pel.h - 6 * s} H${pel.x + pel.w - 4 * s}" stroke="#1b0f07" stroke-width="${2 * s}"/><rect x="${pel.x}" y="${pel.y + pel.h}" width="${pel.w}" height="${5 * s}" fill="#000" opacity=".3"/>`;
  return { clip, panel, stack, pelmet, cid };
}

/**
 * The shutter at rest: a blind that rolls up into a walnut pelmet above the frame (the vector
 * fallback: three louvred sections that concertina). Open, only the pelmet and the rolled-up
 * stack show, so the window by day and by night is the whole window; closed, the blind covers
 * the frame. The pelmet is part of the window at every hour.
 */
export function shutter(o: ShutterOpts): string {
  const g = geometry(o.hud ?? 'live', o.side ?? false),
    { clip, panel, stack, pelmet, cid } = shutterParts(g, o.id, o.walnut, o.picture);
  // the panel (clipped below the pelmet, so it comes from under it and goes back under it), then the stack, then the pelmet on top
  const d =
    clip +
    (o.state === 'closed' ? `<g clip-path="url(#${cid})">${panel}</g>` : stack) +
    pelmet;
  return `<svg viewBox="0 0 ${STAGE_W} ${STAGE_H}" xmlns="http://www.w3.org/2000/svg">${d}</svg>`;
}

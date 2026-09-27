/**
 * The dining car's window: the brass frame around the glass, and the louvred shutter that
 * covers it. The country behind the glass is not drawn here: it is felt pictures, one set per
 * hour, laid over the glass by the FeltWindow instrument.
 *
 * The window is its own module because two things draw it. The dining car paints the frame
 * and the glass as part of the wall. The shutter is painted separately, on top of the
 * car, because it sits in front of the room's own tint (in the benches it is a prop over
 * the backdrop, so the night's blue wash never falls on it) and because it is the one part
 * of the window that later moves: the shutter's motion will be an instrument that reuses
 * the geometry here. At rest it is either gathered up under its pelmet or down over the glass.
 *
 * Sources: the frame from the design kit (kits/stage-kit.js); the shutter
 * from the cover bench (revision 66), as the game-over bench (revision 73) draws it.
 */
import { geometry, STAGE_H, STAGE_W, type Hud, type StageGeometry } from '../units';
import { brass, inkP, K2, rnd, type Rect } from './draw';
import { CAR, type PhasePaint } from './materials';
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

/** The window's glass, in units: centred on the puppet, above the dado. */
export function windowRect(g: StageGeometry): Rect {
  const W = STAGE_W,
    H = STAGE_H,
    { dado } = carLines(g),
    x0 = 0,
    x1 = W;
  const ww = Math.min(0.5 * W, x1 - x0 - 0.3 * W),
    wx = g.cx - ww / 2,
    wy = 0.12 * H,
    wh = dado - 0.04 * H - wy;
  return [wx, wy, ww, wh];
}

/** Snow falling past the glass: two copies stacked so the loop has no seam. */
export const snowfall = (x: number, y: number, w: number, h: number, s: number): string => {
  let f = '';
  for (let i = 0; i < 40; i++)
    f += `<circle cx="${(x + rnd(i, 241) * w).toFixed(0)}" cy="${(y + rnd(i, 242) * h).toFixed(0)}" r="${((0.9 + rnd(i, 243) * 1.4) * s).toFixed(1)}" fill="#fff" fill-opacity=".8"/>`;
  return `<g class="sk-snw" style="--sh:${h.toFixed(0)}px">${f}<g transform="translate(0,${-Number(h.toFixed(0))})">${f}</g></g>`;
};

/* the window behind the puppet: brass, rounded corners, the blind rolled at the top, frost on the glass */
export function windowFrame(c: PhasePaint, rect: Rect, s: number): string {
  const [wx, wy, ww, wh] = rect,
    rr = 0.04 * STAGE_H;
  let d =
    `<rect x="${wx - 10 * s}" y="${wy - 10 * s}" width="${ww + 20 * s}" height="${wh + 20 * s}" rx="${rr + 8 * s}" fill="${CAR.brass}" stroke="${K2}" stroke-width="${2.2 * s}"/>` +
    // the glass: the felt country (FeltWindow) lies over it; the hour's sky shows until it loads
    `<rect x="${wx}" y="${wy}" width="${ww}" height="${wh}" rx="${rr}" fill="${c.skyTop}"/>`;
  d += `<rect x="${wx}" y="${wy}" width="${ww}" height="${wh}" rx="${rr}" fill="none" stroke="#2a180c" stroke-width="${3 * s}"/>`;
  for (const [kx, ky, dx, dy] of [
    [wx, wy, 1, 1],
    [wx + ww, wy, -1, 1],
    [wx, wy + wh, 1, -1],
    [wx + ww, wy + wh, -1, -1],
  ])
    d += `<path d="M${kx},${ky + dy * wh * 0.28} Q${kx + dx * ww * 0.06},${ky + dy * wh * 0.1} ${kx + dx * ww * 0.16},${ky}" fill="#fff" fill-opacity=".38"/>`;
  d += `<rect x="${wx - 4 * s}" y="${wy - 22 * s}" width="${ww + 8 * s}" height="${14 * s}" rx="${7 * s}" fill="#efe4cb" stroke="${K2}" stroke-width="${2 * s}"/><path d="M${wx + ww / 2},${wy - 8 * s} v${16 * s}" stroke="#2a180c" stroke-width="${2 * s}"/><circle cx="${wx + ww / 2}" cy="${wy + 12 * s}" r="${5 * s}" fill="none" stroke="${CAR.brass}" stroke-width="${2 * s}"/>`;
  d += `<rect x="${wx - 12 * s}" y="${wy + wh + 14 * s}" width="${ww + 24 * s}" height="${8 * s}" rx="${4 * s}" fill="${CAR.brass}" stroke="${K2}" stroke-width="${1.6 * s}"/>`;
  return d;
}

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
}

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
  return { f, pel, section: f.h / 3 };
}

/**
 * The shutter's pieces as markup, for the paint above and for the Shutter instrument that
 * moves them: the clip that hides the panel under the pelmet (id `<id>-shc`), the three-section
 * panel down over the frame, the folded stack edge-on under the pelmet, and the pelmet itself.
 * Given `walnut`, the wood is textured (the clip then also carries its pattern, `<id>-shx`).
 */
export function shutterParts(g: StageGeometry, id: string, walnut?: string) {
  const s = 1,
    { f, pel, section: h3 } = shutterGeometry(g, s),
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
  const panel =
    louvre(f.y, h3, true) +
    louvre(f.y + h3, h3, true) +
    louvre(f.y + 2 * h3, h3, false) +
    `<rect x="${f.cx - 14 * s}" y="${f.y + f.h - 12 * s}" width="${28 * s}" height="${5 * s}" rx="${2.5 * s}" fill="${brass}" stroke="${K2}" stroke-width="${s}"/>`;
  // the folded sections, edge on
  let stack = '';
  for (let i = 0; i < 3; i++)
    stack += wood(
      `M${f.x + 2 * s * i},${pel.y + pel.h - 2 * s + i * 7 * s} h${f.w - 4 * s * i} v${7 * s} h${-(f.w - 4 * s * i)}Z`,
      i % 2 ? WAL : WAL2,
      1.6 * s,
    );
  const clip =
    `<clipPath id="${cid}"><rect x="${pel.x}" y="${pel.y + pel.h - 2 * s}" width="${pel.w}" height="${f.h + 40 * s}"/></clipPath>` +
    (walnut && T
      ? `<defs>${walnutImage(id + '-shw', walnut)}${walnutAcross(T, id + '-shw')}</defs>`
      : '');
  const pelmet =
    wood(`M${pel.x},${pel.y} h${pel.w} v${pel.h} h${-pel.w}Z`, WAL2, 2.2 * s) +
    `<path d="M${pel.x + 4 * s},${pel.y + 6 * s} H${pel.x + pel.w - 4 * s}" stroke="${WALHI}" stroke-width="${2 * s}"/><path d="M${pel.x + 4 * s},${pel.y + pel.h - 6 * s} H${pel.x + pel.w - 4 * s}" stroke="#1b0f07" stroke-width="${2 * s}"/><rect x="${pel.x}" y="${pel.y + pel.h}" width="${pel.w}" height="${5 * s}" fill="#000" opacity=".3"/>`;
  return { clip, panel, stack, pelmet, cid };
}

/**
 * The louvred shutter at rest: three hinged sections that concertina up into a walnut pelmet
 * above the frame. Open, only the pelmet and the folded stack's edges show, so the window by
 * day and by night is the whole window; closed, the three sections cover the frame, a brass
 * pull on the bottom rail. The pelmet is part of the window at every hour.
 */
export function shutter(o: ShutterOpts): string {
  const g = geometry(o.hud ?? 'live', o.side ?? false),
    { clip, panel, stack, pelmet, cid } = shutterParts(g, o.id, o.walnut);
  // the panel (clipped below the pelmet, so it comes from under it and goes back under it), then the stack, then the pelmet on top
  const d =
    clip +
    (o.state === 'closed' ? `<g clip-path="url(#${cid})">${panel}</g>` : stack) +
    pelmet;
  return `<svg viewBox="0 0 ${STAGE_W} ${STAGE_H}" xmlns="http://www.w3.org/2000/svg">${d}</svg>`;
}

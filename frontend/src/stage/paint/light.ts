/**
 * The house lights: darkness over the stage everywhere except a soft pool where the action
 * is, the room's own glows (a lit lantern), and the specials, narrow spots from above on a
 * hung or wall-mounted prop.
 *
 * Light is how the stage says "this one": the chosen thing is lit and the rest dims, and
 * nothing moves to say it. So this overlay sits above the backdrop, the figures and the
 * instruments, and below the HUD. It is a dark sheet with soft holes cut in it.
 *
 * Ported from the design kit's `light()` (kits/stage-kit.js, VERSION 2026-09-23), which cut the
 * holes with an SVG mask of blurred shapes. No mask since 2026-10-01: iPhone Safari kills a page
 * that masks the whole stage (stage_architecture.md §6). The sheet is now one evenodd path with
 * the holes cut out, each hole filled from inside with a gradient of the sheet's dark, its
 * profile the blur the kit's shape had (`holes.ts`); where two holes overlap, the clearer wins,
 * with helper holes over the overlap bringing it near the mask's product.
 */
import { geometry, STAGE_H, STAGE_W, type Hud } from '../units';
import type { Glow, Special } from './draw';
import {
  blurredEllipse,
  concentric,
  holeGradient,
  scaled,
  softHoles,
  type Hole,
  type Profile,
} from './holes';

export interface Pool {
  x: number;
  y: number;
  rx: number;
  ry: number;
}

export interface LightOpts {
  /** Prefix for every id this drawing makes, so two stages can share a page. */
  id: string;
  hud?: Hud;
  side?: boolean;
  /** How dark the house is outside the pool, 0–100. */
  dark?: number;
  /** Where the default pool falls: on the puppet at the stand, or high on the stage ("over"). */
  from?: 'over' | 'stand';
  /** An explicit pool, in units; overrides `from`. */
  pool?: Pool;
  /** The backdrop's own glows and specials (from `diningCarPlan`), left open. */
  scene?: { glows: Glow[]; specials: Special[] };
  /** Extra glows and specials for this beat. */
  glows?: Glow[];
  specials?: Special[];
  /**
   * Lamps painted lit (the car's, `diningCarPlan().lamps`): each cut clean through the dark,
   * clear at its flame and soft only at its rim, with no blur, and warmed a little on top, so a
   * lamp is always the brightest, warmest thing in the room however dark the house is.
   */
  lamps?: Glow[];
  /** Units the darkness carries on past each side of the world, over the bleed (default 0). */
  bleed?: number;
}

/** How much warm light a lit lamp adds over its glass and the wall round it (screened), 0–1. */
const LAMP_WARMTH = 0.2;

/** The house's dark. */
const INK = '#0c0a07';

/** A lit lamp's hole: clear at the flame, soft only towards its rim, never blurred. */
const LAMP: Profile = [
  [0, 1],
  [0.4, 0.9],
  [1, 0],
];

/* where the pool falls: given, or on the puppet at the stand, or high over it */
function poolOf(o: LightOpts): Pool {
  const g = geometry(o.hud ?? 'live', o.side ?? false),
    p = g.pwid;
  return (
    o.pool ||
    (o.from === 'over'
      ? { x: g.cx, y: g.railY - p * 0.95, rx: p * 0.58, ry: p * 0.95 }
      : { x: g.cx, y: g.railY - p * 0.1, rx: p * 0.66, ry: p * 0.82 })
  );
}

/**
 * The holes the dark is cut with: the pool, the glows and the specials as soft as the kit's
 * blur (stdDeviation 0.16 of the puppet's width) left them, a special's rounded rect as the
 * ellipse in its box, and the lamps; a lamp and the glow on it are one hole.
 */
export function lightHoles(o: LightOpts): Hole[] {
  const g = geometry(o.hud ?? 'live', o.side ?? false),
    sc = o.scene ?? { glows: [], specials: [] },
    blur = g.pwid * 0.16;
  const glows = sc.glows.concat(o.glows || []),
    specials = sc.specials.concat(o.specials || []);
  return concentric([
    blurredEllipse(poolOf(o), blur),
    ...glows.map(([x, y, r, a]) => blurredEllipse({ x, y, rx: r, ry: r }, blur, Number(a))),
    ...specials.map(([x, y0, y1, rx, a]) =>
      blurredEllipse(
        { x, y: (y0 + y1 + rx * 0.6) / 2, rx, ry: (y1 - y0 + rx * 0.6) / 2 },
        blur,
        a,
      ),
    ),
    ...(o.lamps ?? []).map(([x, y, r, a]): Hole => ({
      x,
      y,
      rx: r,
      ry: r,
      clear: scaled(LAMP, Number(a)),
    })),
  ]);
}

/* darkness outside the pool; the room's glows and the specials left open */
export function light(o: LightOpts): string {
  const P = o.id + '-',
    W = STAGE_W,
    H = STAGE_H,
    dark = (o.dark == null ? 50 : o.dark) / 100,
    b = o.bleed ?? 0;
  const e = poolOf(o),
    lamps = o.lamps ?? [];
  // the sheet less its holes, then each hole's own piece, dark at its rim as the sheet is
  const { sheet, pieces } = softHoles(lightHoles(o), { x0: -b, y0: 0, x1: W + b, y1: H });
  const svg =
    `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0;width:100%;height:100%${b ? ';overflow:visible' : ''}"><defs>${pieces.map((q, i) => holeGradient(`${P}lh${i}`, q.hole, INK, dark)).join('')}</defs>` +
    `<path d="${sheet}" fill="${INK}" fill-opacity="${dark}" fill-rule="evenodd"/>` +
    pieces
      .map((q, i) => `<path d="${q.d}" fill="url(#${P}lh${i})" fill-rule="evenodd"/>`)
      .join('') +
    `</svg>`;
  // The two screened sheets are boxed to their gradients (clear beyond 70% of the radius, so
  // the pixels are the same): a screen blend is rendered through a surface the size of the
  // repaint, and a figure rising through a full-stage one paid for it every frame (build log §8.9).
  const R = Math.round,
    grx = e.rx * 0.9,
    gry = e.ry * 0.9;
  // whole-unit boxes, the gradient centred where it was: the same pixels as the full sheet
  const gl = R(e.x - grx),
    gt = R(e.y - gry);
  const glow = `<div style="position:absolute;left:${gl}px;top:${gt}px;width:${R(e.x + grx) - gl}px;height:${R(e.y + gry) - gt}px;mix-blend-mode:screen;background:radial-gradient(ellipse ${R(grx)}px ${R(gry)}px at ${R(e.x) - gl}px ${R(e.y) - gt}px, rgba(255,179,92,.16), rgba(255,179,92,0) 70%)"></div>`;
  // the lamps' warmth, one sheet round all the lamps, over the bleed too (a table lamp can
  // stand at the world's edge)
  const wl = R(Math.min(...lamps.map(([x, , r]) => x - r * 0.8))),
    wt = R(Math.min(...lamps.map(([, y, r]) => y - r * 0.8))),
    wr = R(Math.max(...lamps.map(([x, , r]) => x + r * 0.8))),
    wb = R(Math.max(...lamps.map(([, y, r]) => y + r * 0.8)));
  const warm = lamps.length
    ? `<div style="position:absolute;left:${wl}px;top:${wt}px;width:${wr - wl}px;height:${wb - wt}px;mix-blend-mode:screen;background:${lamps
        .map(
          ([x, y, r, a]) =>
            `radial-gradient(circle ${R(r * 0.8)}px at ${R(x) - wl}px ${R(y) - wt}px, rgba(255,179,92,${(LAMP_WARMTH * Number(a)).toFixed(2)}), rgba(255,179,92,0) 70%)`,
        )
        .join(',')}"></div>`
    : '';
  return svg + glow + warm;
}

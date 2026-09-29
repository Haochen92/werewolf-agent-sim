/**
 * The house lights: darkness over the stage everywhere except a soft pool where the action
 * is, the room's own glows (a lit lantern), and the specials, narrow spots from above on a
 * hung or wall-mounted prop.
 *
 * Light is how the stage says "this one": the chosen thing is lit and the rest dims, and
 * nothing moves to say it. So this overlay sits above the backdrop, the figures and the
 * instruments, and below the HUD. It is a mask: a dark sheet with soft holes cut in it.
 *
 * Ported from the design kit's `light()` (kits/stage-kit.js, VERSION 2026-09-23).
 */
import { geometry, STAGE_H, STAGE_W, type Hud } from '../units';
import type { Glow, Special } from './draw';

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

/* darkness outside the pool; the room's glows and the specials left open */
export function light(o: LightOpts): string {
  const g = geometry(o.hud ?? 'live', o.side ?? false);
  const P = o.id + '-',
    W = STAGE_W,
    H = STAGE_H,
    p = g.pwid,
    dark = (o.dark == null ? 50 : o.dark) / 100,
    b = o.bleed ?? 0,
    bx = b ? ` x="${-b}"` : '';
  const sc = o.scene ?? { glows: [], specials: [] };
  const e =
    o.pool ||
    (o.from === 'over'
      ? { x: g.cx, y: g.railY - p * 0.95, rx: p * 0.58, ry: p * 0.95 }
      : { x: g.cx, y: g.railY - p * 0.1, rx: p * 0.66, ry: p * 0.82 });
  const blur = p * 0.16,
    glows = sc.glows.concat(o.glows || []),
    specials = sc.specials.concat(o.specials || []),
    lamps = o.lamps ?? [];
  const svg =
    `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0;width:100%;height:100%${b ? ';overflow:visible' : ''}"><defs><filter id="${P}lbl" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="${blur.toFixed(0)}"/></filter>${lamps.length ? `<radialGradient id="${P}lamp"><stop offset="0" stop-color="#000"/><stop offset=".4" stop-color="#000" stop-opacity=".9"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>` : ''}<mask id="${P}lmask" maskUnits="userSpaceOnUse" x="${-b}" y="0" width="${W + 2 * b}" height="${H}"><rect${bx} width="${W + 2 * b}" height="${H}" fill="#fff"/><ellipse cx="${e.x.toFixed(0)}" cy="${e.y.toFixed(0)}" rx="${e.rx.toFixed(0)}" ry="${e.ry.toFixed(0)}" fill="#000" filter="url(#${P}lbl)"/>` +
    glows
      .map(
        ([x, y, r, a]) =>
          `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${r.toFixed(0)}" fill="#000" opacity="${a}" filter="url(#${P}lbl)"/>`,
      )
      .join('') +
    specials
      .map(
        ([x, y0, y1, rx, a]) =>
          `<rect x="${(x - rx).toFixed(0)}" y="${y0}" width="${(2 * rx).toFixed(0)}" height="${(y1 - y0 + rx * 0.6).toFixed(0)}" rx="${rx.toFixed(0)}" fill="#000" opacity="${a}" filter="url(#${P}lbl)"/>`,
      )
      .join('') +
    lamps
      .map(
        ([x, y, r, a]) =>
          `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${r.toFixed(0)}" fill="url(#${P}lamp)" opacity="${a}"/>`,
      )
      .join('') +
    `</mask></defs><rect${bx} width="${W + 2 * b}" height="${H}" fill="#0c0a07" opacity="${dark}" mask="url(#${P}lmask)"/></svg>`;
  const glow = `<div style="position:absolute;inset:0;mix-blend-mode:screen;background:radial-gradient(ellipse ${(e.rx * 0.9).toFixed(0)}px ${(e.ry * 0.9).toFixed(0)}px at ${e.x.toFixed(0)}px ${e.y.toFixed(0)}px, rgba(255,179,92,.16), rgba(255,179,92,0) 70%)"></div>`;
  // the lamps' warmth, over the bleed too (a table lamp can stand at the world's edge)
  const warm = lamps.length
    ? `<div style="position:absolute;top:0;left:${-b}px;width:${W + 2 * b}px;height:${H}px;mix-blend-mode:screen;background:${lamps
        .map(
          ([x, y, r, a]) =>
            `radial-gradient(circle ${(r * 0.8).toFixed(0)}px at ${(x + b).toFixed(0)}px ${y.toFixed(0)}px, rgba(255,179,92,${(LAMP_WARMTH * Number(a)).toFixed(2)}), rgba(255,179,92,0) 70%)`,
        )
        .join(',')}"></div>`
    : '';
  return svg + glow + warm;
}

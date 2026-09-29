/**
 * The atmosphere's paint: the one key light's strength at each hour, the shadow the shutter's
 * pelmet casts down and to the right of it, and the veil that sets the car's back wall back,
 * left open where a lamp is lit. The car is a painting whose frame and lamps carry their own
 * painted shadows, so only the pelmet drawn over it casts one here.
 *
 * The key light comes from the upper left, as the puppets' own pictures are lit. By day and
 * at the hour changes it warms the upper-left of the room a touch; at night the lamp leads, so
 * it all but goes out and leaves the room to the lamps' pools and the specials.
 *
 * The shadow is the long, soft one the key light throws, masked by the pelmet itself, so it only
 * ever lies on the wall. The night compartments have no such pieces; their veil is a plain gradient.
 */
import { BLEED, geometry, STAGE_H, STAGE_W, type Hud } from '../units';
import { diningCarPlan } from './dining-car';
import type { Phase } from './materials';
import { shutterGeometry } from './window';

/** How strongly the key light warms the upper left of the room, 0–1, by hour. */
export const KEY: Record<Phase, number> = { day: 1, dusk: 0.8, night: 0.3, dawn: 0.8 };

/** The shadows' ink: the wall's own darkest brown, not black. */
const INK = '#0c0704';

/** The veil over the back of the room: a warm dark, a little more towards the ceiling. */
export const VEIL = { color: '#1e130b', top: 0.15, mid: 0.1, bottom: 0.07 };

/** The window's shadow: how far it falls (x, y), how soft it is, and how dark. */
const CAST = {
  frame: { dx: 12, dy: 11, blur: 9, a: 0.42 },
} as const;

/**
 * The car's haze: its wall shadows, then the veil over the whole back of the room (and the
 * bleed past its sides), with a soft hole wherever a lamp is lit so the light stays forward.
 * Markup for a paint layer (drawn past the world's sides into the bleed); static, so its blur
 * is rasterised once, like the car's own cut-out shadows.
 */
export function carHaze(o: {
  /** Prefix for every id this drawing makes, so two stages can share a page. */
  id: string;
  phase: Phase;
  hud?: Hud;
  side?: boolean;
}): string {
  const hud = o.hud ?? 'live',
    side = o.side ?? false,
    H = STAGE_H,
    W = STAGE_W,
    b = BLEED,
    P = o.id + '-';
  // the pieces stand where they do at every hour; the glows are the hour's own
  const plan = diningCarPlan({ phase: o.phase, hud, side });
  // each piece's shape, in the colour given (the shadow's ink, or the mask's black)
  const pieces: { kind: keyof typeof CAST; shape: (ink: string) => string }[] = [];

  // the shutter's pelmet over the window (the painted frame below it has its own shadow)
  const { pel } = shutterGeometry(geometry(hud, side));
  pieces.push({
    kind: 'frame',
    shape: () => `<rect x="${pel.x}" y="${pel.y}" width="${pel.w}" height="${pel.h + 5}"/>`,
  });

  // the holes: each piece's own shape
  const holes = pieces.map((p) => p.shape('#000')).join('');
  let d = `<defs><mask id="${P}m" maskUnits="userSpaceOnUse" x="0" y="0" width="${W}" height="${H}"><rect width="${W}" height="${H}" fill="#fff"/><g fill="#000">${holes}</g></mask>`;
  // the veil's fall from ceiling to floor, and its lamps: a lit one's pool left clear
  const lit = plan.glows.filter(([, , , a]) => Number(a) >= 0.7);
  d += `<linearGradient id="${P}v" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${VEIL.color}" stop-opacity="${VEIL.top}"/><stop offset=".6" stop-color="${VEIL.color}" stop-opacity="${VEIL.mid}"/><stop offset="1" stop-color="${VEIL.color}" stop-opacity="${VEIL.bottom}"/></linearGradient><radialGradient id="${P}h"><stop offset="0" stop-color="#000"/><stop offset=".45" stop-color="#000" stop-opacity=".8"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>`;
  d += `<mask id="${P}l" maskUnits="userSpaceOnUse" x="${-b}" y="0" width="${W + 2 * b}" height="${H}"><rect x="${-b}" width="${W + 2 * b}" height="${H}" fill="#fff"/>${lit.map(([x, y, r, a]) => `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${(r * 1.1).toFixed(0)}" fill="url(#${P}h)" opacity="${Math.min(1, Number(a))}"/>`).join('')}</mask>`;
  for (const k of Object.keys(CAST) as (keyof typeof CAST)[])
    d += `<filter id="${P}b${k}" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="${CAST[k].blur}"/></filter>`;
  d += `</defs><g mask="url(#${P}m)">`;
  for (const p of pieces) {
    const s = CAST[p.kind];
    d += `<g filter="url(#${P}b${p.kind})" opacity="${s.a}"><g transform="translate(${s.dx},${s.dy})" fill="${INK}">${p.shape(INK)}</g></g>`;
  }
  d += `</g><rect x="${-b}" width="${W + 2 * b}" height="${H}" fill="url(#${P}v)" mask="url(#${P}l)"/>`;
  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${d}</svg>`;
}

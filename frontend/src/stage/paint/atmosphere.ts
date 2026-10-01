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
 * The shadow is the long, soft one the key light throws, clipped round the pelmet itself, so it
 * only ever lies on the wall. The night compartments have no such pieces; their veil is a plain
 * gradient.
 *
 * No SVG mask (2026-10-01; iPhone Safari kills a page that masks the stage, stage_architecture.md
 * §6): the shadow keeps its blur but is clipped (a clipPath, the stage less the pelmet), and the
 * veil is a sheet with the lit lamps' pools cut out, each pool filled from inside with the veil's
 * own colour, clear at the lamp and as dark as the veil at its rim (`holes.ts`).
 */
import { BLEED, geometry, STAGE_H, STAGE_W, type Hud } from '../units';
import { diningCarPlan } from './dining-car';
import { holeGradient, scaled, softHoles, type Hole, type Profile } from './holes';
import type { Phase } from './materials';
import { shutterGeometry } from './window';

/** How strongly the key light warms the upper left of the room, 0–1, by hour. */
export const KEY: Record<Phase, number> = { day: 1, dusk: 0.8, night: 0.3, dawn: 0.8 };

/** The shadows' ink: the wall's own darkest brown, not black. */
const INK = '#0c0704';

/** The veil over the back of the room: a warm dark, a little more towards the ceiling. */
export const VEIL = { color: '#1e130b', top: 0.15, mid: 0.1, bottom: 0.07 };

/** The veil's darkness at height y, as its gradient falls from the ceiling to the floor. */
const veilAt = (y: number) => {
  const t = y / STAGE_H;
  return t < 0.6
    ? VEIL.top + ((VEIL.mid - VEIL.top) * t) / 0.6
    : VEIL.mid + ((VEIL.bottom - VEIL.mid) * (t - 0.6)) / 0.4;
};

/** A lit lamp's pool in the veil: open at the lamp, fading out to its rim. */
const LIT: Profile = [
  [0, 1],
  [0.45, 0.8],
  [1, 0],
];

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
  // each piece's outline, as path data: its shadow is drawn from it, and the clip cut by it
  const pieces: { kind: keyof typeof CAST; outline: string }[] = [];

  // the shutter's pelmet over the window (the painted frame below it has its own shadow)
  const { pel } = shutterGeometry(geometry(hud, side));
  pieces.push({
    kind: 'frame',
    outline: `M${pel.x},${pel.y}h${pel.w}v${pel.h + 5}h${-pel.w}Z`,
  });

  // the clip: the stage less each piece, so a shadow never lies on what casts it
  let d = `<defs><clipPath id="${P}m" clipPathUnits="userSpaceOnUse"><path d="M0,0H${W}V${H}H0Z${pieces.map((p) => p.outline).join('')}" clip-rule="evenodd"/></clipPath>`;
  // the veil's fall from ceiling to floor, and its lamps: a lit one's pool left clear
  const lit = plan.glows.filter(([, , , a]) => Number(a) >= 0.7);
  d += `<linearGradient id="${P}v" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="${H}"><stop offset="0" stop-color="${VEIL.color}" stop-opacity="${VEIL.top}"/><stop offset=".6" stop-color="${VEIL.color}" stop-opacity="${VEIL.mid}"/><stop offset="1" stop-color="${VEIL.color}" stop-opacity="${VEIL.bottom}"/></linearGradient>`;
  const pools = softHoles(
    lit.map(([x, y, r, a]): Hole => ({
      x,
      y,
      rx: r * 1.1,
      ry: r * 1.1,
      clear: scaled(LIT, Math.min(1, Number(a))),
    })),
    { x0: -b, y0: 0, x1: W + b, y1: H },
  );
  // each pool's rim as dark as the veil at the lamp's height (the veil changes little across one)
  d += pools.pieces
    .map((q, i) => holeGradient(`${P}h${i}`, q.hole, VEIL.color, veilAt(q.hole.y)))
    .join('');
  for (const k of Object.keys(CAST) as (keyof typeof CAST)[])
    d += `<filter id="${P}b${k}" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="${CAST[k].blur}"/></filter>`;
  d += `</defs><g clip-path="url(#${P}m)">`;
  for (const p of pieces) {
    const s = CAST[p.kind];
    d += `<g filter="url(#${P}b${p.kind})" opacity="${s.a}"><g transform="translate(${s.dx},${s.dy})" fill="${INK}"><path d="${p.outline}"/></g></g>`;
  }
  d += `</g><path d="${pools.sheet}" fill="url(#${P}v)" fill-rule="evenodd"/>`;
  d += pools.pieces
    .map((q, i) => `<path d="${q.d}" fill="url(#${P}h${i})" fill-rule="evenodd"/>`)
    .join('');
  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${d}</svg>`;
}

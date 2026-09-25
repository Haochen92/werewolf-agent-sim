/**
 * The dining car: the day's backdrop, and the night lobby's.
 *
 * Walnut panels with a brass dado, the long rounded window on the country, a wall clock
 * hung on its string at the left, an iron lantern on its bracket at the right, the stage
 * floor with one seam and the trapdoor under the puppet. The hour changes the paint, not the
 * shapes: one set of shapes, four paints, and the room's light (a tint over the walls but
 * not the glass, a warm glow per lit source) follows the hour too.
 *
 * Ported from the design kit's `scene()` (kits/stage-kit.js, VERSION 2026-09-23) so that it
 * draws exactly what the kit draws; a test holds the two byte-for-byte equal. The only
 * change is that the wall clock can be left out, for when the WallClock instrument (which
 * carries the turn's red ring and the night's progress) hangs in its place.
 */
import { geometry, STAGE_H, STAGE_W, type Hud, type StageGeometry } from '../units';
import {
  beam,
  cutout,
  flameAt,
  inkP,
  K2,
  twine,
  type Glow,
  type Rect,
  type Special,
} from './draw';
import {
  BOARD,
  BOARD2,
  CAR,
  CLOCK,
  PHASES,
  ROOMLIGHT,
  type Phase,
  type PhasePaint,
} from './materials';
import { carLines, windowFrame, windowRect } from './window';

export interface DiningCarOpts {
  /** Prefix for every id this drawing makes, so two stages can share a page. */
  id: string;
  phase: Phase;
  hud?: Hud;
  /** The side slot is open: the room, the puppet and the window move left. */
  side?: boolean;
  /** How dark the house is, 0–100; only the specials' visible beams use it. */
  dark?: number;
  /** A flat veil over the whole backdrop, 0–100. */
  dim?: number;
  /** Draw the kit's wall clock (default). Off when the WallClock instrument hangs there instead. */
  wallClock?: boolean;
}

/** Where things are in the car, for the layers above it (the light, the floor, the instruments). */
export interface DiningCarPlan {
  /** Warm pools the light overlay leaves open: [x, y, r, strength]. */
  glows: Glow[];
  /** Narrow spots from above on each hung or wall-mounted prop. */
  specials: Special[];
  floor: { floorY: number; floorH: number; B: number; trap: Rect };
  /** The free wall either side of the window, [from, to] in x. */
  slots: { L: [number, number]; R: [number, number] };
  window: Rect;
  /** The wall clock's centre and radius, where the WallClock instrument hangs. */
  clock: { x: number; y: number; r: number } | null;
}

interface Ctx {
  P: string;
  phase: Phase;
  dark: number;
  specials: Special[];
  glows: Glow[];
  special: (x: number, y1: number, rx: number, a?: number, y0?: number) => void;
}
interface Shape {
  W: number;
  H: number;
  s: number;
  B: number;
  cx: number;
  pw: number;
  x0: number;
  x1: number;
  dado: number;
  floorY: number;
  floorH: number;
  winL?: number;
  winR?: number;
}
interface Part {
  d: string;
  emit: string;
  glows: Glow[];
  wins: Rect[];
}

function clockAt(
  ctx: Ctx,
  x: number,
  y: number,
  r: number,
  s: number,
  face = '#ecdfc3',
): string {
  const [hh, mm] = CLOCK[ctx.phase],
    ha = ((hh % 12) / 12) * 2 * Math.PI - Math.PI / 2,
    ma = ((mm % 60) / 60) * 2 * Math.PI - Math.PI / 2;
  return (
    `<circle cx="${x}" cy="${y}" r="${r}" fill="${face}" stroke="${K2}" stroke-width="${2 * s}"/><circle cx="${x}" cy="${y}" r="${r * 0.8}" fill="none" stroke="${K2}" stroke-width="${s}" stroke-dasharray="${1.2 * s} ${r * 0.8 * 0.5236 - 1.2 * s}"/>` +
    `<path d="M${x},${y} l${Math.cos(ha) * r * 0.5},${Math.sin(ha) * r * 0.5} M${x},${y} l${Math.cos(ma) * r * 0.72},${Math.sin(ma) * r * 0.72}" stroke="${K2}" stroke-width="${2.2 * s}" stroke-linecap="round"/><circle cx="${x}" cy="${y}" r="${1.8 * s}" fill="${K2}"/>`
  );
}

function carWindow(ctx: Ctx, sh: Shape, c: PhasePaint, rect: Rect): Part {
  const { s, W } = sh,
    [wx, wy, ww, wh] = rect;
  const d = windowFrame(ctx.P, ctx.phase, c, rect, s);
  sh.winL = wx - 0.02 * W;
  sh.winR = wx + ww + 0.02 * W;
  ctx.special(wx + ww / 2, wy + wh, ww * 0.55, 0.45);
  return { d: cutout(ctx.P, s, d, 1), emit: '', glows: [], wins: [rect] };
}

/* the right piece: an iron carriage lantern, six-sided, peaked roof and finial, on a scrolled bracket from a round plate */
function lantern(ctx: Ctx, sh: Shape, c: PhasePaint, slot: [number, number]): Part {
  const { s, H, W } = sh,
    x = (slot[0] + slot[1]) / 2,
    y = 0.3 * H,
    iron = '#1c1a18',
    glows: Glow[] = [];
  let d = '',
    emit = '';
  const px = x - 0.032 * W,
    py = y + 0.1 * H;
  d += `<circle cx="${px}" cy="${py}" r="${12 * s}" fill="${iron}" stroke="${K2}" stroke-width="${1.6 * s}"/><circle cx="${px}" cy="${py}" r="${5 * s}" fill="#3a3a3a"/><path d="M${px},${py} h${0.02 * W} q${0.02 * W},0 ${0.025 * W},${-0.04 * H} V${y + 0.03 * H}" fill="none" stroke="${iron}" stroke-width="${5 * s}" stroke-linecap="round"/><path d="M${px + 0.02 * W},${py} q${0.012 * W},${-0.01 * H} ${0.01 * W},${-0.03 * H}" fill="none" stroke="${iron}" stroke-width="${3 * s}" stroke-linecap="round"/>`;
  const bw = 0.042 * W,
    bh = 0.075 * H,
    bx = x - bw / 2,
    by = y - bh * 0.5;
  d += `<rect x="${bx - 6 * s}" y="${by + bh}" width="${bw + 12 * s}" height="${8 * s}" rx="${2 * s}" fill="${iron}" stroke="${K2}" stroke-width="${1.6 * s}"/>`;
  const glass = c.lit ? '#ffd27a' : '#f1e6c8',
    gop = c.lit ? 0.95 : 0.55;
  d += `<path d="M${bx - 8 * s},${by + 6 * s} L${bx},${by} V${by + bh} L${bx - 8 * s},${by + bh - 4 * s}Z" fill="${glass}" fill-opacity="${gop * 0.7}" stroke="${iron}" stroke-width="${2.2 * s}"/><path d="M${bx + bw + 8 * s},${by + 6 * s} L${bx + bw},${by} V${by + bh} L${bx + bw + 8 * s},${by + bh - 4 * s}Z" fill="${glass}" fill-opacity="${gop * 0.7}" stroke="${iron}" stroke-width="${2.2 * s}"/>`;
  d += `<rect x="${bx}" y="${by}" width="${bw}" height="${bh}" fill="${glass}" fill-opacity="${gop}" stroke="${iron}" stroke-width="${2.4 * s}"/><path d="M${bx + bw / 2},${by} V${by + bh}" stroke="${iron}" stroke-width="${1.6 * s}" stroke-opacity=".6"/>`;
  d +=
    inkP(
      `M${bx - 12 * s},${by} L${x},${by - bh * 0.45} L${bx + bw + 12 * s},${by}Z`,
      iron,
      2 * s,
    ) +
    `<rect x="${x - 3 * s}" y="${by - bh * 0.62}" width="${6 * s}" height="${bh * 0.2}" fill="${iron}"/><circle cx="${x}" cy="${by - bh * 0.66}" r="${4 * s}" fill="${iron}" stroke="${K2}" stroke-width="${1.2 * s}"/>`;
  ctx.special(x, by + bh, 0.055 * W, 0.85);
  const hid = ctx.P + 'lh' + Math.round(x),
    halo = c.lit ? 0.34 : 0.1,
    rr = c.lit ? 0.26 * H : 0.09 * H;
  emit += `<defs><radialGradient id="${hid}" cx="${x}" cy="${y}" r="${rr.toFixed(0)}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ffd27a" stop-opacity="${halo}"/><stop offset=".35" stop-color="#ffb35c" stop-opacity="${(halo * 0.5).toFixed(2)}"/><stop offset="1" stop-color="#ffb35c" stop-opacity="0"/></radialGradient></defs><circle cx="${x}" cy="${y}" r="${rr.toFixed(0)}" fill="url(#${hid})"/>`;
  if (c.lit) {
    emit +=
      `<path d="M${x - bw * 0.7},${by + bh} L${x - 0.11 * W},${sh.floorY} H${x + 0.11 * W} L${x + bw * 0.7},${by + bh}Z" fill="#ffb35c" opacity=".09"/>` +
      flameAt(x, y + 0.005 * H, 1.2 * s);
    glows.push([x, y, 0.3 * H, '#ffb35c']);
  } else glows.push([x, y, 0.06 * H, '#ffb35c']);
  return { d: cutout(ctx.P, s, d, 1), emit, glows, wins: [] };
}

function wallClockAt(sh: Shape, slot: [number, number]) {
  const { H } = sh,
    x = (slot[0] + slot[1]) / 2,
    y = 0.3 * H,
    r = Math.min(0.085 * H, (slot[1] - slot[0]) * 0.48);
  return { x, y, r };
}

/* the left piece: a wall clock hung by its ring on a long string from above, keeping the phase's time */
function wallClock(ctx: Ctx, sh: Shape, slot: [number, number]): Part {
  const { s, H } = sh,
    { x, y, r } = wallClockAt(sh, slot);
  let d = '';
  ctx.special(x, y + r, r * 1.35);
  d +=
    twine(x, 0, x, y - r - 0.03 * H, s) +
    `<circle cx="${x}" cy="${y - r - 0.018 * H}" r="${8 * s}" fill="none" stroke="${CAR.brass}" stroke-width="${3 * s}"/><rect x="${x - 5 * s}" y="${y - r - 0.01 * H}" width="${10 * s}" height="${0.012 * H}" fill="${CAR.brass}" stroke="${K2}" stroke-width="${1.2 * s}"/>`;
  d +=
    `<circle cx="${x}" cy="${y}" r="${r}" fill="${CAR.brass}" stroke="${K2}" stroke-width="${2.4 * s}"/>` +
    clockAt(ctx, x, y, r * 0.8, s);
  for (let k = 0; k < 12; k++) {
    const a = (k / 12) * Math.PI * 2;
    d += `<circle cx="${(x + Math.cos(a) * r * 0.66).toFixed(1)}" cy="${(y + Math.sin(a) * r * 0.66).toFixed(1)}" r="${(k % 3 ? 1.4 : 2.4) * s}" fill="${K2}"/>`;
  }
  return {
    d: `<g class="sk-hang">${cutout(ctx.P, s, d, 1)}</g>`,
    emit: '',
    glows: [],
    wins: [],
  };
}

function roomLight(
  ctx: Ctx,
  f: { W: number; H: number },
  wins: Rect[],
  glows: Glow[],
): string {
  const Lt = ROOMLIGHT[ctx.phase],
    P = ctx.P;
  let d = '';
  ctx.glows = glows.map(([x, y, r]) => [x, y, r * 0.55, Lt.glow]);
  if (Lt.tint)
    d += `<defs><mask id="${P}rmask" maskUnits="userSpaceOnUse" x="0" y="0" width="${f.W}" height="${f.H}"><rect width="${f.W}" height="${f.H}" fill="#fff"/>${wins.map(([x, y, w, h]) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="#000"/>`).join('')}</mask></defs>
      <rect width="${f.W}" height="${f.H}" fill="${Lt.tint}" opacity="${Lt.a}" mask="url(#${P}rmask)" style="mix-blend-mode:multiply"/>`;
  d += `<defs>${glows.map(([, , , col], i) => `<radialGradient id="${P}rg${i}"><stop offset="0" stop-color="${col}" stop-opacity=".55"/><stop offset=".4" stop-color="${col}" stop-opacity=".18"/><stop offset="1" stop-color="${col}" stop-opacity="0"/></radialGradient>`).join('')}</defs>`;
  d += glows
    .map(
      ([x, y, r], i) =>
        `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${r.toFixed(0)}" fill="url(#${P}rg${i})" opacity="${Lt.glow}" style="mix-blend-mode:screen"/>`,
    )
    .join('');
  d += ctx.specials.map(([x, y0, y1, rx]) => beam(x, y0, y1, rx, ctx.dark)).join('');
  return d;
}

function build(o: DiningCarOpts): { html: string; plan: DiningCarPlan } {
  const g: StageGeometry = geometry(o.hud ?? 'live', o.side ?? false);
  const P = o.id + '-',
    c = PHASES[o.phase],
    W = STAGE_W,
    H = STAGE_H,
    s = 1,
    B = g.railY,
    cx = g.cx,
    pw = g.pwid;
  const ctx: Ctx = {
    P,
    phase: o.phase,
    dark: o.dark == null ? 50 : o.dark,
    specials: [],
    glows: [],
    special: (x, y1, rx, a = 0.9, y0 = 0) => ctx.specials.push([x, y0, y1, rx, a]),
  };
  const { floorH, floorY, dado } = carLines(g);
  let d = `<defs><filter id="${P}shadf" x="-10%" y="-10%" width="120%" height="120%"><feFlood flood-color="#000" flood-opacity=".5"/><feComposite in2="SourceAlpha" operator="in"/><feGaussianBlur stdDeviation="${(5 * s).toFixed(1)}"/></filter>
      <filter id="${P}grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="7" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="linear" slope=".55"/></feComponentTransfer></filter>
      <linearGradient id="${P}qfade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#0c0a07" stop-opacity=".95"/><stop offset=".12" stop-color="#0c0a07" stop-opacity="0"/><stop offset=".88" stop-color="#0c0a07" stop-opacity="0"/><stop offset="1" stop-color="#0c0a07" stop-opacity=".95"/></linearGradient></defs>`;
  d += `<rect width="${W}" height="${H}" fill="#0c0a07"/>`;
  // the back flat: walnut, its panel lines, the dado and its brass rail; hazed toward one value, its ends fading into the dark
  d += `<rect x="0" y="0" width="${W}" height="${floorY}" fill="${CAR.wall}"/>`;
  for (let px = 0; px < W; px += 0.08 * W)
    d += `<path d="M${px.toFixed(0)},0 V${dado}" stroke="${CAR.wallDark}" stroke-width="${4 * s}"/>`;
  d += `<rect x="0" y="${dado}" width="${W}" height="${floorY - dado}" fill="${CAR.dado}"/><rect x="0" y="${dado - 4 * s}" width="${W}" height="${8 * s}" fill="${CAR.brass}" stroke="${K2}" stroke-width="${1.4 * s}"/>`;
  d += `<rect x="0" y="0" width="${W}" height="${floorY}" fill="${CAR.wallDark}" opacity=".38"/><rect x="0" y="0" width="${W}" height="${floorY}" fill="url(#${P}qfade)"/>`;
  // the stage floor: boards with one seam, and the trapdoor under the puppet (a seam and a hinge line; its front edge hidden by the stand)
  d += `<rect x="0" y="${floorY}" width="${W}" height="${floorH}" fill="${BOARD}"/><path d="M0,${(floorY + floorH / 2).toFixed(0)} H${W}" stroke="${BOARD2}" stroke-width="${1.6 * s}" opacity=".7"/><rect x="0" y="${floorY}" width="${W}" height="${floorH}" fill="url(#${P}qfade)"/>`;
  const tw = pw * 0.9,
    tx = cx - tw / 2,
    ty = floorY + floorH * 0.3;
  d += `<rect x="${tx}" y="${ty}" width="${tw}" height="${B - ty}" fill="${BOARD}" stroke="#2a1a0c" stroke-width="${2.4 * s}"/><path d="M${tx + 10 * s},${ty + 6 * s} H${tx + tw - 10 * s}" stroke="#2a1a0c" stroke-width="${2 * s}"/>`;
  const sh: Shape = { W, H, s, B, cx, pw, x0: 0, x1: W, dado, floorY, floorH };
  const edge = 0.03 * W,
    slotL: [number, number] = [edge, cx - pw * 0.55 - 0.02 * W],
    slotR: [number, number] = [cx + pw * 0.55 + 0.02 * W, W - edge];
  const win = windowRect(g);
  const parts = [carWindow(ctx, sh, c, win)];
  slotL[1] = Math.min(slotL[1], sh.winL!);
  slotR[0] = Math.max(slotR[0], sh.winR!);
  let clock: DiningCarPlan['clock'] = null;
  if (slotL[1] - slotL[0] > 0.06 * W) {
    clock = wallClockAt(sh, slotL);
    // without the kit's clock, its special still marks the spot the instrument hangs in
    if (o.wallClock === false) ctx.special(clock.x, clock.y + clock.r, clock.r * 1.35);
    else parts.push(wallClock(ctx, sh, slotL));
  }
  if (slotR[1] - slotR[0] > 0.06 * W) parts.push(lantern(ctx, sh, c, slotR));
  const wins: Rect[] = [],
    glows: Glow[] = [];
  let emit = '';
  for (const p of parts) {
    d += p.d;
    emit += p.emit;
    glows.push(...p.glows);
    wins.push(...p.wins);
  }
  d += roomLight(ctx, { W, H }, wins, glows) + emit;
  d += `<rect width="${W}" height="${H}" fill="#fff" filter="url(#${P}grain)" opacity=".1" style="mix-blend-mode:overlay"/>`;
  const dim = o.dim == null ? 10 : o.dim;
  return {
    html: `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">${d}</svg><div style="position:absolute;inset:0;background:#0c0a07;opacity:${dim / 100}"></div>`,
    plan: {
      glows: ctx.glows,
      specials: ctx.specials,
      floor: { floorY, floorH, B, trap: [tx, ty, tw, B - ty] },
      slots: { L: slotL, R: slotR },
      window: parts[0].wins[0],
      clock,
    },
  };
}

/** The dining car at an hour, as SVG markup (plus the veil) for a paint layer. */
export function diningCar(o: DiningCarOpts): string {
  return build(o).html;
}

/** The car's layout: where its glows, specials, floor, window and clock are. No markup. */
export function diningCarPlan(o: Omit<DiningCarOpts, 'id'>): DiningCarPlan {
  return build({ ...o, id: 'plan' }).plan;
}

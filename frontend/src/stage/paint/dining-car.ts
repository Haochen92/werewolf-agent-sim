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
 * draws exactly what the kit draws; a test holds the two byte-for-byte equal. Two changes: the
 * glass is a plain fill of the hour's sky, with no vector country, because the felt pictures
 * (FeltWindow) lie over it; and the wall clock and the lantern are not drawn, because they are
 * painted pictures now (WallClock, WallLamp) hung where the plan says. Their specials, the
 * lantern's halo and pool and the room's glows are still the car's. Given `wood`, the walls
 * and the floor are painted material rather than flat (paint/texture.ts), in the same shapes.
 */
import { geometry, STAGE_H, STAGE_W, type Hud, type StageGeometry } from '../units';
import { beam, cutout, K2, type Glow, type Rect, type Special } from './draw';
import {
  BOARD,
  BOARD2,
  CAR,
  PHASES,
  ROOMLIGHT,
  type Phase,
  type PhasePaint,
} from './materials';
import { boards, DARKER, veneer, walnutAcross, walnutImage, type Wood } from './texture';
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
  /** The walls' walnut and the floor's boards; without them the car is flat, as the kit draws it. */
  wood?: Wood;
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
  /** The lantern's glass box and its bracket's wall plate, where WallLamp hangs the picture. */
  lamp: ReturnType<typeof lanternBox> | null;
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

function carWindow(ctx: Ctx, sh: Shape, c: PhasePaint, rect: Rect): Part {
  const { s, W } = sh,
    [wx, wy, ww, wh] = rect;
  const d = windowFrame(c, rect, s);
  sh.winL = wx - 0.02 * W;
  sh.winR = wx + ww + 0.02 * W;
  ctx.special(wx + ww / 2, wy + wh, ww * 0.55, 0.45);
  return { d: cutout(ctx.P, s, d, 1), emit: '', glows: [], wins: [rect] };
}

/* where the lantern hangs in its slot: its centre, its glass box, its bracket's plate */
function lanternBox(sh: Pick<Shape, 'H' | 'W'>, slot: [number, number]) {
  const { H, W } = sh,
    x = (slot[0] + slot[1]) / 2,
    y = 0.3 * H,
    bw = 0.042 * W,
    bh = 0.075 * H;
  return {
    x,
    y,
    bw,
    bh,
    bx: x - bw / 2,
    by: y - bh * 0.5,
    px: x - 0.032 * W,
    py: y + 0.1 * H,
  };
}

/* the right piece: the lantern (a picture, WallLamp) — its special, its halo and, lit, its pool on the floor */
function lantern(ctx: Ctx, sh: Shape, c: PhasePaint, slot: [number, number]): Part {
  const { H, W } = sh,
    { x, y, bw, bh, by } = lanternBox(sh, slot),
    glows: Glow[] = [];
  let emit = '';
  ctx.special(x, by + bh, 0.055 * W, 0.85);
  const hid = ctx.P + 'lh' + Math.round(x),
    halo = c.lit ? 0.34 : 0.1,
    rr = c.lit ? 0.26 * H : 0.09 * H;
  emit += `<defs><radialGradient id="${hid}" cx="${x}" cy="${y}" r="${rr.toFixed(0)}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ffd27a" stop-opacity="${halo}"/><stop offset=".35" stop-color="#ffb35c" stop-opacity="${(halo * 0.5).toFixed(2)}"/><stop offset="1" stop-color="#ffb35c" stop-opacity="0"/></radialGradient></defs><circle cx="${x}" cy="${y}" r="${rr.toFixed(0)}" fill="url(#${hid})"/>`;
  if (c.lit) {
    emit += `<path d="M${x - bw * 0.7},${by + bh} L${x - 0.11 * W},${sh.floorY} H${x + 0.11 * W} L${x + bw * 0.7},${by + bh}Z" fill="#ffb35c" opacity=".09"/>`;
    glows.push([x, y, 0.3 * H, '#ffb35c']);
  } else glows.push([x, y, 0.06 * H, '#ffb35c']);
  return { d: '', emit, glows, wins: [] };
}

function wallClockAt(sh: Shape, slot: [number, number]) {
  const { H } = sh,
    x = (slot[0] + slot[1]) / 2,
    y = 0.3 * H,
    r = Math.min(0.085 * H, (slot[1] - slot[0]) * 0.48);
  return { x, y, r };
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
  // the textures: veneered panels between the panel lines, the dado's grain across, the boards' seams on the floor's
  const tex = o.wood
    ? {
        wall: `url(#${P}wal)`,
        dado: `url(#${P}wald)`,
        dadoVeil: `<rect x="0" y="${dado}" width="${W}" height="${floorY - dado}" fill="#000" opacity="${DARKER['#3a2212']}"/>`,
        board: `url(#${P}brd)`,
      }
    : null;
  if (o.wood)
    d += `<defs>${walnutImage(P + 'wimg', o.wood.walnut)}${veneer(P + 'wal', P + 'wimg', 0, 0.08 * W)}${walnutAcross(P + 'wald', P + 'wimg')}${boards(P + 'brd', o.wood.boards, floorY, floorH / 2)}</defs>`;
  d += `<rect width="${W}" height="${H}" fill="#0c0a07"/>`;
  // the back flat: walnut, its panel lines, the dado and its brass rail; hazed toward one value, its ends fading into the dark
  d += `<rect x="0" y="0" width="${W}" height="${floorY}" fill="${tex?.wall ?? CAR.wall}"/>`;
  for (let px = 0; px < W; px += 0.08 * W)
    d += `<path d="M${px.toFixed(0)},0 V${dado}" stroke="${CAR.wallDark}" stroke-width="${4 * s}"/>`;
  d += `<rect x="0" y="${dado}" width="${W}" height="${floorY - dado}" fill="${tex?.dado ?? CAR.dado}"/>${tex?.dadoVeil ?? ''}<rect x="0" y="${dado - 4 * s}" width="${W}" height="${8 * s}" fill="${CAR.brass}" stroke="${K2}" stroke-width="${1.4 * s}"/>`;
  d += `<rect x="0" y="0" width="${W}" height="${floorY}" fill="${CAR.wallDark}" opacity=".38"/><rect x="0" y="0" width="${W}" height="${floorY}" fill="url(#${P}qfade)"/>`;
  // the stage floor: boards with one seam, and the trapdoor under the puppet (a seam and a hinge line; its front edge hidden by the stand)
  d += `<rect x="0" y="${floorY}" width="${W}" height="${floorH}" fill="${tex?.board ?? BOARD}"/><path d="M0,${(floorY + floorH / 2).toFixed(0)} H${W}" stroke="${BOARD2}" stroke-width="${1.6 * s}" opacity=".7"/><rect x="0" y="${floorY}" width="${W}" height="${floorH}" fill="url(#${P}qfade)"/>`;
  const tw = pw * 0.9,
    tx = cx - tw / 2,
    ty = floorY + floorH * 0.3;
  d += `<rect x="${tx}" y="${ty}" width="${tw}" height="${B - ty}" fill="${tex?.board ?? BOARD}" stroke="#2a1a0c" stroke-width="${2.4 * s}"/><path d="M${tx + 10 * s},${ty + 6 * s} H${tx + tw - 10 * s}" stroke="#2a1a0c" stroke-width="${2 * s}"/>`;
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
    // the clock is a picture (WallClock); its special still marks the spot it hangs in
    clock = wallClockAt(sh, slotL);
    ctx.special(clock.x, clock.y + clock.r, clock.r * 1.35);
  }
  const lamp = slotR[1] - slotR[0] > 0.06 * W ? lanternBox(sh, slotR) : null;
  if (lamp) parts.push(lantern(ctx, sh, c, slotR));
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
      lamp,
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

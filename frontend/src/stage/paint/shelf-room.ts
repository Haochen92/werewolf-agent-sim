/**
 * The acting seat's room at night, seen from its own chair.
 *
 * Bare walnut panelling, no window and no lamp: a wall shelf across the upper half on three
 * dark iron brackets, walnut on its face, and below it a row of plain nails with short lengths
 * of dark twine, one per other seat. The role card, the kit and the plush dolls are
 * instruments that stand on the shelf and hang from the nails; this file draws only the room
 * they are placed in, and says where the shelf and the nails are so they can be placed.
 *
 * Also here: the room's lighting, because it is particular to the room. It is night and the
 * room is dark but for one candle: its warm pool falls on the dolls and the shelf's front
 * edge, and the walls and the room's edges sink into shadow. When a doll is chosen the room
 * below the shelf goes darker still, and one light finds that doll.
 *
 * Ported from the shelf bench (revision 70), with the role card framed on the shelf and no
 * lamp, as agreed there. Given `wood`, the panels, the cornice, the shelf's face and the floor
 * are painted material (paint/texture.ts) in the same shapes; without it, flat.
 */
import { geometry, STAGE_H, STAGE_W, type Hud } from '../units';
import { BOARD, brass, K2 } from './draw';
import { boards, DARKER, veneer, walnutAcross, walnutImage, type Wood } from './texture';

const WALLO = '#2a170b';
/* the brackets' and the nails' dull iron, and the twine's brown-black: nothing under the shelf glints */
const IRON = '#3b2c20',
  NAIL = '#120b07',
  TWINE = '#140d08';

export interface ShelfRoomOpts {
  /** Prefix for every id this drawing makes, so two stages can share a page. */
  id: string;
  hud?: Hud;
  /** How many nails hang under the shelf (the bench hangs one per living seat but yours). */
  hooks?: number;
  /** The side slot is open: the shelf and its hooks keep to the narrower room at the left. */
  side?: boolean;
  /** The walnut (the panels, the cornice, the shelf's face) and the boards (the floor). */
  wood?: Wood;
}

/** The shelf and its nails in units, for placing the card, the kit and the dolls. */
export function shelfPlan(o: { hud?: Hud; hooks?: number; side?: boolean } = {}) {
  const g = geometry(o.hud ?? 'live', o.side ?? false),
    H = STAGE_H,
    s = 1;
  // the room right of the wing: the whole of it, or what the open side slot leaves
  const room = g.room,
    cx = g.wingN + room / 2;
  const x0 = g.wingN + room * 0.06,
    x1 = g.wingN + room - room * 0.06,
    top = 0.42 * H,
    face = 0.055 * H,
    depth = 0.03 * H;
  const n = o.hooks ?? 8,
    x0r = x0 + (x1 - x0) * 0.04,
    spanR = (x1 - x0) * 0.92;
  const strTop = top + face,
    strLen = 0.07 * H;
  return {
    room,
    cx,
    x0,
    x1,
    top,
    face,
    depth,
    /** Where things stand on the shelf: on its top face, a little behind the front edge. */
    foot: top - depth * 0.35,
    /** Below this line the room dims on a choice; above it the shelf stays lit. */
    cut: top + face + 2 * s,
    /** The role card's frame and the role's kit: two things, a quarter in from each end. */
    cardX: x0 + (x1 - x0) * 0.25,
    kitX: x0 + (x1 - x0) * 0.75,
    /** Their heights (bench 70: the card 0.31 of the stage's height, the kit 0.19). */
    cardH: 0.31 * H,
    kitH: 0.19 * H,
    /** Each nail's twine: x, where it leaves the shelf, where the doll's crown meets it. */
    hooks: Array.from({ length: n }, (_, i) => ({
      x: x0r + (spanR * (i + 0.5)) / n,
      top: strTop,
      end: strTop + strLen,
    })),
    /** A hung doll's width; its head's top meets the string at `end + 2`. */
    dollW: Math.min(0.085 * STAGE_W, (spanR / n) * 0.9),
  };
}

/* the wall: panels, cornice, a dado, the floor at the bottom */
function wall(wingN: number, P?: string): string {
  return panelling(wingN, STAGE_W, 7, undefined, P);
}

/**
 * The panelling's textures (defs), for `panelling` with the same prefix: a veneer window per
 * panel, `x0` a panel's left edge and `pw` its width; the grain across for the cornice and the
 * shelf; the floor's boards, two to the strip below the wall.
 */
export function shelfTextures(P: string, wood: Wood, x0: number, pw: number): string {
  return `<defs>${walnutImage(P + 'wimg', wood.walnut)}${veneer(P + 'wal', P + 'wimg', x0, pw)}${walnutAcross(P + 'walx', P + 'wimg')}${boards(P + 'brd', wood.boards, 0.92 * STAGE_H, 0.04 * STAGE_H)}</defs>`;
}

/**
 * The room's panelled wall from x0 to W, in n panels: the cornice, the dado, the floor at the
 * bottom. The bleed (bleed.ts) draws the same wall on past the room's sides. `P` names the
 * textures `shelfTextures` defined; without it, flat.
 */
export function panelling(
  x0: number,
  W: number,
  n: number,
  pw = (W - x0) / n,
  P?: string,
): string {
  const H = STAGE_H,
    s = 1,
    room = W - x0,
    corn = 0.06 * H,
    dado = 0.84 * H,
    floorY = 0.92 * H;
  let d = P
    ? `<rect x="${x0}" y="0" width="${room}" height="${H}" fill="url(#${P}wal)"/><rect x="${x0}" y="0" width="${room}" height="${H}" fill="#000" opacity="${DARKER['#3a2212']}"/>`
    : `<rect x="${x0}" y="0" width="${room}" height="${H}" fill="#3a2212"/>`;
  for (let i = 0; i < n; i++) {
    const px = x0 + i * pw;
    d += `<rect x="${px + 8 * s}" y="${corn + 14 * s}" width="${pw - 16 * s}" height="${dado - corn - 28 * s}" fill="none" stroke="#6a4a2a" stroke-width="${2 * s}"/><rect x="${px + 14 * s}" y="${corn + 20 * s}" width="${pw - 28 * s}" height="${dado - corn - 40 * s}" fill="${WALLO}" opacity=".35"/>`;
  }
  d += `<rect x="${x0}" y="0" width="${room}" height="${corn}" fill="${P ? `url(#${P}walx)` : '#4a2c18'}"/><path d="M${x0},${corn} H${W}" stroke="${K2}" stroke-width="${3 * s}"/><path d="M${x0},${corn - 8 * s} H${W}" stroke="#6a4a2a" stroke-width="${3 * s}"/>`;
  d += `<path d="M${x0},${dado} H${W}" stroke="${K2}" stroke-width="${4 * s}"/><path d="M${x0},${dado} H${W}" stroke="${brass}" stroke-width="${2.4 * s}"/>`;
  d += `<rect x="${x0}" y="${floorY}" width="${room}" height="${H - floorY}" fill="${P ? `url(#${P}brd)` : BOARD}"/><path d="M${x0},${floorY} H${W}" stroke="${K2}" stroke-width="${3 * s}"/><rect x="${x0}" y="${floorY}" width="${room}" height="${H - floorY}" fill="#0c0a07" opacity=".25"/>`;
  return d;
}

/* the shelf: a walnut board across the upper half on three iron brackets; its top face shows a little, its front edge shows the wood */
function shelf(S: ReturnType<typeof shelfPlan>): string {
  const s = 1,
    H = STAGE_H,
    { x0, x1, top, face, depth } = S;
  let d = '';
  // brackets
  for (const bx of [x0 + (x1 - x0) * 0.08, x0 + (x1 - x0) * 0.5, x0 + (x1 - x0) * 0.92])
    d += `<path d="M${bx},${top + face} q0,${0.07 * H} ${-0.045 * H},${0.075 * H}" fill="none" stroke="${K2}" stroke-width="${6 * s}"/><path d="M${bx},${top + face} q0,${0.07 * H} ${-0.045 * H},${0.075 * H}" fill="none" stroke="${IRON}" stroke-width="${3.5 * s}"/><path d="M${bx - 0.045 * H},${top + face + 0.075 * H} h${0.03 * H} q${0.01 * H},${-0.03 * H} ${0.015 * H},${-0.06 * H}" fill="none" stroke="${K2}" stroke-width="${2.6 * s}"/>`;
  // the top face (a sliver, lit) and the front edge (textured by the wood tile beneath; here the ink and the shade)
  d += `<path d="M${x0 + 0.012 * H},${top - depth} H${x1 - 0.012 * H} L${x1},${top} H${x0}Z" fill="#7a5230"/><path d="M${x0 + 0.012 * H},${top - depth} H${x1 - 0.012 * H} L${x1},${top} H${x0}Z" fill="none" stroke="${K2}" stroke-width="${2 * s}"/>`;
  d += `<rect x="${x0}" y="${top}" width="${x1 - x0}" height="${face}" fill="none" stroke="${K2}" stroke-width="${2.4 * s}"/><path d="M${x0},${top + face * 0.85} H${x1}" stroke="#000" stroke-opacity=".35" stroke-width="${face * 0.3}"/>`;
  d += `<path d="M${x0},${top + face} H${x1}" stroke="#000" stroke-opacity=".4" stroke-width="${6 * s}" transform="translate(0,${3 * s})"/>`; // its shadow on the wall
  return d;
}

/* a plain nail in the wall just under the shelf, and the doll's twine hanging from it to `end` */
function nail(x: number, y: number, end: number): string {
  const s = 1;
  return `<path d="M${x},${y} V${end}" stroke="${TWINE}" stroke-width="${2.2 * s}"/><path d="M${x - 0.6 * s},${y + 3 * s} V${end}" stroke="#8a6a50" stroke-opacity=".3" stroke-width="${0.6 * s}"/><circle cx="${x}" cy="${y}" r="${3.8 * s}" fill="${NAIL}"/><path d="M${x - 2.2 * s},${y - 1.6 * s} a${2.6 * s},${2.6 * s} 0 0 1 ${3.2 * s},${-1 * s}" fill="none" stroke="#6b5443" stroke-opacity=".5" stroke-width="${0.8 * s}"/>`;
}

/** The shelf room, as SVG markup for a paint layer. */
export function shelfRoom(o: ShelfRoomOpts): string {
  const g = geometry(o.hud ?? 'live'),
    S = shelfPlan(o),
    s = 1,
    H = STAGE_H,
    P = o.id + '-';
  let d = o.wood ? shelfTextures(P, o.wood, g.wingN, (STAGE_W - g.wingN) / 7) : '';
  d += wall(g.wingN, o.wood ? P : undefined);
  // the face's wood: the wall's walnut with its grain along the board
  const fx = Number(S.x0.toFixed(0)),
    fy = Number(S.top.toFixed(0)),
    fw = Number((S.x1 - S.x0).toFixed(0)),
    fh = Number(S.face.toFixed(0));
  if (o.wood)
    d += `<rect x="${fx}" y="${fy}" width="${fw}" height="${fh}" fill="url(#${P}walx)" opacity=".95"/>`;
  else
    d += `<rect x="${fx}" y="${fy}" width="${fw}" height="${fh}" fill="${BOARD}" opacity=".95"/>`;
  d += shelf(S);
  // a nail under the shelf for each doll, its twine down to where the doll's crown meets it
  for (const h of S.hooks) d += nail(h.x, h.top + 0.02 * H, h.end + 2 * s);
  return `<svg viewBox="0 0 ${STAGE_W} ${H}" xmlns="http://www.w3.org/2000/svg">${d}</svg>`;
}

export interface ShelfLightOpts {
  id: string;
  hud?: Hud;
  hooks?: number;
  side?: boolean;
  /** A hung doll's head-to-toe height in units (the dolls' row the pool falls on). */
  body: number;
  /** Where the kit's own flame burns (Kit `kitFlame`); without one, a candle at the shelf's end. */
  flame?: { x: number; y: number } | null;
  /** Units the darkness carries on past each side of the world (default 0). */
  bleed?: number;
}

/** The night's dark over the room, and the candle's warmth (normal alpha only). */
const DARK = { ink: '#0a0604', rest: 0.72, chosen: 0.7 };
const WARM = '255,180,96';

/** The candle: the kit's flame, or one just out of sight at the shelf's right end. */
function candleOf(
  S: ReturnType<typeof shelfPlan>,
  flame?: { x: number; y: number } | null,
) {
  return flame
    ? { ...flame, seen: true }
    : { x: S.x1 - 0.02 * STAGE_H, y: S.top - 0.1 * STAGE_H, seen: false };
}

/**
 * The shelf room's light at night: the room in the dark, and one candle's warm pool on the
 * dolls and the shelf's front edge, leaning towards the candle. The card and the kit keep a
 * soft light so they still read; the walls and the room's edges sink. A still picture: soft
 * holes cut with gradients (no filter, no blend mode), so it never has to be redrawn.
 */
export function shelfLight(o: ShelfLightOpts): string {
  const b = o.bleed ?? 0,
    H = STAGE_H,
    W = STAGE_W,
    P = o.id + '-',
    S = shelfPlan(o),
    c = candleOf(S, o.flame),
    first = S.hooks[0],
    last = S.hooks[S.hooks.length - 1];
  const f = (n: number) => n.toFixed(0);
  // the pool: from just above the shelf's front edge to under the dolls' feet, across the row
  const y0 = S.top - 0.03 * H,
    y1 = (first?.end ?? S.cut) + o.body + 0.05 * H,
    rowL = first ? first.x - S.dollW * 0.6 : S.x0,
    rowR = last ? last.x + S.dollW * 0.6 : S.x1;
  const pool = {
    x: (rowL + rowR) / 2 + (c.x - (rowL + rowR) / 2) * 0.18,
    y: (y0 + y1) / 2,
    rx: (rowR - rowL) / 2 / 0.74,
    ry: (y1 - y0) / 2 / 0.78,
  };
  const cardW = S.cardH * 0.72,
    kitW = S.kitH * 1.25;
  const hole = (id: string, stops: [number, number][]) =>
    `<radialGradient id="${P}${id}">${stops.map(([at, a]) => `<stop offset="${at}" stop-color="#000" stop-opacity="${a}"/>`).join('')}</radialGradient>`;
  const warm = (id: string, a: number) =>
    `<radialGradient id="${P}${id}"><stop offset="0" stop-color="rgb(${WARM})" stop-opacity="${a}"/><stop offset="1" stop-color="rgb(${WARM})" stop-opacity="0"/></radialGradient>`;
  let d = `<defs>${hole('pool', [
    [0, 1],
    [0.5, 0.95],
    [0.78, 0.62],
    [1, 0],
  ])}${hole('soft', [
    [0, 1],
    [0.6, 0.85],
    [1, 0],
  ])}${warm('wash', 0.08)}${warm('halo', c.seen ? 0.3 : 0.1)}`;
  d += `<mask id="${P}m" maskUnits="userSpaceOnUse" x="${-b}" y="0" width="${W + 2 * b}" height="${H}"><rect x="${-b}" width="${W + 2 * b}" height="${H}" fill="#fff"/>`;
  d += `<ellipse cx="${f(pool.x)}" cy="${f(pool.y)}" rx="${f(pool.rx)}" ry="${f(pool.ry)}" fill="url(#${P}pool)"/>`;
  // the card (with its "tap to read" under it) and the kit, softly, so both still read
  d += `<ellipse cx="${f(S.cardX)}" cy="${f(S.foot - S.cardH * 0.42)}" rx="${f(cardW * 0.78)}" ry="${f(S.cardH * 0.74)}" fill="url(#${P}soft)" opacity=".82"/>`;
  d += `<ellipse cx="${f(S.kitX)}" cy="${f(S.foot - S.kitH * 0.35)}" rx="${f(kitW * 0.72)}" ry="${f(S.kitH * 0.85)}" fill="url(#${P}soft)" opacity=".7"/>`;
  // round the candle
  d += `<circle cx="${f(c.x)}" cy="${f(c.y)}" r="${f((c.seen ? 0.2 : 0.16) * H)}" fill="url(#${P}soft)" opacity="${c.seen ? 1 : 0.6}"/>`;
  d += `</mask></defs>`;
  d += `<rect x="${-b}" width="${W + 2 * b}" height="${H}" fill="${DARK.ink}" opacity="${DARK.rest}" mask="url(#${P}m)"/>`;
  // the candle's warmth on the pool, and its halo
  d += `<ellipse cx="${f(pool.x)}" cy="${f(pool.y)}" rx="${f(pool.rx * 0.9)}" ry="${f(pool.ry * 0.9)}" fill="url(#${P}wash)"/>`;
  d += `<circle cx="${f(c.x)}" cy="${f(c.y)}" r="${f(0.1 * H)}" fill="url(#${P}halo)"/>`;
  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="position:absolute;inset:0;width:100%;height:100%${b ? ';overflow:visible' : ''}">${d}</svg>`;
}

export interface ShelfChoiceOpts {
  hud?: Hud;
  hooks?: number;
  side?: boolean;
  body: number;
  /** The chosen doll's nail index. */
  chosen: number;
  bleed?: number;
}

/**
 * A doll chosen: the room below the shelf goes darker still and one light finds that doll,
 * over the candle's room (`shelfLight`). Plain CSS gradients, so it fades in and out cheaply.
 */
export function shelfChoice(o: ShelfChoiceOpts): string {
  const b = o.bleed ?? 0,
    S = shelfPlan(o),
    h = S.hooks[o.chosen];
  if (!h) return '';
  const f = (n: number) => n.toFixed(0);
  const x = h.x + b,
    y = h.end + o.body * 0.5 - S.cut,
    rx = S.dollW * 0.95,
    ry = o.body * 0.9;
  const bg =
    `radial-gradient(ellipse ${f(rx * 0.8)}px ${f(ry * 0.8)}px at ${f(x)}px ${f(y)}px, rgba(${WARM},.1), rgba(${WARM},0)),` +
    `radial-gradient(ellipse ${f(rx)}px ${f(ry)}px at ${f(x)}px ${f(y)}px, rgba(10,6,4,0) 0%, rgba(10,6,4,0) 45%, rgba(10,6,4,${DARK.chosen}) 100%)`;
  return `<div style="position:absolute;left:${-b}px;top:${f(S.cut)}px;width:${STAGE_W + 2 * b}px;height:${f(STAGE_H - S.cut)}px;background:${bg}"></div>`;
}

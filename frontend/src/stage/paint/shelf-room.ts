/**
 * The acting seat's room at night, seen from its own chair.
 *
 * Bare walnut panelling, no window and no lamp: a wall shelf across the upper half on three
 * brass brackets, the walnut tile on its face, and below it a row of brass hooks with short
 * strings, one per other seat. The role card, the clock, the kit and the plush dolls are
 * instruments that stand on the shelf and hang from the hooks; this file draws only the room
 * they are placed in, and says where the shelf and the hooks are so they can be placed.
 *
 * Also here: the room's lighting, because it is particular to the room. The shelf and what
 * is on it stay lit; only the room below the shelf dims when a doll is chosen, and then one
 * light finds that doll.
 *
 * Ported from the shelf bench (revision 70), with the role card framed on the shelf and no
 * lamp, as agreed there.
 */
import { geometry, STAGE_H, STAGE_W, type Hud } from '../units';
import { BOARD, brass, K2, type Special } from './draw';
import { light } from './light';

const WALLO = '#2a170b';

export interface ShelfRoomOpts {
  /** Prefix for every id this drawing makes, so two stages can share a page. */
  id: string;
  hud?: Hud;
  /** How many hooks hang under the shelf (the bench hangs one per living seat but yours). */
  hooks?: number;
  /** The side slot is open: the shelf and its hooks keep to the narrower room at the left. */
  side?: boolean;
  /** URL of the walnut tile for the shelf's face. Without it the face is a flat board colour. */
  wood?: string;
}

/** The shelf and its hooks in units, for placing the card, the clock, the kit and the dolls. */
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
    /** Where things stand on the shelf: its top face, just behind the front edge. */
    foot: top - depth + 2 * s,
    /** Below this line the room dims on a choice; above it the shelf stays lit. */
    cut: top + face + 2 * s,
    /** The role card's frame (left end), the clock (centre) and the role's kit (right end). */
    cardX: x0 + (x1 - x0) * 0.13,
    clockX: cx,
    kitX: x0 + (x1 - x0) * 0.82,
    /** Each hook's string: x, where it leaves the shelf, where the doll's loop meets it. */
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
function wall(wingN: number): string {
  return panelling(wingN, STAGE_W, 7);
}

/**
 * The room's panelled wall from x0 to W, in n panels: the cornice, the dado, the floor at the
 * bottom. The bleed (bleed.ts) draws the same wall on past the room's sides.
 */
export function panelling(x0: number, W: number, n: number, pw = (W - x0) / n): string {
  const H = STAGE_H,
    s = 1,
    room = W - x0,
    corn = 0.06 * H,
    dado = 0.84 * H,
    floorY = 0.92 * H;
  let d = `<rect x="${x0}" y="0" width="${room}" height="${H}" fill="#3a2212"/>`;
  for (let i = 0; i < n; i++) {
    const px = x0 + i * pw;
    d += `<rect x="${px + 8 * s}" y="${corn + 14 * s}" width="${pw - 16 * s}" height="${dado - corn - 28 * s}" fill="none" stroke="#6a4a2a" stroke-width="${2 * s}"/><rect x="${px + 14 * s}" y="${corn + 20 * s}" width="${pw - 28 * s}" height="${dado - corn - 40 * s}" fill="${WALLO}" opacity=".35"/>`;
  }
  d += `<rect x="${x0}" y="0" width="${room}" height="${corn}" fill="#4a2c18"/><path d="M${x0},${corn} H${W}" stroke="${K2}" stroke-width="${3 * s}"/><path d="M${x0},${corn - 8 * s} H${W}" stroke="#6a4a2a" stroke-width="${3 * s}"/>`;
  d += `<path d="M${x0},${dado} H${W}" stroke="${K2}" stroke-width="${4 * s}"/><path d="M${x0},${dado} H${W}" stroke="${brass}" stroke-width="${2.4 * s}"/>`;
  d += `<rect x="${x0}" y="${floorY}" width="${room}" height="${H - floorY}" fill="${BOARD}"/><path d="M${x0},${floorY} H${W}" stroke="${K2}" stroke-width="${3 * s}"/><rect x="${x0}" y="${floorY}" width="${room}" height="${H - floorY}" fill="#0c0a07" opacity=".25"/>`;
  return d;
}

/* the shelf: a walnut board across the upper half on three brass brackets; its top face shows a little, its front edge shows the wood */
function shelf(S: ReturnType<typeof shelfPlan>): string {
  const s = 1,
    H = STAGE_H,
    { x0, x1, top, face, depth } = S;
  let d = '';
  // brackets
  for (const bx of [x0 + (x1 - x0) * 0.08, x0 + (x1 - x0) * 0.5, x0 + (x1 - x0) * 0.92])
    d += `<path d="M${bx},${top + face} q0,${0.07 * H} ${-0.045 * H},${0.075 * H}" fill="none" stroke="${K2}" stroke-width="${6 * s}"/><path d="M${bx},${top + face} q0,${0.07 * H} ${-0.045 * H},${0.075 * H}" fill="none" stroke="${brass}" stroke-width="${3.5 * s}"/><path d="M${bx - 0.045 * H},${top + face + 0.075 * H} h${0.03 * H} q${0.01 * H},${-0.03 * H} ${0.015 * H},${-0.06 * H}" fill="none" stroke="${K2}" stroke-width="${2.6 * s}"/>`;
  // the top face (a sliver, lit) and the front edge (textured by the wood tile beneath; here the ink and the shade)
  d += `<path d="M${x0 + 0.012 * H},${top - depth} H${x1 - 0.012 * H} L${x1},${top} H${x0}Z" fill="#7a5230"/><path d="M${x0 + 0.012 * H},${top - depth} H${x1 - 0.012 * H} L${x1},${top} H${x0}Z" fill="none" stroke="${K2}" stroke-width="${2 * s}"/>`;
  d += `<rect x="${x0}" y="${top}" width="${x1 - x0}" height="${face}" fill="none" stroke="${K2}" stroke-width="${2.4 * s}"/><path d="M${x0},${top + face * 0.85} H${x1}" stroke="#000" stroke-opacity=".35" stroke-width="${face * 0.3}"/>`;
  d += `<path d="M${x0},${top + face} H${x1}" stroke="#000" stroke-opacity=".4" stroke-width="${6 * s}" transform="translate(0,${3 * s})"/>`; // its shadow on the wall
  return d;
}

function hook(x: number, y: number): string {
  const s = 1,
    k = 0.012 * STAGE_H;
  return `<path d="M${x},${y} v${k * 0.8} a${k * 0.7},${k * 0.7} 0 1 0 ${k * 1.2},${k * 0.4}" fill="none" stroke="${K2}" stroke-width="${3.6 * s}" stroke-linecap="round"/><path d="M${x},${y} v${k * 0.8} a${k * 0.7},${k * 0.7} 0 1 0 ${k * 1.2},${k * 0.4}" fill="none" stroke="${brass}" stroke-width="${2 * s}" stroke-linecap="round"/>`;
}

/** The shelf room, as SVG markup for a paint layer. */
export function shelfRoom(o: ShelfRoomOpts): string {
  const g = geometry(o.hud ?? 'live'),
    S = shelfPlan(o),
    s = 1,
    H = STAGE_H,
    P = o.id + '-';
  let d = wall(g.wingN);
  // the face's wood: the tile laid flat, 0.16 of the stage's height per repeat, as the bench's CSS background did
  const fx = Number(S.x0.toFixed(0)),
    fy = Number(S.top.toFixed(0)),
    fw = Number((S.x1 - S.x0).toFixed(0)),
    fh = Number(S.face.toFixed(0)),
    tile = Number((0.16 * H).toFixed(0));
  if (o.wood)
    d += `<defs><pattern id="${P}wood" patternUnits="userSpaceOnUse" x="${fx}" y="${fy}" width="${tile}" height="${tile}"><image href="${o.wood}" width="${tile}" height="${tile}" preserveAspectRatio="none"/></pattern></defs><rect x="${fx}" y="${fy}" width="${fw}" height="${fh}" fill="url(#${P}wood)" opacity=".95"/>`;
  else
    d += `<rect x="${fx}" y="${fy}" width="${fw}" height="${fh}" fill="${BOARD}" opacity=".95"/>`;
  d += shelf(S);
  // the hooks and strings under the shelf, a brass loop at each string's end for a doll to hang from
  for (const h of S.hooks)
    d +=
      hook(h.x - 0.004 * H, h.top) +
      `<path d="M${h.x + 0.004 * H},${h.top + 0.016 * H} V${h.end}" stroke="#d9c9a0" stroke-width="${1.6 * s}"/><path d="M${h.x - 5 * s},${h.end} a${5 * s},${5 * s} 0 1 0 ${10 * s},0 a${5 * s},${5 * s} 0 1 0 ${-10 * s},0" fill="none" stroke="${brass}" stroke-width="${2 * s}"/>`;
  return `<svg viewBox="0 0 ${STAGE_W} ${H}" xmlns="http://www.w3.org/2000/svg">${d}</svg>`;
}

export interface ShelfLightOpts {
  id: string;
  hud?: Hud;
  hooks?: number;
  side?: boolean;
  /** The chosen doll's hook index; omitted, the room below is evenly lit. */
  chosen?: number;
  /** Units the light's darkness carries on past each side of the world (default 0). */
  bleed?: number;
}

/**
 * The shelf room's light, in two halves split at the shelf's lower edge. Above: a soft pool
 * on the shelf and a special on the clock and on the framed card. Below: the room lit evenly
 * before a choice; once a doll is chosen, dark, with one light on that doll.
 */
export function shelfLight(o: ShelfLightOpts): string {
  const hud = o.hud ?? 'live',
    bleed = o.bleed ?? 0,
    sides = bleed ? ` -${bleed}px` : ' 0',
    H = STAGE_H,
    S = shelfPlan(o),
    { cx, room, cut } = S;
  const specials: Special[] = [
    [cx, 0, S.top, 0.12 * H, 0.55],
    [S.cardX, 0, S.top, 0.11 * H, 0.7],
  ];
  const above = light({
    id: o.id + 'a',
    hud,
    pool: { x: cx, y: S.top - 0.16 * H, rx: room * 0.55, ry: 0.34 * H },
    specials,
    dark: 22,
    bleed,
  });
  let below: string;
  const h = o.chosen == null ? undefined : S.hooks[o.chosen];
  if (h) {
    const dw = S.dollW;
    below = light({
      id: o.id + 'b',
      hud,
      pool: { x: h.x, y: h.end + dw * 0.75, rx: dw * 0.62, ry: dw * 1.0 },
      specials: [[h.x, cut, h.end + dw * 1.3, dw * 0.55, 1]],
      dark: 84,
      bleed,
    });
  } else
    below = light({
      id: o.id + 'b',
      hud,
      pool: { x: cx, y: 0.62 * H, rx: room * 0.5, ry: 0.3 * H },
      dark: 50,
      bleed,
    });
  return `<div style="position:absolute;inset:0;clip-path:inset(${cut.toFixed(0)}px${sides} 0${sides})">${below}</div><div style="position:absolute;inset:0;clip-path:inset(0${sides} ${(H - cut).toFixed(0)}px${sides})">${above}</div>`;
}

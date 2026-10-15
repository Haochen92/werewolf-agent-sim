/**
 * The acting seat's room at night, and the pack's: the owner's painted sleeping compartments,
 * one per acting role (the healer's apothecary, the investigator's office, the vigilante's
 * hideout, the killer's trophy room) and the wolves' red-lit "Grandma's things". The props are
 * painted in; this file says where the painting sits on the stage and where the things placed
 * in it go: the night behind its glass, the photo line under the brass rack, the role card on
 * the fold-down table, and the candle whose light the room is lit by.
 *
 * Every room was painted to one plan (a rack across the top, a clear wall under it, a rounded
 * window at the right over a table with a lit candle), so one photo line serves all five; the
 * glass, the candle and the table's clear spot are measured per picture, in its own pixels
 * (stage_architecture §4 "The night rooms").
 *
 * Also here: the room's light, because it is particular to the room. The pictures are already
 * lit by their candles; over them the night's dark, with the candle's warm pool on the photos
 * and the card, and when a photo is chosen, a further dark with one light finding it.
 */
import type { RoomPicture } from '@/assets/manifest';
import { geometry, STAGE_H, STAGE_W, type Hud } from '../units';
import { holeGradient, POOL, scaled, SOFT, softHoles } from './holes';

/** Units per picture pixel: the picture is as wide as the room right of the wing (1512). */
export const ROOM_SCALE = 1512 / 1536;
/** How far down the master the shipped picture starts, in its pixels (the WebP's crop). */
export const ROOM_CROP_Y = 40;
/** The shipped picture's size in pixels: the master's band from the rack to the floor. */
export const ROOM_PX = { w: 1536, h: 915 } as const;
/** Where the open side slot starts: the painting slides left until its glass ends about here. */
const SIDE_GLASS_END = 985;

interface RoomMeasure {
  /** The glass's rounded rectangle, master px (the brass frame's inside). */
  glass: { x0: number; x1: number; y0: number; y1: number; r: number };
  /** The painted flame the room is lit by, master px. */
  candle: readonly [number, number];
  /** The table's clear spot: the card's centre and where its frame stands, master px. */
  card: readonly [number, number];
  /** The candle's light, as `r,g,b`. */
  warm: string;
}

/** Measured on the masters (1536×1024); stage_architecture §4 has the recipe. */
export const ROOMS: Record<RoomPicture, RoomMeasure> = {
  healer: {
    glass: { x0: 893, x1: 1340, y0: 253, y1: 529, r: 44 },
    candle: [1248, 522],
    card: [1075, 628],
    warm: '255,180,96',
  },
  investigator: {
    glass: { x0: 892, x1: 1339, y0: 251, y1: 528, r: 48 },
    candle: [1233, 518],
    card: [1005, 622],
    warm: '255,180,96',
  },
  vigilante: {
    glass: { x0: 875, x1: 1306, y0: 240, y1: 511, r: 46 },
    candle: [1220, 512],
    card: [1000, 604],
    warm: '255,180,96',
  },
  serial_killer: {
    glass: { x0: 881, x1: 1331, y0: 241, y1: 514, r: 49 },
    candle: [1369, 468],
    card: [1010, 625],
    warm: '226,170,255',
  },
  wolf: {
    glass: { x0: 891, x1: 1340, y0: 249, y1: 528, r: 49 },
    candle: [1265, 522],
    card: [1040, 630],
    warm: '255,76,52',
  },
  // The 2026-10-07 rooms (docs/night_rooms_brief.md), measured by scripts/fit-night-rooms.mjs;
  // the plan's table, so one card spot. Light: amber for the town, the neutral side's
  // moon-silver (the speculator's lamp, the fortune teller's crystal ball), the necromancer's
  // sickly green to match his figure.
  sentinel: {
    glass: { x0: 893, x1: 1339, y0: 252, y1: 525, r: 49 },
    candle: [1245, 561],
    card: [1045, 628],
    warm: '255,180,96',
  },
  trailseer: {
    glass: { x0: 892, x1: 1338, y0: 253, y1: 525, r: 46 },
    candle: [1247, 549],
    card: [1045, 628],
    warm: '255,180,96',
  },
  sigilist: {
    glass: { x0: 892, x1: 1337, y0: 253, y1: 526, r: 46 },
    candle: [1242, 550],
    card: [1045, 628],
    warm: '255,180,96',
  },
  speculator: {
    glass: { x0: 891, x1: 1338, y0: 254, y1: 527, r: 48 },
    candle: [1244, 579],
    card: [1045, 628],
    warm: '214,224,240',
  },
  necromancer: {
    glass: { x0: 892, x1: 1338, y0: 252, y1: 524, r: 48 },
    candle: [1257, 576],
    card: [1045, 628],
    warm: '190,230,110',
  },
  fortune_teller: {
    glass: { x0: 891, x1: 1339, y0: 252, y1: 526, r: 48 },
    candle: [1252, 589],
    card: [1045, 628],
    warm: '214,224,240',
  },
};

/**
 * The photo line, the same in every room: twine tied to the rack's lowest rail from just over
 * the left wall's hangings to the window's panel (master px), sagging between them.
 */
const LINE = { x0: 280, x1: 835, y: 128 } as const;
/** How far the twine sags at its middle, in units. */
const SAG = 34;
/** A print's height over its width: the square picture, the borders, the numeral's strip. */
export const PHOTO_H = 1.26;
/** The gap between one height's feet and the next height's heads, in units. */
const DROP_GAP = 24;
/** The gap between two prints at one height, in units. */
const PRINT_GAP = 8;
/** The smallest print a line settles for before it hangs at one more height (~45 css px on a phone). */
const MIN_PRINT = 104;
/** The card's height on the table, in units. */
const CARD_H = 200;

export interface RoomOpts {
  room: RoomPicture;
  hud?: Hud;
  /** The side slot is open: the painting slides left so its window and wall stay in view. */
  side?: boolean;
  /** How many photos hang on the line. */
  n?: number;
  /**
   * Units the whole line of prints hangs lower, each on its own length of twine (the
   * necromancer's targets, under its bodies on the line itself); default 0.
   */
  lower?: number;
  /** The widest a print may be, in units (default 140, one height's widest). */
  maxW?: number;
}

/** Where the painting and everything in it sits, in units. */
export function roomPlan(o: RoomOpts) {
  const M = ROOMS[o.room],
    g = geometry(o.hud ?? 'live', o.side ?? false),
    s = ROOM_SCALE,
    // the room right of the wing, or slid left until the glass ends at the open slot
    ox = o.side ? SIDE_GLASS_END - M.glass.x1 * s : STAGE_W - ROOM_PX.w * s;
  const X = (px: number) => ox + px * s,
    Y = (py: number) => (py - ROOM_CROP_Y) * s;
  const n = Math.max(1, o.n ?? 8);
  const a = { x: X(LINE.x0), y: Y(LINE.y) },
    b = { x: X(LINE.x1), y: Y(LINE.y) };
  /** The twine's height at x: a sag between its two ties. */
  const lineY = (x: number) => {
    const t = Math.min(1, Math.max(0, (x - a.x) / (b.x - a.x)));
    return a.y + 4 * SAG * t * (1 - t);
  };
  // the photos keep to the line's part in view: clear of the wing, clear of the window's frame
  const lo = Math.max(a.x + 10, g.wingN + 16),
    span = b.x - 10 - lo;
  // k heights: neighbours overlap across the heights, prints at one height k pitches apart
  const across = (k: number) =>
    Math.min(130, (k * span - PRINT_GAP * (n - 1)) / (n - 1 + k));
  // one height while it keeps the prints big enough (up to four), else two, else three
  const rows =
    n <= 4 && (span / n) * 0.9 >= MIN_PRINT ? 1 : n >= 6 && across(2) < MIN_PRINT ? 3 : 2;
  // one height: evenly spaced, each in its own stretch
  const widest = o.maxW ?? 140;
  const w = Math.min(widest, rows === 1 ? (span / n) * 0.9 : across(rows)),
    pitch = rows === 1 ? span / n : (span - w) / (n - 1),
    first = rows === 1 ? lo + pitch / 2 : lo + w / 2,
    h = w * PHOTO_H;
  const photos = Array.from({ length: n }, (_, i) => {
    const x = first + pitch * i,
      at = lineY(x),
      row = i % rows;
    // the first height is pegged to the line itself; a lower one hangs on its own length of twine
    const top = at + 3 + (o.lower ?? 0) + row * (h + DROP_GAP);
    return { x, top, line: at, drop: top - at, row };
  });
  const cardW = CARD_H * 0.72;
  return {
    ox,
    /** The picture's box. */
    picture: { x: ox, y: 0, w: ROOM_PX.w * s, h: ROOM_PX.h * s },
    /** The glass, a few units wider than the frame's inside so no edge shows past the night. */
    glass: {
      x: X(M.glass.x0) - 3,
      y: Y(M.glass.y0) - 3,
      w: (M.glass.x1 - M.glass.x0) * s + 6,
      h: (M.glass.y1 - M.glass.y0) * s + 6,
      r: M.glass.r * s + 3,
    },
    candle: { x: X(M.candle[0]), y: Y(M.candle[1]) },
    card: { x: X(M.card[0]), foot: Y(M.card[1]), h: CARD_H, w: cardW },
    warm: M.warm,
    /** The twine's two ties on the rack and its sag. */
    line: { a, b, sag: SAG },
    lineY,
    /** Each photo's width and height, and where it hangs: its centre, its top, the line above it. */
    photo: { w, h },
    photos,
  };
}

export type RoomPlan = ReturnType<typeof roomPlan>;

/** The twine across the wall, from tie to tie, as SVG markup (the photos' own strings are theirs). */
export function photoTwine(o: RoomOpts & { id: string }): string {
  const P = roomPlan(o),
    { a, b, sag } = P.line,
    f = (v: number) => v.toFixed(1);
  const d = `M${f(a.x)},${f(a.y)} Q${f((a.x + b.x) / 2)},${f(a.y + 2 * sag)} ${f(b.x)},${f(b.y)}`;
  // a hair of light on its upper side, and a knot round the rail at each end
  const knot = (x: number, y: number) =>
    `<ellipse cx="${f(x)}" cy="${f(y)}" rx="3.2" ry="2.4" fill="#1a110a"/>`;
  return (
    `<svg viewBox="0 0 ${STAGE_W} ${STAGE_H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="position:absolute;inset:0;width:100%;height:100%;overflow:visible">` +
    `<path d="${d}" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="2.4" transform="translate(2.5,4)"/>` +
    `<path d="${d}" fill="none" stroke="#2a1d11" stroke-width="2.2"/>` +
    `<path d="${d}" fill="none" stroke="#a88a66" stroke-opacity=".45" stroke-width=".7" transform="translate(0,-0.7)"/>` +
    knot(a.x, a.y) +
    knot(b.x, b.y) +
    `</svg>`
  );
}

export interface RoomLightOpts extends RoomOpts {
  /** Prefix for every id this drawing makes, so two stages can share a page. */
  id: string;
  /** Units the darkness carries on past each side of the world (default 0). */
  bleed?: number;
}

/** The night's dark over the painting (already lit by its candle), and the dark of a choice. */
const DARK = { ink: '#0a0604', rest: 0.5, chosen: 0.62 };

/**
 * The room's light at night: the painting in the dark, and its candle's warm pool on the photo
 * line, leaning towards the candle; the card on the table keeps a soft light so it reads, and
 * the candle its own glow. A still picture: soft holes cut with gradients (no filter, no blend
 * mode), so it never has to be redrawn. No SVG mask either (2026-10-01, iPhone Safari): the
 * dark is a sheet with the holes cut out, each filled from inside with a gradient of the same
 * dark, clear at its middle and as dark as the sheet at its rim (`holes.ts`); where the card's
 * light runs into the candle's, the clearer of the two wins.
 */
export function roomLight(o: RoomLightOpts): string {
  const b = o.bleed ?? 0,
    H = STAGE_H,
    W = STAGE_W,
    P = o.id + '-',
    R = roomPlan(o),
    c = R.candle,
    first = R.photos[0],
    last = R.photos[R.photos.length - 1];
  const f = (n: number) => n.toFixed(0);
  // the pool: from the rack's ties to under the lowest photo, across the line
  const y0 = R.line.a.y - 0.04 * H,
    y1 = Math.max(...R.photos.map((p) => p.top)) + R.photo.h + 0.05 * H,
    rowL = (first?.x ?? R.line.a.x) - R.photo.w * 0.7,
    rowR = (last?.x ?? R.line.b.x) + R.photo.w * 0.7;
  const pool = {
    x: (rowL + rowR) / 2 + (c.x - (rowL + rowR) / 2) * 0.18,
    y: (y0 + y1) / 2,
    rx: (rowR - rowL) / 2 / 0.74,
    ry: (y1 - y0) / 2 / 0.78,
  };
  const warm = (id: string, a: number) =>
    `<radialGradient id="${P}${id}"><stop offset="0" stop-color="rgb(${R.warm})" stop-opacity="${a}"/><stop offset="1" stop-color="rgb(${R.warm})" stop-opacity="0"/></radialGradient>`;
  const { sheet, pieces } = softHoles(
    [
      { ...pool, clear: POOL },
      // the card on the table (with its "tap to read" under it), softly, so it still reads
      {
        x: R.card.x,
        y: R.card.foot - R.card.h * 0.42,
        rx: R.card.w * 0.95,
        ry: R.card.h * 0.8,
        clear: scaled(SOFT, 0.85),
      },
      // round the candle
      { x: c.x, y: c.y, rx: 0.2 * H, ry: 0.2 * H, clear: SOFT },
    ],
    { x0: -b, y0: 0, x1: W + b, y1: H },
  );
  let d = `<defs>${pieces.map((q, i) => holeGradient(`${P}h${i}`, q.hole, DARK.ink, DARK.rest)).join('')}${warm('wash', 0.08)}${warm('halo', 0.22)}</defs>`;
  d += `<path d="${sheet}" fill="${DARK.ink}" fill-opacity="${DARK.rest}" fill-rule="evenodd"/>`;
  d += pieces
    .map((q, i) => `<path d="${q.d}" fill="url(#${P}h${i})" fill-rule="evenodd"/>`)
    .join('');
  // the candle's warmth on the pool, and its halo
  d += `<ellipse cx="${f(pool.x)}" cy="${f(pool.y)}" rx="${f(pool.rx * 0.9)}" ry="${f(pool.ry * 0.9)}" fill="url(#${P}wash)"/>`;
  d += `<circle cx="${f(c.x)}" cy="${f(c.y)}" r="${f(0.1 * H)}" fill="url(#${P}halo)"/>`;
  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="position:absolute;inset:0;width:100%;height:100%${b ? ';overflow:visible' : ''}">${d}</svg>`;
}

export interface RoomChoiceOpts extends RoomOpts {
  /** Prefix for every id this drawing makes, so two stages can share a page. */
  id: string;
  /** The chosen photo's index on the line. */
  chosen: number;
  bleed?: number;
}

/** How far before the card's left edge the choice's dark starts to fade, in units. */
const CHOICE_FADE = 90;
/** The card's side as a hole: a far, tall ellipse whose rim is all but straight across the stage. */
const CHOICE_FAR = 3000;

/**
 * A photo chosen: the wall goes darker still and one light finds that photo, over the candle's
 * room (`roomLight`). The table, its candle and the card are left as they were: the dark fades
 * out just before the card. Fades in and out cheaply (its wrapper's opacity).
 *
 * No mask of any kind (2026-10-01: a full-stage CSS `mask-image`, which faded this dark out
 * before the card, killed iPhone Safari as the SVG masks did; stage_architecture.md §6). The dark
 * is a sheet with two soft holes (`holes.ts`): the chosen photo's ellipse, clear to 55% of its
 * radius as before, and the card's side, an ellipse so far and tall that its rim runs straight
 * down the stage, clear from the card's left edge and dark again 90 units before it.
 */
export function roomChoice(o: RoomChoiceOpts): string {
  const b = o.bleed ?? 0,
    H = STAGE_H,
    W = STAGE_W,
    P = o.id + '-',
    R = roomPlan(o),
    p = R.photos[o.chosen];
  if (!p) return '';
  const f = (n: number) => n.toFixed(0);
  const x = p.x,
    y = p.top + R.photo.h * 0.5,
    rx = R.photo.w * 1.25,
    ry = R.photo.h * 1.1,
    // the dark ends at the card's left edge, faded over the last stretch
    end = R.card.x - R.card.w / 2,
    far = CHOICE_FAR + CHOICE_FADE;
  const { sheet, pieces } = softHoles(
    [
      {
        x,
        y,
        rx,
        ry,
        clear: [
          [0, 1],
          [0.55, 1],
          [1, 0],
        ],
      },
      {
        x: end + CHOICE_FAR,
        y: H / 2,
        rx: far,
        ry: 40 * H,
        clear: [
          [0, 1],
          [CHOICE_FAR / far, 1],
          [1, 0],
        ],
      },
    ],
    { x0: -b, y0: 0, x1: W + b, y1: H },
  );
  let d = `<defs>${pieces.map((q, i) => holeGradient(`${P}c${i}`, q.hole, DARK.ink, DARK.chosen)).join('')}<radialGradient id="${P}cwarm"><stop offset="0" stop-color="rgb(${R.warm})" stop-opacity=".18"/><stop offset="1" stop-color="rgb(${R.warm})" stop-opacity="0"/></radialGradient></defs>`;
  d += `<path d="${sheet}" fill="${DARK.ink}" fill-opacity="${DARK.chosen}" fill-rule="evenodd"/>`;
  d += pieces
    .map((q, i) => `<path d="${q.d}" fill="url(#${P}c${i})" fill-rule="evenodd"/>`)
    .join('');
  // the light finding the photo, warm
  d += `<ellipse cx="${f(x)}" cy="${f(y)}" rx="${f(rx * 0.8)}" ry="${f(ry * 0.8)}" fill="url(#${P}cwarm)"/>`;
  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="position:absolute;inset:0;width:100%;height:100%${b ? ';overflow:visible' : ''}">${d}</svg>`;
}

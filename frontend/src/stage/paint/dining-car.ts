/**
 * The dining car: the day's backdrop, and the night lobby's.
 *
 * The car is a painting (owner-ruled 2026-09-29): walnut panels, the long brass-framed window
 * on the country, a lantern on its bracket at the right, a table lamp at each edge, and the
 * stage floor, painted once by day and relit from that same picture for the night
 * (SPRITES.car, stage_architecture §4 "The dining car"). The CarBackdrop instrument lays it;
 * this file says where it sits and what the layers above it need from the room: where the
 * light's glows and specials fall, the floor's lines, the window and its glass.
 *
 * The painting was fitted to the kit's car at the HUD 'none' layout (scripts/fit-car.mjs): its
 * glass on the kit's window, its floor strip on the rail. It follows the layout as the drawn
 * car did: across with the puppet's centre line (the HUD's wing, the open side slot) and up or
 * down with the rail (the replay's), so the glass, the floor and the lamps move together.
 *
 * The plan is still the design kit's `scene()` (kits/stage-kit.js, VERSION 2026-09-23); a test
 * holds the two equal, with the departures it documents: the kit's drawing is gone (the
 * painting is the walls, the frame and the floor), the wall clock is gone, and the lantern's
 * special and glow sit on the painted lantern, with a glow on each painted table lamp too.
 */
import { geometry, STAGE_H, STAGE_W, type Hud } from '../units';
import type { Glow, Rect, Special } from './draw';
import { PHASES, ROOMLIGHT, type Phase } from './materials';
import { carLines, windowRect } from './window';

/**
 * The fitted painting, in its own 1600×900 pixels (one a unit), measured on car-day.png
 * (2026-09-29): the layout it was fitted to, its cleared glass, and the lamps' flames.
 */
export const CAR_PICTURE = {
  /** The puppet's centre line and the rail it was fitted to (the kit's car at HUD 'none'). */
  fit: { cx: 800, railY: 639 },
  /** The glass the felt country shows through: its box and corner radius. */
  glass: { x0: 401, y0: 113, x1: 1199, y1: 409, r: 28 },
  /** The lantern on its bracket at the right, its glass's centre. */
  lantern: [1485, 175],
  /** The table lamps at the left and right edges, their shades' centres. */
  tableLamps: [
    [45, 400],
    [1555, 400],
  ],
} as const;

/** How far each painted lamp's hole in the house's dark reaches, in units: the glass, its pool on the wall and table. */
export const LAMP_HOLE = { lantern: 120, table: 150 };

/** Where the painting's top-left corner goes on the stage for a layout, in units. */
export function carOffset(hud: Hud = 'live', side = false) {
  const g = geometry(hud, side);
  return { x: g.cx - CAR_PICTURE.fit.cx, y: g.railY - CAR_PICTURE.fit.railY };
}

export interface DiningCarOpts {
  phase: Phase;
  hud?: Hud;
  /** The side slot is open: the room, the puppet and the window move left. */
  side?: boolean;
}

/** Where things are in the car, for the layers above it (the light, the floor, the instruments). */
export interface DiningCarPlan {
  /** Warm pools the light overlay leaves open: [x, y, r, strength]. */
  glows: Glow[];
  /** Narrow spots from above on the window and the lantern. */
  specials: Special[];
  /**
   * The painted lamps (the lantern, then the table lamps), lit in both pictures: the light
   * cuts each a clean warm hole through the house's dark (`light`'s `lamps`), at any hour.
   */
  lamps: Glow[];
  floor: { floorY: number; floorH: number; B: number; trap: Rect };
  /** The free wall either side of the window, [from, to] in x. */
  slots: { L: [number, number]; R: [number, number] };
  /** The kit's window: the layout's glass, which the shutter and the flies measure from. */
  window: Rect;
  /** The painting's top-left corner on the stage. */
  picture: { x: number; y: number };
  /** The painting's cleared glass on the stage, and its corner radius. */
  glass: { x: number; y: number; w: number; h: number; r: number };
}

/* a painted lamp's glow and, for the lantern, its special: the kit's lantern(), at the painting's lamp */
function lamp(
  at: readonly [number, number],
  lit: boolean,
  special: ((x: number, y1: number, rx: number, a?: number) => void) | null,
): Glow {
  const W = STAGE_W,
    H = STAGE_H,
    [x, y] = at,
    bh = 0.075 * H;
  special?.(x, y + bh * 0.5, 0.055 * W, 0.85);
  return lit ? [x, y, 0.3 * H, '#ffb35c'] : [x, y, 0.06 * H, '#ffb35c'];
}

function build(o: DiningCarOpts): DiningCarPlan {
  const g = geometry(o.hud ?? 'live', o.side ?? false);
  const c = PHASES[o.phase],
    W = STAGE_W,
    B = g.railY,
    cx = g.cx,
    pw = g.pwid;
  const specials: Special[] = [];
  const special = (x: number, y1: number, rx: number, a = 0.9, y0 = 0) =>
    specials.push([x, y0, y1, rx, a]);
  const { floorH, floorY } = carLines(g);
  // the kit's trapdoor under the puppet: painted now, but still where the floor's hole is measured from
  const tw = pw * 0.9,
    tx = cx - tw / 2,
    ty = floorY + floorH * 0.3;
  const edge = 0.03 * W,
    slotL: [number, number] = [edge, cx - pw * 0.55 - 0.02 * W],
    slotR: [number, number] = [cx + pw * 0.55 + 0.02 * W, W - edge];
  // the window: its special, and the free wall either side of it
  const win = windowRect(g),
    [wx, wy, ww, wh] = win;
  special(wx + ww / 2, wy + wh, ww * 0.55, 0.45);
  slotL[1] = Math.min(slotL[1], wx - 0.02 * W);
  slotR[0] = Math.max(slotR[0], wx + ww + 0.02 * W);
  // the painted lamps: the lantern (its special and glow, the kit's) and the two table lamps
  const at = carOffset(o.hud, o.side),
    on = ([x, y]: readonly [number, number]) => [x + at.x, y + at.y] as const;
  const glows: Glow[] = [];
  if (slotR[1] - slotR[0] > 0.06 * W)
    glows.push(lamp(on(CAR_PICTURE.lantern), c.lit, special));
  for (const t of CAR_PICTURE.tableLamps) glows.push(lamp(on(t), c.lit, null));
  const Lt = ROOMLIGHT[o.phase];
  const G = CAR_PICTURE.glass;
  const lamps: Glow[] = [
    [...on(CAR_PICTURE.lantern), LAMP_HOLE.lantern, 1],
    ...CAR_PICTURE.tableLamps.map((t): Glow => [...on(t), LAMP_HOLE.table, 1]),
  ];
  return {
    glows: glows.map(([x, y, r]) => [x, y, r * 0.55, Lt.glow]),
    specials,
    lamps,
    floor: { floorY, floorH, B, trap: [tx, ty, tw, B - ty] },
    slots: { L: slotL, R: slotR },
    window: win,
    picture: at,
    glass: { x: G.x0 + at.x, y: G.y0 + at.y, w: G.x1 - G.x0, h: G.y1 - G.y0, r: G.r },
  };
}

/** The car's layout: where its glows, specials, floor, window and painting are. */
export function diningCarPlan(o: DiningCarOpts): DiningCarPlan {
  return build(o);
}

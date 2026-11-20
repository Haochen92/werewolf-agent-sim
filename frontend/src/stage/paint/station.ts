/**
 * The station platform: the waiting room's backdrop (review 2026-09-26 §A5, ruling F1), before
 * the train leaves for the deal.
 *
 * A winter night under the station's canopy, the owner's one picture (2026-10-19; drawn in parts
 * before): a walnut beam under snow, two stone pillars with their lanterns, a low stone ledge,
 * the paving, the night country through the arches. The train (the dining car in the middle,
 * its five windows holding the places, a carriage either side) stands in the arches, behind the
 * pillars, the beam and the ledge: the picture ships whole for the back and again with the
 * arches clear for the front (scripts/fit_platform.py). The people waiting stand on the
 * platform, one under each place in the window, so the row on the platform mirrors the row in
 * the car. `stationPlan` says where everything is, for the scene's pictures and instruments.
 *
 * Ported from the waiting-room mockup (`claude_artifacts/design/pages/waiting-room.html`),
 * whose geometry is in container units of a 16:9 box: 1cqw = 16 units, 1cqh = 9 units here.
 */
import { STAGE_H, STAGE_W, geometry, type Hud } from '../units';

/**
 * The train picture's own geometry, in the pixels of its master: the owner's wooden toy train
 * (2026-10-18; felt before it), joined from its pieces by scripts/fit_felt_station.py, which
 * prints these numbers.
 */
const TRAIN_PX = {
  w: 8260,
  h: 1323,
  /** The dining car's window, left to right and top to bottom. */
  wx0: 2523,
  wx1: 5723,
  wy0: 383,
  wy1: 676,
  /** The roof's snow line and the wheels' foot. */
  snow: 45,
  bottom: 1319,
  /** The dining car's five windows: the first's left edge is `wx0`; each this wide, this far apart. */
  windows: 5,
  windowW: 480,
  windowPitch: 680,
} as const;

/** The car from its roof's snow to its wheels (48cqh), and where that snow sits: under the
 * picture's beam, its wheels behind the ledge (2026-10-19; 144 before). */
const CAR_H = 432;
const SNOW_Y = 164;
/**
 * The platform picture's master pixels, and its width in units: its pillars stand where the
 * lamp posts stood, just outside the window's ends, and its ledge's top at `floorY`.
 */
const PLATFORM_PX = { w: 1672, h: 941 } as const;
const PLATFORM_W = 1745;

/** A box in units. */
export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface StationPlan {
  /** The room's centre line: the dining car's window and the station sign sit on it. */
  cx: number;
  /** The whole train picture at rest. */
  train: Box;
  /** The dining car's windows, first to last, as one box (the train at rest): the places' row. */
  glass: Box;
  /** Each window's own glass, in world units: a place is seen only through these. */
  windows: Box[];
  /** One place's width in the window. */
  pitch: number;
  /** The places' centres, one per seat, left to right; the platform's marks sit under them. */
  places: number[];
  /** The top of the brass plates under the window. */
  plateY: number;
  /** The platform's top (its stone ledge). */
  floorY: number;
  /** Where the people waiting stand, and how tall a body is there. */
  feetY: number;
  bodyH: number;
  /** The platform picture (back and front alike): centred on the room, from the stage's top. */
  picture: Box;
  /** How far right the train travels to leave the world (it is clipped at the world's edges). */
  pull: number;
}

/**
 * Where everything on the platform is, in units, for a HUD mode (the wing narrows the room).
 * `seats` divides the window into places: the room's size (`RoomInput.places`); nine where no
 * room is known (the back and front paint, which use no places).
 */
export function stationPlan(hud: Hud = 'live', seats = 9): StationPlan {
  const g = geometry(hud);
  // one master pixel in units, the same both ways (the mockup's `s`, turned into units)
  const k = CAR_H / (TRAIN_PX.bottom - TRAIN_PX.snow);
  const cx = g.wingN + g.area / 2;
  const wlen = (TRAIN_PX.wx1 - TRAIN_PX.wx0) * k;
  const wl = cx - wlen / 2;
  const train = {
    x: wl - TRAIN_PX.wx0 * k,
    y: SNOW_Y - TRAIN_PX.snow * k,
    w: TRAIN_PX.w * k,
    h: TRAIN_PX.h * k,
  };
  const glass = {
    x: wl,
    y: train.y + TRAIN_PX.wy0 * k,
    w: wlen,
    h: (TRAIN_PX.wy1 - TRAIN_PX.wy0) * k,
  };
  const windows = Array.from({ length: TRAIN_PX.windows }, (_, i) => ({
    x: wl + i * TRAIN_PX.windowPitch * k,
    y: glass.y,
    w: TRAIN_PX.windowW * k,
    h: glass.h,
  }));
  const pitch = wlen / seats;
  const ph = (PLATFORM_W * PLATFORM_PX.h) / PLATFORM_PX.w;
  return {
    cx,
    train,
    glass,
    windows,
    pitch,
    places: Array.from({ length: seats }, (_, i) => wl + (i + 0.5) * pitch),
    // under the window's felt frame, on the panel
    plateY: glass.y + glass.h + 14,
    floorY: 0.66 * STAGE_H,
    feetY: 0.775 * STAGE_H,
    bodyH: 0.2 * STAGE_H,
    picture: { x: cx - PLATFORM_W / 2, y: 0, w: PLATFORM_W, h: ph },
    // past the right edge, with a little to spare
    pull: STAGE_W - train.x + 64,
  };
}

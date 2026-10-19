/**
 * Where the vote's things stand, in units: the table on the floor, the glass jar, the plates
 * along the table's front edge, the place cards on the cloth, the chips on the plates. The
 * table is sized from the puppet's box as the vote bench's was, and stands whole, its feet
 * near the frame's foot (owner, 2026-10-19); a number here can be checked against the vote
 * bench (rev 64 `VG`, `jar`, `plateSpots`, `stackPos`, `cardSVG`) by eye.
 */
import { carLines } from '../paint/window';
import { CAMERA_ZOOM_MAX, STAGE_H, type StageGeometry } from '../units';

export interface VoteGeometry {
  g: StageGeometry;
  cx: number;
  /** The table's front edge (top of the cloth's drop) and how deep its top reads. */
  topY: number;
  depth: number;
  /** Front and back width of the table's top; the cloth's drop below the front edge. */
  tw: number;
  bw: number;
  drop: number;
  /** Where the table's feet stand on the floor. */
  footY: number;
  /** A ballot chip's radius. */
  r: number;
  /** The jar's base line on the table. */
  base: number;
  floorH: number;
}

/**
 * The table picture (SPRITES.props.voteTable, the owner's, 2026-10-19: a green baize top in a
 * studded walnut rim, a cream cloth with a fleur-de-lis and a scalloped hem, turned legs) in its
 * file's pixels: its top's back and front lines, the front corners, the cloth's depth to the
 * hem's cusps (so the place cards hang on the plain cloth above the scallops), and its feet.
 */
export const TABLE_PX = {
  W: 1412,
  H: 657,
  back: 1.8,
  front: 164.6,
  left: 0,
  right: 1411.1,
  drop: 114.2,
  feet: 654.8,
} as const;

export function voteGeometry(g: StageGeometry): VoteGeometry {
  const ph = g.ph,
    { floorH } = carLines(g),
    P = TABLE_PX;
  // the bench's width (0.6 of the room right of the wing), the picture at one scale down it
  const tw = Math.min((g.side ? 0.76 : 0.6) * g.room, 2.1 * g.pwid),
    s = tw / (P.right - P.left),
    depth = 0.085 * ph,
    footY = 0.988 * STAGE_H,
    topY = footY - (P.feet - P.front) * s;
  return {
    g,
    cx: g.cx,
    topY,
    depth,
    tw,
    bw: tw * 0.9,
    drop: P.drop * s,
    footY,
    r: Math.max(8, 0.078 * g.pwid),
    base: topY - depth * 0.62,
    floorH,
  };
}

/**
 * The painted glass and lid (SPRITES.props), in their files' pixels: the file's size and the
 * painted thing's box inside it. The glass's lines are fractions of its height above its foot.
 */
export const GLASS_PX = { W: 1052, H: 960, x: 6, y: 6, w: 1040, h: 948 } as const;
/**
 * The lid (a glass dome with a ball knob, its flange underneath going down inside the mouth):
 * `skirt` is the width in its pixels that matches the jar's lip, so the 960 px flange fills the
 * mouth's inside (0.84 of the lip); the string ties round the knob's neck, 224 px down.
 */
export const LID_PX = {
  W: 1276,
  H: 686,
  x: 6,
  y: 6,
  w: 1264,
  h: 674,
  skirt: 1143,
  tie: 224,
} as const;

/** The jar and its lid, upright on the table, where the glass picture has them. */
export function jarGeometry(v: VoteGeometry) {
  const { cx, base, g } = v,
    // the footed sweet jar (2026-10-17) is squat: this height keeps it ~1.2× the old jar's width
    h = 0.42 * g.ph,
    w = (h * GLASS_PX.w) / GLASS_PX.h;
  // measured on the picture: the lip's width; where the lid's flange ends inside the neck (the
  // dome's front edge then rests on the lip's); the mouth; the neck's foot; the inner floor
  const wN = w * 0.7,
    yL = base - h * 0.793,
    yR = base - h * 0.948,
    yN = base - h * 0.758,
    floor = base - h * 0.278;
  // the lid scaled so its flange fills the mouth, its foot (the flange's) inside the neck
  const ks = wN / LID_PX.skirt,
    lw = LID_PX.w * ks,
    lh = LID_PX.h * ks,
    ly = yL - lh;
  // for the count it stands at the table's right end, past the plates' row (`plateSpots`), a
  // little smaller for being upstage (owner 2026-10-17: a sweet jar is not tipped out; it fades
  // from the centre to there)
  const sc = 0.6,
    ax = cx + 0.38 * v.tw,
    ay = v.topY - v.depth * 0.7;
  const m = base - yR;
  return {
    h,
    w,
    wN,
    yN,
    yR,
    /** Where the chips in the jar lie: in the belly's bottom, above the stem. */
    floor,
    /** The lid picture's box, its scale (units a pixel), and where its string ties on. */
    lid: { lh, lw, ly, ks, knob: ly + LID_PX.tie * ks, cx, cy: ly + lh / 2 },
    /** Lifted off and tilted, hung on its string. */
    lidUp: { x: 0.07 * g.pwid, y: -0.11 * g.ph, rot: -16 },
    /** The top of the lid's ring, where the light's special stops. */
    top: ly,
    /** Standing at the back for the count: its base's centre, and its scale about it. */
    aside: { x: ax, y: ay, sc },
    /** The jar's mouth at the back, where a counted chip leaves it. */
    mouth: { x: ax, y: ay - m * sc },
  };
}

/** Chips in a pile, per = 4 to a layer, each layer a little higher and staggered. */
export function pileSpots(v: VoteGeometry, n: number): [number, number][] {
  const J = jarGeometry(v),
    base = J.floor,
    // inside the glass's walls, where the belly narrows to its stem
    halfW = J.w * 0.3,
    { r } = v,
    per = 4;
  const out: [number, number][] = [];
  for (let i = 0; i < n; i++) {
    const L = Math.floor(i / per),
      p = i % per,
      off = (L % 2 ? 0.45 : -0.2) * r;
    out.push([
      v.cx +
        Math.max(-halfW + r, Math.min(halfW - r, (p - (per - 1) / 2) * 1.75 * r + off)),
      base - r * 0.5 - L * 0.55 * r,
    ]);
  }
  return out;
}

/**
 * A counted chip's thickness, as a fraction of its radius (the tower's step: the maple ring's edge
 * at the table's tilt, 2026-10-19); chips per tower.
 */
export const TOWER_STEP = 0.42;
export const TOWER_CAP = 4;

export interface PlateSpot {
  /** The candidate: a seat, or `abstain` for the plate at the right. */
  c: string;
  x: number;
  y: number;
  rx: number;
  ry: number;
  /** How many towers the plate's chips need, from the full tally. */
  towers: number;
}

/**
 * One plate per candidate along the front edge, abstain's last, sized to the full tally. The row
 * leaves the table's right end to the jar standing there (`jarGeometry().aside`), so no plate's
 * towers stand in front of it, however many candidates there are.
 */
export function plateSpots(
  v: VoteGeometry,
  cands: readonly string[],
  counts: Record<string, number>,
): PlateSpot[] {
  const n = cands.length,
    left = v.cx - v.tw * 0.42,
    span = v.tw * 0.68,
    gap = span / Math.max(1, n);
  const rx0 = Math.min(0.2 * v.g.pwid, gap * 0.44);
  return cands.map((c, i) => {
    const rx = rx0;
    return {
      c,
      x: left + gap * (i + 0.5),
      y: v.topY - v.depth * 0.28,
      rx,
      ry: rx * 0.3,
      towers: Math.max(1, Math.ceil((counts[c] ?? 0) / TOWER_CAP)),
    };
  });
}

/** The radius of a chip on a plate: big enough to read, small enough for its towers. */
export function plateChipR(v: VoteGeometry, p: PlateSpot): number {
  return Math.min(v.r * 1.25, (p.rx * 0.92) / (p.towers + 0.15));
}

/** Where the i-th chip on a plate lies: its tower, its level in the tower; and its radius. */
export function stackPos(
  v: VoteGeometry,
  p: PlateSpot,
  i: number,
): [number, number, number] {
  const rr = plateChipR(v, p),
    tower = Math.floor(i / TOWER_CAP),
    level = i % TOWER_CAP;
  const off = (tower - (p.towers - 1) / 2) * rr * 2.15;
  return [p.x + off, p.y - rr * TOWER_STEP - level * rr * TOWER_STEP, rr];
}

/** The place card under a plate, on the cloth's drop. */
export function placeCardBox(v: VoteGeometry, p: PlateSpot, nCands: number) {
  const cw = Math.min(p.rx * 2.3, 0.3 * v.g.pwid, (v.tw / Math.max(1, nCands)) * 0.92),
    ch = v.drop * 0.74;
  return { x: p.x - cw / 2, y: v.topY + v.drop * 0.16, w: cw, h: ch };
}

/**
 * The camera's push-in for the count: 1.32, bringing the table's front edge to where the bench's
 * came (bench 64), though the owner's table stands lower.
 */
export function countShot(v: VoteGeometry) {
  const k = CAMERA_ZOOM_MAX;
  // the bench's table edge (railY − 0.15 of the puppet), and its shot: scaled about (cx, edge −
  // 0.04H), then the picture dropped 0.015H, as one fixed point (the one scale alone leaves
  // where it is); moved down k/(k − 1) of the way the table did, the edge lands where it did
  const edge = v.g.railY - 0.15 * v.g.ph,
    bench = edge - 0.04 * STAGE_H - (0.015 * STAGE_H) / (k - 1);
  return { scale: k, x: v.cx, y: bench + (k * (v.topY - edge)) / (k - 1) };
}

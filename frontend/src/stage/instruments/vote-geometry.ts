/**
 * Where the vote's things stand, in units: the table on its lift, the glass jar, the plates
 * along the table's front edge, the place cards on the cloth, the chips on the plates. The
 * table rises through the trap, so all of it is sized from the same puppet box the trap is,
 * and a number here can be checked against the vote bench (rev 64 `VG`, `jar`, `plateSpots`,
 * `stackPos`, `cardSVG`) by eye.
 */
import { carLines } from '../paint/window';
import { CAMERA_ZOOM_MAX, STAGE_H, STAGE_W, type StageGeometry } from '../units';
import { trapGeometry } from './Floor';

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
  /** Where the table's feet stand on the lift. */
  footY: number;
  /** A ballot chip's radius. */
  r: number;
  /** The jar's base line on the table. */
  base: number;
  /** The trap's opening, and the lift's slab inside it. */
  holeTop: number;
  holeBot: number;
  trapW: number;
  slabTop: number;
  slabBot: number;
  floorH: number;
}

export function voteGeometry(g: StageGeometry): VoteGeometry {
  const H = STAGE_H,
    ph = g.ph,
    t = trapGeometry(g),
    { floorH } = carLines(g);
  const tw = t.trapW / 1.1,
    depth = 0.085 * ph,
    topY = g.railY - 0.15 * ph;
  const rim = Math.max(4, 0.011 * STAGE_W);
  return {
    g,
    cx: g.cx,
    topY,
    depth,
    tw,
    bw: tw * 0.9,
    drop: 0.13 * ph,
    footY: g.railY + 0.012 * H,
    r: Math.max(8, 0.078 * g.pwid),
    base: topY - depth * 0.62,
    holeTop: t.holeTop,
    holeBot: t.holeBot,
    trapW: t.trapW,
    slabTop: t.holeTop + rim,
    slabBot: t.holeBot - rim,
    floorH,
  };
}

/**
 * The painted glass and lid (SPRITES.props), in their files' pixels: the file's size and the
 * painted thing's box inside it. The glass's lines are fractions of its height above its foot.
 */
export const GLASS_PX = { W: 988, H: 1446, x: 8, y: 8, w: 972, h: 1430 } as const;
/** The lid's skirt is 1030 px wide; the string ties round the ring's top bar, 38 px down. */
export const LID_PX = {
  W: 1154,
  H: 827,
  x: 8,
  y: 8,
  w: 1138,
  h: 811,
  skirt: 1030,
  tie: 38,
} as const;

/** The jar and its lid, upright on the table, where the glass picture has them. */
export function jarGeometry(v: VoteGeometry) {
  const { cx, base, g } = v,
    h = 0.56 * g.ph,
    w = (h * GLASS_PX.w) / GLASS_PX.h;
  // measured on the picture: the lip's width, its foot, the mouth, the neck's foot, the inner floor
  const wN = w * 0.705,
    yL = base - h * 0.907,
    yR = base - h * 0.968,
    yN = base - h * 0.824,
    floor = base - h * 0.15;
  // the lid's skirt as wide as the lip it screws over, its foot on the lip's foot
  const ks = wN / LID_PX.skirt,
    lw = LID_PX.w * ks,
    lh = LID_PX.h * ks,
    ly = yL - lh;
  // the tipped pose: turned on its side about the base's centre, a little smaller for being
  // upstage, set down at the back rail to the right
  const sc = 0.62,
    ang = -96,
    rad = (ang * Math.PI) / 180;
  const cs = Math.cos(rad),
    sn = Math.sin(rad);
  const cy0 = -h / 2,
    cX = -cy0 * sn * sc,
    cY = cy0 * cs * sc;
  const wantX = cx + 0.22 * v.tw,
    wantY = v.topY - v.depth * 1.05 - w * sc * 0.5;
  const dx = wantX - cx - cX,
    dy = wantY - base - cY;
  const m = base - yR;
  return {
    h,
    w,
    wN,
    yN,
    yR,
    /** Where the chips in the jar lie: on the thick glass bottom. */
    floor,
    /** The lid picture's box, its scale (units a pixel), and where its string ties on. */
    lid: { lh, lw, ly, ks, knob: ly + LID_PX.tie * ks, cx, cy: ly + lh / 2 },
    /** Lifted off and tilted, hung on its string. */
    lidUp: { x: 0.07 * g.pwid, y: -0.11 * g.ph, rot: -16 },
    /** The top of the lid's ring, where the light's special stops. */
    top: ly,
    tip: { ox: cx, oy: base, dx, dy, ang, sc },
    /** The tipped jar's mouth, where a counted chip leaves it. */
    mouth: { x: cx + dx + m * sn * sc, y: base + dy - m * cs * sc },
  };
}

/** Chips in a pile, per = 4 to a layer, each layer a little higher and staggered. */
export function pileSpots(v: VoteGeometry, n: number): [number, number][] {
  const J = jarGeometry(v),
    base = J.floor,
    // inside the glass's walls
    halfW = J.w * 0.44,
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

/** A counted chip's thickness, as a fraction of its radius (the tower's step); chips per tower. */
export const TOWER_STEP = 0.45;
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

/** One plate per candidate along the front edge, abstain's last, sized to the full tally. */
export function plateSpots(
  v: VoteGeometry,
  cands: readonly string[],
  counts: Record<string, number>,
): PlateSpot[] {
  const n = cands.length,
    span = v.tw * 0.84,
    gap = span / Math.max(1, n);
  const rx0 = Math.min(0.2 * v.g.pwid, gap * 0.44);
  return cands.map((c, i) => {
    const rx = rx0;
    return {
      c,
      x: v.cx - span / 2 + gap * (i + 0.5),
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

/** The camera's push-in for the count: 1.32 about a point just above the table (bench 64). */
export function countShot(v: VoteGeometry) {
  const k = CAMERA_ZOOM_MAX;
  // the bench scales about (cx, topY − 0.04H) and then drops the picture 0.015H; one fixed
  // point says the same: the point that scale alone leaves where it is
  return { scale: k, x: v.cx, y: v.topY - 0.04 * STAGE_H - (0.015 * STAGE_H) / (k - 1) };
}

/**
 * Where the vote's things stand, in units: the table on its lift, the glass jar, the plates
 * along the table's front edge, the place cards on the cloth, the chips on the plates. The
 * table rises through the trap, so all of it is sized from the same puppet box the trap is,
 * and a number here can be checked against the vote bench (rev 64 `VG`, `jar`, `plateSpots`,
 * `stackPos`, `cardSVG`) by eye.
 */
import { carLines } from '../paint/window';
import { STAGE_H, STAGE_W, type StageGeometry } from '../units';
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

/** The jar's outline and its lid, upright on the table. */
export function jarGeometry(v: VoteGeometry) {
  const { cx, base, g } = v,
    h = 0.56 * g.ph,
    w = 0.42 * g.pwid;
  const wN = w * 0.66,
    yS = base - h * 0.6,
    yN = base - h * 0.82,
    yR = base - h * 0.93,
    rb = w * 0.14;
  const lh = h * 0.11,
    lw = wN * 1.12,
    ly = yR - lh * 0.72;
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
    yS,
    yN,
    yR,
    rb,
    /** The lid: a brass band, a dome and a knob; where its string ties on. */
    lid: { lh, lw, ly, knob: ly - h * 0.105 - 7, cx, cy: ly + lh / 2 },
    /** Lifted off and tilted, hung on its string. */
    lidUp: { x: 0.07 * g.pwid, y: -0.11 * g.ph, rot: -16 },
    /** The top of the lifted lid, where the light's special stops. */
    top: ly - h * 0.12,
    tip: { ox: cx, oy: base, dx, dy, ang, sc },
    /** The tipped jar's mouth, where a counted chip leaves it. */
    mouth: { x: cx + dx + m * sn * sc, y: base + dy - m * cs * sc },
  };
}

/** Chips in a pile, per = 4 to a layer, each layer a little higher and staggered. */
export function pileSpots(v: VoteGeometry, n: number): [number, number][] {
  const J = jarGeometry(v),
    base = v.base - J.rb * 0.3,
    halfW = J.w / 2 - 3,
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
  /** The candidate: a seat, or `abstain` for the upturned saucer. */
  c: string;
  x: number;
  y: number;
  rx: number;
  ry: number;
  /** How many towers the plate's chips need, from the full tally. */
  towers: number;
}

/** One plate per candidate along the front edge, the saucer last, sized to the full tally. */
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
    const rx = c === 'abstain' ? rx0 * 1.18 : rx0;
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
  const ab = p.c === 'abstain';
  return Math.min(
    v.r * (ab ? 1.05 : 1.25),
    (p.rx * (ab ? 0.72 : 0.92)) / (p.towers + 0.15),
  );
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
  const lift = p.c === 'abstain' ? p.ry * 1.3 : 0;
  return [p.x + off, p.y - rr * TOWER_STEP - level * rr * TOWER_STEP - lift, rr];
}

/** The place card under a plate, on the cloth's drop. */
export function placeCardBox(v: VoteGeometry, p: PlateSpot, nCands: number) {
  const cw = Math.min(p.rx * 2.3, 0.3 * v.g.pwid, (v.tw / Math.max(1, nCands)) * 0.92),
    ch = v.drop * 0.74;
  return { x: p.x - cw / 2, y: v.topY + v.drop * 0.16, w: cw, h: ch };
}

/** The camera's push-in for the count: 1.32 about a point just above the table (bench 64). */
export function countShot(v: VoteGeometry) {
  const k = 1.32;
  // the bench scales about (cx, topY − 0.04H) and then drops the picture 0.015H; one fixed
  // point says the same: the point that scale alone leaves where it is
  return { scale: k, x: v.cx, y: v.topY - 0.04 * STAGE_H - (0.015 * STAGE_H) / (k - 1) };
}

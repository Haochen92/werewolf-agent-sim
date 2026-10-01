/**
 * A dark sheet with soft holes in it, drawn without an SVG mask. iPhone Safari kills a page that
 * masks a whole stage (found 2026-10-01 with the GPU probe, `styles/gpu-probe.css`), and the
 * house light, the car's veil and the night rooms' light were each a dark rect masked by soft
 * shapes. Here the same darkness is plain paths: the sheet is one path with its holes cut out
 * (fill-rule evenodd), and each hole is filled from inside with a radial gradient of the
 * sheet's own colour, clear at its middle and as dark as the sheet at its rim, so the two meet
 * without a seam.
 *
 * Holes may overlap (a lamp under its special, the pool under the window's light). A mask
 * multiplied overlapping holes together; plain paint can only add darkness, so where two holes
 * overlap each place takes the clearer of the two (with helper holes over the overlap to come
 * near the product, `overlaps`), and the line between them runs where both are equally dark, so
 * that line never shows either. The pieces are found on a grid: each grid point belongs to
 * whichever hole (or the sheet) is clearest there, and the borders between them are traced
 * between the points (marching squares), each border shared exactly by the two pieces it
 * separates.
 */

/** A softness profile: [t, clear] stops from a hole's middle (t 0) to its rim (t 1, clear 0). */
export type Profile = readonly (readonly [number, number])[];

/** One soft hole: an ellipse, and how clear it is along its radius. */
export interface Hole {
  x: number;
  y: number;
  rx: number;
  ry: number;
  clear: Profile;
}

/** The night rooms' pool of light: wide open, falling away over its outer quarter. */
export const POOL: Profile = [
  [0, 1],
  [0.5, 0.95],
  [0.78, 0.62],
  [1, 0],
];
/** A softer hole, falling away from its middle. */
export const SOFT: Profile = [
  [0, 1],
  [0.6, 0.85],
  [1, 0],
];

/** How clear a profile is at t (0 past the rim). */
export function clearAt(p: Profile, t: number): number {
  if (t >= 1) return 0;
  for (let i = 1; i < p.length; i++)
    if (t <= p[i][0]) {
      const [a, va] = p[i - 1],
        [b, vb] = p[i];
      return b === a ? vb : va + ((vb - va) * (t - a)) / (b - a);
    }
  return 0;
}

/** A profile scaled by a strength (a hole drawn at `a` of its full clearness). */
export const scaled = (p: Profile, a: number): Profile =>
  p.map(([t, c]) => [t, c * a] as const);

/* the error function (Abramowitz and Stegun 7.1.26, to 1.5e-7) and the normal distribution */
const erf = (x: number) => {
  const s = Math.sign(x),
    z = Math.abs(x),
    t = 1 / (1 + 0.3275911 * z);
  return (
    s *
    (1 -
      ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t +
        0.254829592) *
        t *
        Math.exp(-z * z))
  );
};
const Phi = (z: number) => 0.5 * (1 + erf(z / Math.SQRT2));

/** How far past a blurred shape's edge its blur still shows, in blurs (2.5: under 1%). */
const TAIL = 2.5;

/**
 * A disc of radius R under a Gaussian blur of `blur` (an feGaussianBlur's stdDeviation), as a
 * profile reaching out to R + 2.5 blurs: what the house light's blurred mask shapes were.
 */
export function blurredDisc(R: number, blur: number, samples = 14): Profile {
  const O = R + TAIL * blur,
    n = 160;
  // the blurred disc at distance r: the disc's chords, each a strip of the blur's falloff
  const at = (r: number) => {
    let sum = 0;
    for (let i = 0; i <= n; i++) {
      const x = -R + (2 * R * i) / n,
        w = i === 0 || i === n ? 1 : i % 2 ? 4 : 2,
        h = Math.sqrt(Math.max(0, R * R - x * x)),
        g = Math.exp(-((x - r) ** 2) / (2 * blur * blur)) / (blur * Math.sqrt(2 * Math.PI));
      sum += w * g * (Phi(h / blur) - Phi(-h / blur));
    }
    return (sum * (2 * R)) / n / 3;
  };
  return Array.from({ length: samples + 1 }, (_, i) => {
    const t = i / samples;
    return [t, i === samples ? 0 : Math.min(1, at(t * O))] as const;
  });
}

/**
 * A blurred ellipse as a hole: its profile is the blurred disc of the same area, stretched to
 * the ellipse's own radii plus the blur's reach. `a` is how clear it is at full strength.
 */
export function blurredEllipse(
  e: { x: number; y: number; rx: number; ry: number },
  blur: number,
  a = 1,
): Hole {
  const R = Math.sqrt(e.rx * e.ry),
    k = (R + TAIL * blur) / R;
  return {
    x: e.x,
    y: e.y,
    rx: e.rx * k,
    ry: e.ry * k,
    clear: scaled(blurredDisc(R, blur), a),
  };
}

/**
 * Circles on one centre made one hole, as a mask would have stacked them: clear wherever any
 * of them is (1 − the product of what each leaves dark), out to the widest rim.
 */
export function concentric(holes: Hole[]): Hole[] {
  const out: Hole[] = [];
  const groups = new Map<string, Hole[]>();
  for (const h of holes) {
    if (h.rx !== h.ry) {
      out.push(h);
      continue;
    }
    const k = `${h.x},${h.y}`;
    groups.set(k, [...(groups.get(k) ?? []), h]);
  }
  for (const g of groups.values()) {
    if (g.length === 1) {
      out.push(g[0]);
      continue;
    }
    const R = Math.max(...g.map((h) => h.rx));
    // every stop of every circle, at its own radius in the widest one's terms, and between
    const at = [...new Set(g.flatMap((h) => h.clear.map(([t]) => (t * h.rx) / R)))].sort(
      (a, b) => a - b,
    );
    const ts = at.flatMap((t, i) => (i ? [(at[i - 1] + t) / 2, t] : [t]));
    out.push({
      x: g[0].x,
      y: g[0].y,
      rx: R,
      ry: R,
      clear: ts.map(
        (t) =>
          [
            t,
            1 - g.reduce((m, h) => m * (1 - clearAt(h.clear, (t * R) / h.rx)), 1),
          ] as const,
      ),
    });
  }
  return out;
}

/** How dark a hole leaves a point, 0–1 of the sheet; past its rim it keeps rising (1 at the rim). */
function darkAt(h: Hole, x: number, y: number): number {
  const r = Math.hypot((x - h.x) / h.rx, (y - h.y) / h.ry);
  return r < 1 ? 1 - clearAt(h.clear, r) : r;
}

/**
 * Overlapping holes, nearer what a mask made of them. There their darks multiplied (two holes
 * each half open over one place left it a quarter dark), and the pieces can only take the
 * clearer of the two. So more holes join them, each on an ellipse where the overlap is: on each
 * hole's own, and on the box two overlapping holes share. Each is as dark, at each radius, as
 * the product of every hole's dark at its darkest round that ring, so it is never clearer than
 * the mask was anywhere; and it rises to the sheet's dark at its rim, so its piece meets the
 * rest without a seam (the pieces take the clearest, and the clearest of fields that are each
 * unbroken is unbroken). A helper that nowhere beats what is already there is left out.
 */
function overlaps(holes: Hole[]): Hole[] {
  if (holes.length < 2) return holes;
  const n = 14,
    round = 24;
  const P = (x: number, y: number) =>
    holes.reduce((m, h) => m * Math.min(1, darkAt(h, x, y)), 1);
  const out = [...holes];
  const best = (x: number, y: number) =>
    out.reduce((m, h) => Math.min(m, darkAt(h, x, y)), 1);
  const helper = (e: { x: number; y: number; rx: number; ry: number }) => {
    let gain = false;
    const clear = Array.from({ length: n + 1 }, (_, k) => {
      if (k === n) return [1, 0] as const;
      const t = k / n;
      let m = 0;
      for (let q = 0; q < (k ? round : 1); q++) {
        const w = (2 * Math.PI * q) / round,
          x = e.x + t * e.rx * Math.cos(w),
          y = e.y + t * e.ry * Math.sin(w);
        m = Math.max(m, P(x, y));
      }
      for (let q = 0; q < (k ? round : 1) && !gain; q++) {
        const w = (2 * Math.PI * q) / round;
        if (best(e.x + t * e.rx * Math.cos(w), e.y + t * e.ry * Math.sin(w)) > m + 0.05)
          gain = true;
      }
      return [t, 1 - m] as const;
    });
    if (gain) out.push({ ...e, clear });
  };
  const overlapping: [Hole, Hole][] = [];
  for (let i = 0; i < holes.length; i++)
    for (let j = i + 1; j < holes.length; j++) {
      const [a, b] = [holes[i], holes[j]];
      if (Math.abs(a.x - b.x) < a.rx + b.rx && Math.abs(a.y - b.y) < a.ry + b.ry)
        overlapping.push([a, b]);
    }
  for (const h of new Set(overlapping.flat())) helper(h);
  // the box two holes share, and the ellipse round it
  for (const [a, b] of overlapping) {
    const x0 = Math.max(a.x - a.rx, b.x - b.rx),
      x1 = Math.min(a.x + a.rx, b.x + b.rx),
      y0 = Math.max(a.y - a.ry, b.y - b.ry),
      y1 = Math.min(a.y + a.ry, b.y + b.ry);
    helper({
      x: (x0 + x1) / 2,
      y: (y0 + y1) / 2,
      rx: ((x1 - x0) / 2) * Math.SQRT2,
      ry: ((y1 - y0) / 2) * Math.SQRT2,
    });
  }
  return out;
}

/** How dark the holes leave each point, 0–1 of the sheet, as `softHoles` draws them. */
export function darkness(holes: Hole[]): (x: number, y: number) => number {
  const all = overlaps(holes);
  return (x, y) => all.reduce((m, h) => Math.min(m, darkAt(h, x, y)), 1);
}

export interface Box {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

/**
 * The sheet and each hole's piece of it, as path data (fill-rule evenodd): the sheet is the box
 * less every piece, each piece the part of the box where its hole is the clearest thing. The
 * pieces tile the box and share their borders exactly. `step` is the grid, in units; the
 * borders between pieces fall where they are equally dark, so the grid only sets how closely
 * they follow that line. A hole that is nowhere the clearest gets no piece; overlapping holes
 * bring helpers (`overlaps`), which may get one.
 */
export function softHoles(
  given: Hole[],
  box: Box,
  step = 24,
): { sheet: string; pieces: { hole: Hole; d: string }[] } {
  const holes = overlaps(given);
  const nx = Math.max(1, Math.round((box.x1 - box.x0) / step)),
    ny = Math.max(1, Math.round((box.y1 - box.y0) / step)),
    dx = (box.x1 - box.x0) / nx,
    dy = (box.y1 - box.y0) / ny;
  const X = (i: number) => box.x0 + i * dx,
    Y = (j: number) => box.y0 + j * dy;
  // how dark each label leaves a point: -1 is the sheet, always 1
  const val = (l: number, x: number, y: number) => (l < 0 ? 1 : darkAt(holes[l], x, y));
  const label: number[] = [];
  for (let j = 0; j <= ny; j++)
    for (let i = 0; i <= nx; i++) {
      let best = -1,
        bv = 1;
      for (let k = 0; k < holes.length; k++) {
        const h = holes[k];
        // outside a hole's box it is darker than the sheet: skip it
        if (Math.abs(X(i) - h.x) >= h.rx || Math.abs(Y(j) - h.y) >= h.ry) continue;
        const v = darkAt(h, X(i), Y(j));
        if (v < bv) {
          best = k;
          bv = v;
        }
      }
      label.push(best);
    }
  const L = (i: number, j: number) => label[j * (nx + 1) + i];

  const pts = new Map<string, [number, number]>();
  const segs = new Map<number, [string, string][]>();
  const seg = (l: number, a: string, b: string) => {
    if (!segs.has(l)) segs.set(l, []);
    segs.get(l)!.push([a, b]);
  };
  const vert = (i: number, j: number) => {
    const k = `v${i},${j}`;
    if (!pts.has(k)) pts.set(k, [X(i), Y(j)]);
    return k;
  };
  // where the border crosses the grid edge from (i,j) to (i2,j2): where both sides are equally dark
  const cross = (i: number, j: number, i2: number, j2: number) => {
    const k = `e${i},${j},${i2},${j2}`;
    if (!pts.has(k)) {
      const a = L(i, j),
        b = L(i2, j2),
        fa = val(a, X(i), Y(j)) - val(b, X(i), Y(j)),
        fb = val(a, X(i2), Y(j2)) - val(b, X(i2), Y(j2)),
        t = fa === fb ? 0.5 : Math.min(1, Math.max(0, fa / (fa - fb)));
      pts.set(k, [X(i) + t * (X(i2) - X(i)), Y(j) + t * (Y(j2) - Y(j))]);
    }
    return k;
  };

  // inside: each cell's corners in turn round it, and the borders between them
  for (let j = 0; j < ny; j++)
    for (let i = 0; i < nx; i++) {
      const c: [number, number][] = [
        [i, j],
        [i + 1, j],
        [i + 1, j + 1],
        [i, j + 1],
      ];
      const xs: { p: string; before: number; after: number }[] = [];
      for (let k = 0; k < 4; k++) {
        const [a, b] = [c[k], c[(k + 1) % 4]],
          la = L(...a),
          lb = L(...b);
        if (la === lb) continue;
        // each edge named from its lower corner, so both cells find the same point
        const p = a[0] + a[1] <= b[0] + b[1] ? cross(...a, ...b) : cross(...b, ...a);
        xs.push({ p, before: la, after: lb });
      }
      if (xs.length === 2) {
        seg(xs[0].before, xs[0].p, xs[1].p);
        seg(xs[0].after, xs[0].p, xs[1].p);
      } else if (xs.length > 2) {
        // three pieces meet, or two cross: every border runs to the cell's middle
        const m = `c${i},${j}`;
        pts.set(m, [X(i) + dx / 2, Y(j) + dy / 2]);
        for (const x of xs) {
          seg(x.before, x.p, m);
          seg(x.after, x.p, m);
        }
      }
    }
  // round the box's edge, each piece closed along it
  const edge = (i: number, j: number, i2: number, j2: number) => {
    const a = L(i, j),
      b = L(i2, j2),
      va = vert(i, j),
      vb = vert(i2, j2);
    if (a === b) seg(a, va, vb);
    else {
      const p = cross(i, j, i2, j2);
      seg(a, va, p);
      seg(b, p, vb);
    }
  };
  for (let i = 0; i < nx; i++) {
    edge(i, 0, i + 1, 0);
    edge(i, ny, i + 1, ny);
  }
  for (let j = 0; j < ny; j++) {
    edge(0, j, 0, j + 1);
    edge(nx, j, nx, j + 1);
  }

  // each label's borders joined into closed loops, in whole units (a shared point rounds the
  // same in both pieces), a point dropped where it lies on the straight line through its two
  // neighbours (the box's edges), which leaves the shape exactly as it was
  const xy = (p: string) => pts.get(p)!.map(Math.round) as [number, number];
  const straight = (a: [number, number], b: [number, number], c: [number, number]) =>
    (b[0] - a[0]) * (c[1] - b[1]) === (b[1] - a[1]) * (c[0] - b[0]);
  const path = (l: number) => {
    const list = segs.get(l) ?? [];
    const at = new Map<string, number[]>();
    list.forEach(([a, b], n) => {
      for (const p of [a, b]) at.set(p, [...(at.get(p) ?? []), n]);
    });
    const used = new Array(list.length).fill(false);
    let d = '';
    for (let s = 0; s < list.length; s++) {
      if (used[s]) continue;
      used[s] = true;
      const [start, first] = list[s];
      const loop = [start];
      let cur = first;
      while (cur !== start) {
        loop.push(cur);
        const n = at.get(cur)!.find((k) => !used[k]);
        if (n === undefined) break;
        used[n] = true;
        cur = list[n][0] === cur ? list[n][1] : list[n][0];
      }
      const ring = loop.map(xy).filter((p, k, r) => {
        const q = r[(k + r.length - 1) % r.length];
        return p[0] !== q[0] || p[1] !== q[1];
      });
      const kept = ring.filter(
        (p, k) =>
          !straight(
            ring[(k + ring.length - 1) % ring.length],
            p,
            ring[(k + 1) % ring.length],
          ),
      );
      // the first point, then each the whole units on from the last (exact: no drift)
      if (kept.length > 2)
        d +=
          `M${kept[0].join(',')}l` +
          kept
            .slice(1)
            .map((p, k) => `${p[0] - kept[k][0]},${p[1] - kept[k][1]}`)
            .join(' ') +
          'Z';
    }
    return d;
  };
  const pieces: { hole: Hole; d: string }[] = [];
  holes.forEach((hole, k) => {
    if (segs.has(k)) pieces.push({ hole, d: path(k) });
  });
  return { sheet: path(-1), pieces };
}

/**
 * A hole's fill: a radial gradient of the sheet's colour across its ellipse, `alpha` (the
 * sheet's own darkness) times how dark the hole leaves each radius, so it meets the sheet at
 * its rim and pads on past it at the sheet's darkness.
 */
export function holeGradient(id: string, h: Hole, color: string, alpha: number): string {
  const n = (v: number) => String(Math.round(v * 1000) / 1000);
  const stops = h.clear.map(([t, c]) => [t, alpha * (1 - c)] as const);
  // a stop the line between its neighbours already passes (to within 0.005) says nothing
  const kept = stops.filter(([t, a], k) => {
    if (k === 0 || k === stops.length - 1) return true;
    const [t0, a0] = stops[k - 1],
      [t1, a1] = stops[k + 1];
    return Math.abs(a0 + ((a1 - a0) * (t - t0)) / (t1 - t0) - a) > 0.005;
  });
  return (
    `<radialGradient id="${id}" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="1" gradientTransform="translate(${n(h.x)} ${n(h.y)}) scale(${n(h.rx)} ${n(h.ry)})">` +
    kept
      .map(
        ([t, a]) => `<stop offset="${n(t)}" stop-color="${color}" stop-opacity="${n(a)}"/>`,
      )
      .join('') +
    `</radialGradient>`
  );
}

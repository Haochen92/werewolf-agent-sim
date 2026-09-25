/**
 * Lays a flat rectangle onto any four-cornered shape on the stage, in perspective: the CSS
 * `matrix3d` that carries a w×h box's corners onto four points. This is how the walnut tile
 * (a flat picture) becomes the top of a table seen from the house, its planks narrowing toward
 * the back; a plain SVG pattern can only shear or scale, never foreshorten (handoff §1:
 * "wood is a seamless tile laid on vector geometry with a homography").
 */

export type Pt = [number, number];

/** Solves the 8×8 system for the projective map taking (0,0) (w,0) (w,h) (0,h) to `to`. */
function solve(w: number, h: number, to: readonly [Pt, Pt, Pt, Pt]): number[] {
  const from: Pt[] = [
    [0, 0],
    [w, 0],
    [w, h],
    [0, h],
  ];
  const A: number[][] = [];
  const b: number[] = [];
  for (let i = 0; i < 4; i++) {
    const [x, y] = from[i],
      [u, v] = to[i];
    A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]);
    b.push(u);
    A.push([0, 0, 0, x, y, 1, -v * x, -v * y]);
    b.push(v);
  }
  // Gaussian elimination with partial pivoting
  const n = 8;
  for (let c = 0; c < n; c++) {
    let p = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
    [A[c], A[p]] = [A[p], A[c]];
    [b[c], b[p]] = [b[p], b[c]];
    for (let r = c + 1; r < n; r++) {
      const f = A[r][c] / A[c][c];
      for (let k = c; k < n; k++) A[r][k] -= f * A[c][k];
      b[r] -= f * b[c];
    }
  }
  const x = new Array<number>(n).fill(0);
  for (let r = n - 1; r >= 0; r--) {
    let s = b[r];
    for (let k = r + 1; k < n; k++) s -= A[r][k] * x[k];
    x[r] = s / A[r][r];
  }
  return x;
}

/**
 * The `matrix3d(...)` for a box of w×h whose top-left is at the origin (`transform-origin: 0
 * 0`), mapping its corners, clockwise from the top-left, onto `to`.
 */
export function homography(w: number, h: number, to: readonly [Pt, Pt, Pt, Pt]): string {
  const [a, b, c, d, e, f, g, hh] = solve(w, h, to);
  // column-major 4×4, with z passed through untouched
  const m = [a, d, 0, g, b, e, 0, hh, 0, 0, 1, 0, c, f, 0, 1];
  return `matrix3d(${m.map((x) => +x.toFixed(9)).join(',')})`;
}

/** Where the map sends a point; for tests and for checking a corner by eye. */
export function project(w: number, h: number, to: readonly [Pt, Pt, Pt, Pt], p: Pt): Pt {
  const [a, b, c, d, e, f, g, hh] = solve(w, h, to);
  const z = g * p[0] + hh * p[1] + 1;
  return [(a * p[0] + b * p[1] + c) / z, (d * p[0] + e * p[1] + f) / z];
}

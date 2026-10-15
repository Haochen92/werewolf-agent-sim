/**
 * One-off: bakes the case file's stamp ink as a small seamless mask tile (owner, 2026-09-29: a
 * stamp's worn ink, with no live SVG filter). White everywhere, its alpha the ink's coverage:
 * mostly solid, a little uneven, with a scatter of small bare specks where the rubber missed
 * the paper, all wrapped at the edges so the tile repeats without a seam. The stamps use it as
 * a CSS `mask-image` (a still picture: nothing is filtered at run time). Seeded, so a rerun
 * draws the same tile.
 *
 * Run from frontend/: `node scripts/make-stamp-ink.mjs` → src/assets/sprites/textures/ink.webp
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(root, 'src/assets/sprites/textures/ink.webp');
const N = 128;

// mulberry32: a tiny seeded generator, so the tile is the same on every run
let seed = 0x57a3b;
const rnd = () => {
  seed = (seed + 0x6d2b79f5) | 0;
  let t = seed;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

// the ink's coverage: nearly full, a soft unevenness of a few blotches
const a = new Float32Array(N * N).fill(0.94);
/** A soft round patch of coverage `v`, blended in by `k`, wrapped at the tile's edges. */
function patch(cx, cy, r, v, k) {
  const R = Math.ceil(r) + 1;
  for (let dy = -R; dy <= R; dy++)
    for (let dx = -R; dx <= R; dx++) {
      const d = Math.hypot(dx, dy) / r;
      if (d > 1) continue;
      const x = (((Math.round(cx) + dx) % N) + N) % N,
        y = (((Math.round(cy) + dy) % N) + N) % N;
      const w = k * (1 - d * d);
      a[y * N + x] += (v - a[y * N + x]) * w;
    }
}
for (let i = 0; i < 90; i++) patch(rnd() * N, rnd() * N, 4 + rnd() * 10, 0.72 + rnd() * 0.3, 0.6);
// the bare specks: small, sharp, where the paper shows through
for (let i = 0; i < 260; i++) patch(rnd() * N, rnd() * N, 0.6 + rnd() * 1.4, 0, 0.95);

const out = Buffer.alloc(N * N * 4);
for (let i = 0; i < N * N; i++) {
  out[i * 4] = out[i * 4 + 1] = out[i * 4 + 2] = 255;
  out[i * 4 + 3] = Math.max(0, Math.min(255, Math.round(a[i] * 255)));
}
await sharp(out, { raw: { width: N, height: N, channels: 4 } })
  .webp({ quality: 85, alphaQuality: 90 })
  .toFile(OUT);
console.log('wrote', path.relative(root, OUT));

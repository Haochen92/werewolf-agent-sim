/**
 * One-off: draws the seat rail's cork board as a small seamless tile (HUD pass 2, owner
 * 2026-09-29: the cards are pinned to cork, not hung in the air). Warm, fine-grained: a tan
 * ground, a few thousand granules of lighter and darker cork, and a scatter of dark pits, all
 * wrapped at the edges so the tile repeats without a seam. Seeded, so a rerun draws the same
 * tile.
 *
 * Run from frontend/: `node scripts/make-cork.mjs` → src/assets/sprites/textures/cork.webp
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(root, 'src/assets/sprites/textures/cork.webp');
const N = 192;

// mulberry32: a tiny seeded generator, so the tile is the same on every run
let seed = 0x6c07c0;
const rnd = () => {
  seed = (seed + 0x6d2b79f5) | 0;
  let t = seed;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

const px = new Float32Array(N * N * 3);
const GROUND = [168, 118, 70];
for (let i = 0; i < N * N; i++) px.set(GROUND, i * 3);

/** A granule: a small jittered ellipse of one tone, blended in, wrapped at the tile's edges. */
function granule(cx, cy, rx, ry, rgb, a) {
  const r = Math.ceil(Math.max(rx, ry)) + 1;
  for (let dy = -r; dy <= r; dy++)
    for (let dx = -r; dx <= r; dx++) {
      const d = (dx / rx) ** 2 + (dy / ry) ** 2;
      if (d > 1) continue;
      const x = (((Math.round(cx) + dx) % N) + N) % N,
        y = (((Math.round(cy) + dy) % N) + N) % N;
      const k = a * (1 - d * 0.5),
        o = (y * N + x) * 3;
      for (let c = 0; c < 3; c++) px[o + c] += (rgb[c] - px[o + c]) * k;
    }
}

const TONES = [
  [196, 145, 90],
  [182, 130, 78],
  [150, 101, 58],
  [128, 84, 46],
  [210, 160, 104],
];
for (let i = 0; i < 5200; i++) {
  const t = TONES[Math.floor(rnd() * TONES.length)];
  const s = 0.7 + rnd() * 1.6;
  granule(
    rnd() * N,
    rnd() * N,
    s * (0.7 + rnd() * 0.6),
    s * (0.7 + rnd() * 0.6),
    t,
    0.55 + rnd() * 0.35,
  );
}
// the pits: small dark holes between the granules
for (let i = 0; i < 420; i++)
  granule(rnd() * N, rnd() * N, 0.6 + rnd() * 0.7, 0.6 + rnd() * 0.7, [86, 54, 28], 0.7);

const out = Buffer.alloc(N * N * 3);
for (let i = 0; i < px.length; i++) out[i] = Math.max(0, Math.min(255, Math.round(px[i])));
await sharp(out, { raw: { width: N, height: N, channels: 3 } })
  .webp({ quality: 82 })
  .toFile(OUT);
console.log('wrote', path.relative(root, OUT));

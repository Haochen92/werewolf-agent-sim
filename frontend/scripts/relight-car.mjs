/**
 * One-off: lights the dining car's fitted painting (the output of `fit-car.mjs`) for the day
 * and for the night, and writes the two WebPs the build ships. Both come from the one painting,
 * so they line up exactly and the day-to-night fade never shifts a panel. (A night painted
 * separately by ChatGPT, 2026-09-29, redrew the room: the window changed shape and props moved.)
 *
 * Day (owner's pick 2026-09-29, "warm"): the wall lantern and the table lamps are lit and cast
 * soft pools, the corners dim a little. Night: the room goes dark and warm, the lamps keep
 * pools of light, and the far edges and the ceiling fall toward black. The glass stays
 * transparent in both.
 *
 * Run from frontend/:  node scripts/relight-car.mjs
 * It reads claude_artifacts/design/rasters/car-day.png and writes src/assets/sprites/car/
 * {day,night}.webp. The lamp positions are in stage units on the fitted 1600×900 painting
 * (measured 2026-09-29); move them if a new painting puts its lamps elsewhere.
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(root, 'claude_artifacts/design/rasters/car-day.png');
const OUT = path.join(root, 'src/assets/sprites/car');

// [x, y, rx, ry, strength]
const LIGHTS = {
  day: {
    ambient: 0.62,
    cap: 1.8,
    pools: [
      [45, 400, 300, 320, 0.35], // left table lamp
      [1555, 400, 300, 320, 0.35], // right table lamp
      [1485, 175, 190, 210, 0.4], // wall lantern
      [1485, 190, 30, 40, 1.3], // the lantern's flame
    ],
    warm: [1.0, 0.86, 0.68],
    warmMix: 0.25,
    edge: 0.35,
    ceiling: 0.3,
  },
  night: {
    ambient: 0.16,
    cap: 1.6,
    pools: [
      [45, 400, 260, 300, 1.0],
      [1555, 400, 260, 300, 1.0],
      [1485, 175, 170, 190, 0.95],
      [800, 330, 560, 190, 0.1], // a little light off the window
      [45, 390, 60, 55, 1.2],
      [1555, 390, 60, 55, 1.2],
      [1485, 190, 35, 45, 2.0],
    ],
    warm: [1.0, 0.78, 0.52],
    warmMix: 0.45,
    edge: 0.55,
    ceiling: 0.45,
  },
};

const { data, info } = await sharp(SRC).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
const { width: W, height: H } = info;

for (const [name, L] of Object.entries(LIGHTS)) {
  const out = Buffer.alloc(data.length);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      let light = L.ambient;
      for (const [px, py, rx, ry, k] of L.pools)
        light += k * Math.exp(-(((x - px) / rx) ** 2 + ((y - py) / ry) ** 2));
      light = Math.min(light, L.cap);
      // darker toward the far left and right, and under the ceiling
      const edge = Math.abs(x - W / 2) / (W / 2);
      const shade = Math.max(
        0,
        1 - L.edge * edge ** 3 - L.ceiling * Math.max(0, Math.min(1, (140 - y) / 140)),
      );
      const i = (y * W + x) * 4;
      for (let c = 0; c < 3; c++) {
        const tint = 1 - L.warmMix + L.warmMix * L.warm[c];
        out[i + c] = Math.round(Math.min(1, (data[i + c] / 255) * light * tint * shade) * 255);
      }
      out[i + 3] = data[i + 3];
    }
  }
  const file = path.join(OUT, `${name}.webp`);
  await sharp(out, { raw: { width: W, height: H, channels: 4 } })
    .webp({ quality: 85, alphaQuality: 100, effort: 6 })
    .toFile(file);
  console.log(`wrote ${path.relative(root, file)}`);
}

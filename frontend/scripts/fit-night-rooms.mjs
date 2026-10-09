/**
 * One-off: turns night room masters into the stage's room pictures (stage_architecture.md §4
 * "The night rooms"), for rooms painted on the plan with an empty white or transparent glass
 * (docs/night_rooms_brief.md). The five first rooms had a checkerboard in the glass and were
 * cleared by an unrecorded script; this is the recipe from 2026-10-07 on.
 *
 * Glass: flooded from the glass's middle through pale pixels, inside the plan's glass box grown
 * a little, so a pale prop outside the brass rim is never reached. Each flooded pixel's whiteness
 * becomes its transparency, and its colour is taken back out of the white it was mixed with, so
 * the rim's soft edge keeps its brass and leaves no pale halo over the night behind the glass.
 * Then the band from the rack to the floor (1536×915 from y 40), WebP quality 82, alpha 100.
 *
 * It prints what `ROOMS` in paint/compartment.ts needs, in master px: the glass's rounded rect
 * and the brightest point on the table (the light's flame or glow). It never overwrites a
 * shipped room unless `--force` is given.
 *
 * Run from frontend/: `node scripts/fit-night-rooms.mjs sentinel trailseer …`
 */
import { stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(root, 'claude_artifacts/design/rasters/rooms');
const OUT = path.join(root, 'src/assets/sprites/rooms');
const BOX = { x0: 891 - 8, x1: 1339 + 8, y0: 251 - 8, y1: 527 + 8 }; // the plan's glass, grown
const SEED = [1115, 389]; // the glass's middle
const PALE = 150; // darkest channel at or above this is glass or its mix with the rim
const CLEAR = 240; // at or above this, fully clear
const CROP = { top: 40, height: 915 };
// where a table's light stands: right of the card, under the glass
const LIGHT = { x0: 1150, x1: 1460, y0: 440, y1: 625 };

const force = process.argv.includes('--force');
const ids = process.argv.slice(2).filter((a) => !a.startsWith('--'));
if (!ids.length) throw new Error('name the rooms to fit');

for (const id of ids) {
  const dest = path.join(OUT, `${id}.webp`);
  if (!force && (await stat(dest).catch(() => null))) {
    console.log(`${id}: ${path.relative(root, dest)} exists, skipped (--force to redo)`);
    continue;
  }
  const { data, info } = await sharp(path.join(SRC, `${id}.png`))
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });
  const { width: W, height: H } = info;
  const at = (x, y) => (y * W + x) * 4;
  const dark = (i) => Math.min(data[i], data[i + 1], data[i + 2]);

  // flood the glass
  const seen = new Uint8Array(W * H);
  const stack = [SEED];
  let gx0 = W,
    gx1 = 0,
    gy0 = H,
    gy1 = 0;
  const firstX = new Map(); // row → leftmost clear-ish x, for the corner radius
  while (stack.length) {
    const [x, y] = stack.pop();
    if (x < BOX.x0 || x > BOX.x1 || y < BOX.y0 || y > BOX.y1) continue;
    const k = y * W + x;
    if (seen[k]) continue;
    seen[k] = 1;
    const i = at(x, y);
    const m = dark(i);
    if (m < PALE) continue;
    const w = Math.min(1, (m - PALE) / (CLEAR - PALE)); // how much of this pixel is the white glass
    const a = 1 - w;
    if (a < 0.02) data[i + 3] = 0;
    else {
      for (let c = 0; c < 3; c++)
        data[i + c] = Math.max(0, Math.min(255, (data[i + c] - w * 255) / a));
      data[i + 3] = Math.round(a * 255);
    }
    if (w >= 0.5) {
      gx0 = Math.min(gx0, x);
      gx1 = Math.max(gx1, x);
      gy0 = Math.min(gy0, y);
      gy1 = Math.max(gy1, y);
      if (!firstX.has(y) || x < firstX.get(y)) firstX.set(y, x);
    }
    stack.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]);
  }
  // corner radius, from the top-left arc: a row d below the top starts o in from the left
  // edge, and a circle of radius r gives (r - o)² + (r - d)² = r², so r = o + d + √(2od);
  // the median over a few rows near the top, where the arc is steep enough to read
  const rs = [];
  for (let d = 4; d <= 14; d++) {
    const o = (firstX.get(gy0 + d) ?? gx0) - gx0;
    if (o > 0) rs.push(o + d + Math.sqrt(2 * o * d));
  }
  rs.sort((p, q) => p - q);
  const r = Math.round(rs[rs.length >> 1] ?? 0);

  // the light: centroid of the brightest pixels on the table, outside the glass
  const lums = [];
  for (let y = LIGHT.y0; y < LIGHT.y1; y++)
    for (let x = LIGHT.x0; x < LIGHT.x1; x++) {
      if (seen[y * W + x] && data[at(x, y) + 3] < 255) continue;
      const i = at(x, y);
      lums.push([0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2], x, y]);
    }
  lums.sort((p, q) => q[0] - p[0]);
  const top = lums.slice(0, 60);
  const fx = Math.round(top.reduce((s, p) => s + p[1], 0) / top.length);
  const fy = Math.round(top.reduce((s, p) => s + p[2], 0) / top.length);

  const out = await sharp(data, { raw: { width: W, height: H, channels: 4 } })
    .extract({ left: 0, top: CROP.top, width: W, height: CROP.height })
    .webp({ quality: 82, alphaQuality: 100, effort: 6 })
    .toFile(dest);
  console.log(
    `${id}: glass { x0: ${gx0}, x1: ${gx1}, y0: ${gy0}, y1: ${gy1}, r: ${r} }, light [${fx}, ${fy}], ${(out.size / 1024).toFixed(0)} KB`,
  );
}

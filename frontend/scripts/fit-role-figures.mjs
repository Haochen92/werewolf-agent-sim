/**
 * One-off: fits role figure masters to the role cards' 720×960 sprite, the way the six from
 * 2026-09-30 were made (measured 2026-10-07; stage_architecture.md §4): the figure's alpha box is
 * cut out, scaled to the full 960 height, and centred on the 720 width, feet on the bottom edge.
 * So a master's own canvas and margins never matter, only its figure's proportion: a box wider
 * than 0.75 of its height would not fit the width, and the script refuses it.
 *
 * Masters: claude_artifacts/design/rasters/roles/<id>.png (gitignored). Output:
 * src/assets/sprites/roles/<id>.webp at quality 85, as convert-sprites.mjs does painted art.
 * It never overwrites a sprite unless `--force` is given; then run small-sprites.mjs for the tiles.
 *
 * Run from frontend/: `node scripts/fit-role-figures.mjs sentinel trailseer …`
 */
import { stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(root, 'claude_artifacts/design/rasters/roles');
const OUT = path.join(root, 'src/assets/sprites/roles');
const W = 720;
const H = 960;
const ALPHA = 8; // a pixel this opaque or more is figure, as the box was measured

const force = process.argv.includes('--force');
const ids = process.argv.slice(2).filter((a) => !a.startsWith('--'));
if (!ids.length) throw new Error('name the roles to fit');

for (const id of ids) {
  const src = path.join(SRC, `${id}.png`);
  const dest = path.join(OUT, `${id}.webp`);
  if (!force && (await stat(dest).catch(() => null))) {
    console.log(`${id}: ${path.relative(root, dest)} exists, skipped (--force to redo)`);
    continue;
  }
  const { data, info } = await sharp(src)
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });
  let x0 = info.width,
    x1 = -1,
    y0 = info.height,
    y1 = -1;
  for (let y = 0; y < info.height; y++)
    for (let x = 0; x < info.width; x++)
      if (data[(y * info.width + x) * 4 + 3] >= ALPHA) {
        if (x < x0) x0 = x;
        if (x > x1) x1 = x;
        if (y < y0) y0 = y;
        if (y > y1) y1 = y;
      }
  const bw = x1 - x0 + 1;
  const bh = y1 - y0 + 1;
  const fitW = Math.round((bw * H) / bh);
  if (fitW > W)
    throw new Error(`${id}: box ${bw}×${bh} is ${(bw / bh).toFixed(2)} wide, over 0.75`);
  const left = Math.floor((W - fitW) / 2);
  const figure = await sharp(src)
    .extract({ left: x0, top: y0, width: bw, height: bh })
    .resize(fitW, H, { kernel: sharp.kernel.lanczos3, fit: 'fill' })
    .png()
    .toBuffer();
  const out = await sharp({
    create: {
      width: W,
      height: H,
      channels: 4,
      background: { r: 0, g: 0, b: 0, alpha: 0 },
    },
  })
    .composite([{ input: figure, left, top: 0 }])
    .webp({ quality: 85, alphaQuality: 100, effort: 6 })
    .toFile(dest);
  console.log(
    `${id}: box ${bw}×${bh} (${(bw / bh).toFixed(2)}) → ${fitW}×${H} at x ${left}, ${(out.size / 1024).toFixed(1)} KB`,
  );
}

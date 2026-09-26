/**
 * One-off: turns the design bundle's PNG masters into the WebP files the build ships
 * (stage_architecture.md §4). The masters stay in the gitignored archive; only the WebP
 * output is committed, so rerun this whenever a master is re-exported.
 *
 * Day figures and chips are flat paletted colour, so near-lossless keeps every edge crisp;
 * plush, kits and wood are painted, where quality 85 is indistinguishable and far smaller.
 * Nothing is resized: sharpness comes from the master, never from upscaling.
 *
 * Run from frontend/: `node scripts/convert-sprites.mjs` (or `… station` for one group only, so
 * the other groups' files are not re-encoded)
 */
import { mkdir, readdir, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(root, 'claude_artifacts/design/sprites');
const OUT = path.join(root, 'src/assets/sprites');

async function listMasters(dir) {
  const found = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) found.push(...(await listMasters(full)));
    else if (/\.(png|jpe?g)$/i.test(entry.name)) found.push(full);
  }
  return found.sort();
}

function optionsFor(rel) {
  const group = rel.split(path.sep)[0];
  if (group === 'day') return { nearLossless: true, alphaQuality: 100, effort: 6 };
  return { quality: 85, alphaQuality: 100, effort: 6 };
}

const kb = (bytes) => (bytes / 1024).toFixed(1);
const rows = [];
let before = 0;
let after = 0;

const only = process.argv[2];
for (const src of await listMasters(SRC)) {
  const rel = path.relative(SRC, src);
  if (only && rel.split(path.sep)[0] !== only) continue;
  const dest = path.join(OUT, rel.replace(/\.(png|jpe?g)$/i, '.webp'));
  await mkdir(path.dirname(dest), { recursive: true });
  const info = await sharp(src).webp(optionsFor(rel)).toFile(dest);
  const inBytes = (await stat(src)).size;
  before += inBytes;
  after += info.size;
  rows.push([rel, `${info.width}x${info.height}`, kb(inBytes), kb(info.size)]);
}

const widths = [0, 1, 2, 3].map((i) => Math.max(...rows.map((r) => r[i].length), 8));
const line = (cells) =>
  cells.map((c, i) => (i === 0 ? c.padEnd(widths[i]) : c.padStart(widths[i]))).join('  ');
console.log(line(['file', 'size', 'png KB', 'webp KB']));
for (const row of rows) console.log(line(row));
console.log(line([`TOTAL (${rows.length} files)`, '', kb(before), kb(after)]));
console.log(`${((1 - after / before) * 100).toFixed(1)}% smaller`);

/**
 * One-off: the phone's copies of the pictures a phone draws far smaller than their files (a
 * census on an iPhone 14, 2026-10-02). Each goes beside its source as `<name>@small.webp`, scaled
 * so the phone's largest drawn size stays at or under it; components pick it on a small stage
 * (`useSmall`), as the backdrop picks its 1×/1.5× sheet. Desktop keeps the full pictures.
 *
 * Each copy takes its source's encoder: the props, cards and window as convert-sprites.mjs
 * (quality 85); the day figures as the cast was made (stage_architecture §4 "The cast": quality
 * 82, method 6), since near-lossless on a resampled figure came out near 3× its source's bytes.
 * Rerun whenever a source on the list is re-exported.
 *
 * Run from frontend/: `node scripts/small-sprites.mjs`
 */
import { readdir, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DIR = path.join(root, 'src/assets/sprites');

// [source under sprites/, scale]
const LIST = [
  ['props/jar-glass.webp', 0.5],
  ['props/jar-lid.webp', 0.35],
  ['props/plate.webp', 0.45],
  // the deal's small cards (Card.tsx SmallCard): 86 units wide, 720×960 → 180×240
  ...[
    'villager',
    'wolf',
    'investigator',
    'vigilante',
    'healer',
    'serial_killer',
    'sentinel',
    'trailseer',
    'sigilist',
    'chanteuse',
    'illusionist',
    'necromancer',
    'speculator',
    'fortune_teller',
  ].map((r) => [`roles/${r}.webp`, 0.25]),
  // only the night's pair is drawn live (a night room's glass); the car's hours are baked
  ['window/night-far.webp', 0.65],
  ['window/night-near.webp', 0.75],
];
for (const character of (await readdir(path.join(DIR, 'day'))).sort())
  for (const state of ['base', 'talking', 'thinking', 'out']) {
    const rel = `day/${character}/${state}.webp`;
    if (await stat(path.join(DIR, rel)).catch(() => null)) LIST.push([rel, 0.8]);
  }

function optionsFor(rel) {
  if (rel.split('/')[0] === 'day') return { quality: 82, alphaQuality: 100, effort: 6 };
  return { quality: 85, alphaQuality: 100, effort: 6 };
}

const kb = (bytes) => (bytes / 1024).toFixed(1);
const rows = [];
let before = 0;
let after = 0;

for (const [rel, scale] of LIST) {
  const src = path.join(DIR, rel);
  const dest = src.replace(/\.webp$/, '@small.webp');
  const { width, height } = await sharp(src).metadata();
  const info = await sharp(src)
    .resize(Math.round(width * scale), Math.round(height * scale), {
      kernel: sharp.kernel.lanczos3,
      fit: 'fill',
    })
    .webp(optionsFor(rel))
    .toFile(dest);
  const inBytes = (await stat(src)).size;
  before += inBytes;
  after += info.size;
  rows.push([
    path.relative(DIR, dest),
    `${width}x${height}`,
    `${info.width}x${info.height}`,
    kb(inBytes),
    kb(info.size),
  ]);
}

const widths = [0, 1, 2, 3, 4].map((i) => Math.max(...rows.map((r) => r[i].length), 8));
const line = (cells) =>
  cells.map((c, i) => (i === 0 ? c.padEnd(widths[i]) : c.padStart(widths[i]))).join('  ');
console.log(line(['file', 'source', 'size', 'src KB', 'small KB']));
for (const row of rows) console.log(line(row));
console.log(line([`TOTAL (${rows.length} files)`, '', '', kb(before), kb(after)]));

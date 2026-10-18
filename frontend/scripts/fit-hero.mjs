/**
 * One-off: the landing hero's pictures (owner, 2026-10-18), from the owner's masters in
 * claude_artifacts/design/rasters/wood/: the night platform as a handmade set, a wide one for a
 * screen wider than tall and a tall one for a phone (each screen fetches only its own), and the
 * cream ticket paper, a tile that repeats without a seam, under both of the hero's tickets.
 *
 * Each is shipped at its master's size or under: the hero is the first thing a visitor sees,
 * so it is not upscaled into more memory (6 MiB decoded each).
 *
 * Run from frontend/: `node scripts/fit-hero.mjs`
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MASTERS = path.join(root, 'claude_artifacts/design/rasters/wood');
const OUT = path.join(root, 'src/assets/site');

const JOBS = [
  { from: 'hero/hero-desktop-v3.png', to: 'hero-wide.webp', width: 1536, quality: 80 },
  { from: 'hero/hero-phone-v2.png', to: 'hero-tall.webp', width: 1024, quality: 80 },
  // shown at 256 css px a tile: 512 px stays sharp on a phone's screen
  { from: 'ticket-paper.png', to: 'ticket-paper.webp', width: 512, quality: 82 },
];

for (const job of JOBS) {
  const info = await sharp(path.join(MASTERS, job.from))
    .removeAlpha()
    .resize({ width: job.width })
    .webp({ quality: job.quality, effort: 6 })
    .toFile(path.join(OUT, job.to));
  console.log(
    `${job.to}: ${info.width}×${info.height}, ${Math.round(info.size / 1024)} KB`,
  );
}

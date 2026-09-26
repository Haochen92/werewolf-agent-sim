/**
 * One-off: the station's pictures exist only inlined in the waiting-room mockup
 * (`claude_artifacts/design/pages/waiting-room.html`, review 2026-09-26 §B6: no masters in the
 * design bundle). This pulls each one out ONCE, by the CSS rule that uses it, into the archive
 * as a PNG master (`claude_artifacts/design/sprites/station/<name>.png`); then
 * `node scripts/convert-sprites.mjs station` turns them into the WebP the build ships, as for
 * every other sprite. The mapping is recorded in stage_architecture.md §4.
 *
 * Not extracted: the chip and figure strips (`.ch`, `.fg`: the stage has its own per-character
 * sprites, §B6) and the ledge's wood (`.ledge`: a 512 px copy of `sprites/wood/walnut.webp`).
 *
 * Run from frontend/: `node scripts/extract-station-sprites.mjs`
 */
import { mkdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MOCK = path.join(root, 'claude_artifacts/design/pages/waiting-room.html');
const OUT = path.join(root, 'claude_artifacts/design/sprites/station');

/** The mockup's CSS rule whose first `url(data:…)` is the picture, and the master's name. */
const PICTURES = [
  ['.sky{', 'sky'],
  ['.fringe{', 'fringe'],
  ['.floor .tile{', 'floor'],
  ['.post{', 'post'],
  ['.lamp{', 'lamp'],
  ['.cars{', 'train'],
  ['.place .blind{', 'blind'],
];

const html = await readFile(MOCK, 'utf8');
await mkdir(OUT, { recursive: true });
for (const [rule, name] of PICTURES) {
  const at = html.indexOf(rule);
  if (at < 0) throw new Error(`no rule ${rule} in the mockup`);
  const m = /url\(data:image\/[a-z+]+;base64,([A-Za-z0-9+/=]+)\)/.exec(html.slice(at));
  if (!m) throw new Error(`no picture in ${rule}`);
  const info = await sharp(Buffer.from(m[1], 'base64'))
    .png()
    .toFile(path.join(OUT, `${name}.png`));
  console.log(`${rule.padEnd(16)} → station/${name}.png  ${info.width}x${info.height}`);
}

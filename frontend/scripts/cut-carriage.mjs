/**
 * Cuts the landing carriage's painted pieces from the waiting room's train
 * (`claude_artifacts/design/sprites/station/train.png`, the master of `sprites/station/train.webp`):
 * redesign handoff 2026-10-14, "Placeholders". Each piece is a rectangle of the painting, saved at
 * the painting's own pixels and shown at half size (Carriage.module.css), so a 2× screen draws it
 * sharp; nothing is ever shown larger than it was painted.
 *
 * The painting's carriage is a long car with small windows; the landing's has one window the size
 * of the game. So only what repeats or keeps its size is cut: the roof (snow and iron), the brass
 * rail, the teak (mirrored into a seamless tile), the window's brass rim (a 9-slice whose rivets
 * repeat along its sides), a bogie, the solebar and the gangway's bellows. The doors stay drawn in
 * CSS over the teak: the painting's doors are a third of the height the carriage needs.
 *
 * Run from frontend/: `node scripts/cut-carriage.mjs`
 */
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(root, 'claude_artifacts/design/sprites/station/train.png');
const OUT = path.join(root, 'src/assets/sprites/carriage');

/** Each piece: its rectangle in the painting (px). */
const PIECES = {
  // one seam-to-seam bay of the roof: the snow's lip and the iron, 120 px a repeat
  roof: { left: 590, top: 22, width: 120, height: 130 },
  // the brass rail under the roof, two rivets a repeat (the same 120 px)
  rail: { left: 590, top: 150, width: 120, height: 22 },
  // plain teak from the lower panel, between the stiles (mirrored below into a seamless tile)
  teak: { left: 282, top: 480, width: 300, height: 88 },
  // a window's brass rim with its rivets, the black glass inside kept as the 9-slice's middle
  frame: { left: 347, top: 195, width: 168, height: 249 },
  // one bogie: two wheels, the frame and the springs between them
  bogie: { left: 548, top: 585, width: 252, height: 115 },
  // the solebar's black beam with its bolts, between the bogies
  solebar: { left: 820, top: 572, width: 200, height: 30 },
  // the gangway's bellows: a band of pleats from the uniform middle, repeated downwards
  bellows: { left: 1796, top: 200, width: 48, height: 200 },
};

await mkdir(OUT, { recursive: true });
const train = sharp(SRC);
for (const [name, box] of Object.entries(PIECES)) {
  let img = sharp(await train.clone().extract(box).png().toBuffer());
  if (name === 'teak') {
    // mirror right and down, so the tile meets itself on every side
    const a = await img.png().toBuffer();
    const b = await sharp(a).flop().png().toBuffer();
    const row = await sharp({
      create: {
        width: box.width * 2,
        height: box.height,
        channels: 4,
        background: '#0000',
      },
    })
      .composite([
        { input: a, left: 0, top: 0 },
        { input: b, left: box.width, top: 0 },
      ])
      .png()
      .toBuffer();
    const flipped = await sharp(row).flip().png().toBuffer();
    img = sharp({
      create: {
        width: box.width * 2,
        height: box.height * 2,
        channels: 4,
        background: '#0000',
      },
    }).composite([
      { input: row, left: 0, top: 0 },
      { input: flipped, left: 0, top: box.height },
    ]);
  }
  const file = path.join(OUT, `${name}.webp`);
  const info = await img.webp({ quality: 86, alphaQuality: 90 }).toFile(file);
  console.log(
    path.relative(root, file),
    `${info.width}×${info.height}`,
    `${(info.size / 1024).toFixed(1)} KB`,
  );
}

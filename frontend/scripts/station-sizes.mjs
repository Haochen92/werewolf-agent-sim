/**
 * The station's pictures at the sizes a screen draws them (frontend lessons 22, 30), from the
 * masters `extract-station-sprites.mjs` pulled out of the waiting-room mockup:
 *
 * - `train@1x.webp`, `sky@1x.webp`: one pixel per stage unit. The shipped `train.webp` and
 *   `sky.webp` (the masters as they are) are about 1.5 pixels per unit and stay the sharper copy;
 *   `stage/scenes/station-pictures.ts` picks between the two by the pixels the stage is drawn at.
 * - `lamp-lit.webp`: the lantern with its glow baked in, at 2 pixels per unit. The glow was an
 *   SVG drop-shadow drawn live over a box four times the lamp's, on every repaint of the
 *   platform; the master itself was 8.6 pixels per unit, for a picture never drawn above 2.
 *
 * The units come from `paint/station.ts` (the train's master geometry, the lamp's height, the
 * glow's spread) and `paint/materials.ts` (the glow's colour): change those and run this again.
 *
 * Run from frontend/: `node scripts/station-sizes.mjs`
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(root, 'claude_artifacts/design/sprites/station');
const OUT = path.join(root, 'src/assets/sprites/station');
const WEBP = { quality: 85, alphaQuality: 100, effort: 6 };

const STAGE_W = 1600;
const STAGE_H = 900;
/** The train master's width and the units one of its pixels covers (station.ts `TRAIN_PX`, `CAR_H`). */
const TRAIN_MASTER_W = 11980;
const TRAIN_K = 432 / (1379 - 61);
/**
 * The lantern: its height in units, the glow's blur and opacity, and the glow's colour. The
 * filter said .55, but Chrome drew it brighter than this bake at .55 (3-4 levels beside the
 * lamp); .65 matches its render within 3 levels a channel (the platform golden, 2026-10-15).
 */
const LAMP_H = 0.13 * STAGE_H;
const GLOW = { sigma: 19.2, opacity: 0.65, rgb: [255, 196, 110] };
/** The baked lamp's density, and the room left round it for the glow (3 sigma, in units). */
const LAMP_PX_PER_UNIT = 2;
const LAMP_PAD = 60;

const kb = (bytes) => `${(bytes / 1024).toFixed(1)} KB`;

async function at1x(name, unitsW) {
  const src = path.join(SRC, `${name}.png`);
  const { width, height } = await sharp(src).metadata();
  const w = Math.round(unitsW);
  const h = Math.round((height * w) / width);
  const info = await sharp(src)
    .resize(w, h, { kernel: 'lanczos3' })
    .webp(WEBP)
    .toFile(path.join(OUT, `${name}@1x.webp`));
  console.log(`${name}@1x.webp  ${info.width}x${info.height}  ${kb(info.size)}`);
}

await at1x('train', TRAIN_MASTER_W * TRAIN_K);
await at1x('sky', STAGE_W);

// the lantern: scaled to its density, padded for the glow, the glow drawn under it as the SVG
// filter drew it (the lamp's own alpha blurred, in the lamp's light at .55), the lamp over it
{
  const src = path.join(SRC, 'lamp.png');
  const { width, height } = await sharp(src).metadata();
  const h = Math.round(LAMP_H * LAMP_PX_PER_UNIT);
  const w = Math.round((width * h) / height);
  const pad = LAMP_PAD * LAMP_PX_PER_UNIT;
  const lamp = await sharp(src).resize(w, h, { kernel: 'lanczos3' }).png().toBuffer();
  const W = w + 2 * pad;
  const H = h + 2 * pad;
  const alpha = await sharp(lamp)
    .ensureAlpha()
    .extend({ top: pad, bottom: pad, left: pad, right: pad, background: '#00000000' })
    .extractChannel('alpha')
    .blur(GLOW.sigma * LAMP_PX_PER_UNIT)
    .raw()
    .toBuffer();
  const glow = Buffer.alloc(W * H * 4);
  for (let i = 0; i < W * H; i++) {
    glow[i * 4] = GLOW.rgb[0];
    glow[i * 4 + 1] = GLOW.rgb[1];
    glow[i * 4 + 2] = GLOW.rgb[2];
    glow[i * 4 + 3] = Math.round(alpha[i] * GLOW.opacity);
  }
  const info = await sharp(glow, { raw: { width: W, height: H, channels: 4 } })
    .composite([{ input: lamp, left: pad, top: pad }])
    .webp(WEBP)
    .toFile(path.join(OUT, 'lamp-lit.webp'));
  console.log(
    `lamp-lit.webp  ${info.width}x${info.height}  ${kb(info.size)}  (pad ${LAMP_PAD} units)`,
  );
}

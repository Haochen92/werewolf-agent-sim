/**
 * One-off: fits a painted dining car (a ChatGPT raster, 1536×1024) onto the 1600×900 stage, so
 * its window lands on the stage's window and its floor on the stage's floor. ChatGPT keeps the
 * look of a layout guide but not its measurements, so every painting needs this.
 *
 * 1. Find the window glass: the painting's glass is flat black (or green), so the run of dark
 *    pixels through the picture's centre gives its box.
 * 2. Scale the whole painting so that box matches the stage's glass, and place it there.
 * 3. The painting's wall under the window is taller than the stage's, so squash that band of
 *    plain panelling until the floor strip lands on the stage's floor, and stretch the floor
 *    below it down to the bottom edge.
 * 4. Cut the glass out (transparent), so the felt window shows through.
 *
 * Run it once on a new ChatGPT download and write over the download: the fitted picture is
 * the only version kept (`claude_artifacts/design/rasters/car-day.png`). `relight-car.mjs`
 * then lights it for the day and the night and writes the WebPs the build ships.
 *
 * Run from frontend/:
 *   node scripts/fit-car.mjs <chatgpt.png> claude_artifacts/design/rasters/car-day.png [floorSrc]
 * floorSrc: where the painting's floor strip ends, in stage units after step 2 (default 771,
 * measured on the 2026-09-29 painting). Check the fit with the guide picture it writes to the
 * system temp folder (the stage's glass and trapdoor drawn over the result).
 */
import os from 'node:os';
import path from 'node:path';
import sharp from 'sharp';

const W = 1600;
const H = 900;
// The stage's glass (paint/window.ts, the dining car plan at hud 'none') and its corner radius.
const GLASS = { x0: 401, y0: 113, x1: 1199, y1: 409, r: 28 };
// The band that gets squashed: from just under the sill rail to the floor strip's bottom edge.
const BAND_TOP = 455;
const FLOOR = 640;

const [inPath, outPath, floorArg] = process.argv.slice(2);
if (!inPath || !outPath) {
  console.error('usage: node scripts/fit-car.mjs <in.png> <out.png> [floorSrc]');
  process.exit(1);
}
const floorSrc = Number(floorArg ?? 771);

// 1. the glass: the dark run through the centre, vertically and horizontally
const { data, info } = await sharp(inPath).removeAlpha().raw().toBuffer({ resolveWithObject: true });
const dark = (x, y) => {
  const i = (y * info.width + x) * 3;
  const [r, g, b] = [data[i], data[i + 1], data[i + 2]];
  return r + g + b < 20 || (g > 200 && r < 60 && b < 60);
};
const cx = Math.round(info.width / 2);
const cy = Math.round(info.height * 0.39);
if (!dark(cx, cy)) throw new Error(`no dark glass at the centre (${cx}, ${cy})`);
let [top, bot, left, right] = [cy, cy, cx, cx];
while (top > 0 && dark(cx, top - 1)) top--;
while (bot < info.height - 1 && dark(cx, bot + 1)) bot++;
while (left > 0 && dark(left - 1, cy)) left--;
while (right < info.width - 1 && dark(right + 1, cy)) right++;
console.log(`glass in the painting: x ${left}–${right}, y ${top}–${bot}`);

// 2. scale so the glass widths match, and place the glass on the stage's
const s = (GLASS.x1 - GLASS.x0) / (right - left);
const sw = Math.round(info.width * s);
const sh = Math.round(info.height * s);
const ox = Math.round(GLASS.x0 - left * s);
const oy = Math.round(GLASS.y0 - top * s);
console.log(`scale ${s.toFixed(4)}, placed at (${ox}, ${oy}); glass height ${((bot - top) * s).toFixed(0)} vs ${GLASS.y1 - GLASS.y0}`);

const scaled = await sharp(inPath).removeAlpha().resize(sw, sh, { kernel: 'lanczos3' }).toBuffer();
// crop the stage's view out of the scaled painting; a few columns short at the sides are
// filled by extending the edge
const vx0 = Math.max(0, -ox);
const vy0 = Math.max(0, -oy);
const view = await sharp(scaled)
  .extract({ left: vx0, top: vy0, width: Math.min(sw - vx0, W - Math.max(0, ox)), height: Math.min(sh - vy0, H - Math.max(0, oy)) })
  .toBuffer({ resolveWithObject: true });
const placed = await sharp(view.data)
  .extend({
    left: Math.max(0, ox),
    top: Math.max(0, oy),
    right: W - Math.max(0, ox) - view.info.width,
    bottom: H - Math.max(0, oy) - view.info.height,
    extendWith: 'copy',
  })
  .toBuffer();

// 3. the bands: kept, squashed, stretched
const bandOf = async (sy0, sy1, ty0, ty1) => ({
  input: await sharp(placed)
    .extract({ left: 0, top: sy0, width: W, height: sy1 - sy0 })
    .resize(W, ty1 - ty0, { fit: 'fill', kernel: 'lanczos3' })
    .toBuffer(),
  left: 0,
  top: ty0,
});
const bands = [
  await bandOf(0, BAND_TOP, 0, BAND_TOP),
  await bandOf(BAND_TOP, floorSrc, BAND_TOP, FLOOR),
  await bandOf(floorSrc, H, FLOOR, H),
];

// 4. the glass cut out
const glassMask = Buffer.from(
  `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><rect width="${W}" height="${H}" fill="#fff"/>` +
    `<rect x="${GLASS.x0}" y="${GLASS.y0}" width="${GLASS.x1 - GLASS.x0}" height="${GLASS.y1 - GLASS.y0}" rx="${GLASS.r}" fill="#000"/></svg>`,
);
const fitted = await sharp({ create: { width: W, height: H, channels: 3, background: '#000' } })
  .composite(bands)
  .png()
  .toBuffer();
const alpha = await sharp(glassMask).extractChannel(0).raw().toBuffer();
// composite leaves an opaque alpha channel; drop it first so the mask becomes the alpha
const rgb = await sharp(fitted).removeAlpha().raw().toBuffer();
await sharp(rgb, { raw: { width: W, height: H, channels: 3 } })
  .joinChannel(alpha, { raw: { width: W, height: H, channels: 1 } })
  .png()
  .toFile(outPath);

// a check picture: the stage's glass and trapdoor over the result
const guides = Buffer.from(
  `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><rect x="${GLASS.x0}" y="${GLASS.y0}" width="${GLASS.x1 - GLASS.x0}" height="${GLASS.y1 - GLASS.y0}" rx="${GLASS.r}" fill="none" stroke="#0f0" stroke-width="3"/>` +
    `<rect x="548" y="590" width="504" height="50" fill="none" stroke="#fc3" stroke-width="3"/></svg>`,
);
const guidePath = path.join(os.tmpdir(), 'fit-car-guides.png');
await sharp(fitted).composite([{ input: guides }]).png().toFile(guidePath);
console.log(`wrote ${outPath}; check the fit in ${guidePath}`);

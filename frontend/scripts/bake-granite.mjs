/**
 * Bakes the landing's granite (Rooms.module.css, the reading room): one 512 px seamless square of
 * dark stone, drawn once here from SVG noise and saved as a webp, so the page repeats a small
 * picture instead of running a noise filter over a wall (owner, 2026-10-14: granite over tile for
 * "What makes it different"). `stitchTiles` makes every noise layer wrap at the square's edges;
 * the mottle is kept faint so the repeat does not show as a grid.
 *
 * Layers, bottom to top: the stone's ground, a broad mottle, a grey grain, dark flecks, a few warm
 * flecks and a few pale crystals (each a noise thresholded through its alpha).
 *
 * Run from frontend/: `node scripts/bake-granite.mjs`
 */
import { writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(root, 'src/assets/site/granite.webp');
const S = 512;

/** A noise layer: its frequency, seed, colour (0–1 rgb) and alpha = gain·noise + bias. */
const layer = (freq, octaves, seed, [r, g, b], gain, bias, name) => `
  <feTurbulence type="fractalNoise" baseFrequency="${freq}" numOctaves="${octaves}" seed="${seed}" stitchTiles="stitch" result="${name}-n"/>
  <feColorMatrix in="${name}-n" type="matrix" values="0 0 0 0 ${r}  0 0 0 0 ${g}  0 0 0 0 ${b}  ${gain} 0 0 0 ${bias}" result="${name}"/>`;

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${S}" height="${S}">
<filter id="f" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">
  <feFlood flood-color="#221f1b" result="base"/>
  ${layer(0.008, 2, 5, [0.03, 0.028, 0.025], -0.8, 0.5, 'mottle')}
  ${layer(0.45, 2, 7, [0.21, 0.195, 0.175], 5, -2.4, 'grey')}
  ${layer(0.25, 2, 11, [0.05, 0.045, 0.04], -8, 3.4, 'dark')}
  ${layer(0.3, 2, 21, [0.3, 0.24, 0.2], 9, -5.6, 'warm')}
  ${layer(0.32, 2, 3, [0.5, 0.47, 0.43], 10, -7.0, 'light')}
  <feMerge>${['base', 'mottle', 'grey', 'dark', 'warm', 'light'].map((n) => `<feMergeNode in="${n}"/>`).join('')}</feMerge>
</filter>
<rect width="${S}" height="${S}" filter="url(#f)"/></svg>`;

const browser = await chromium.launch();
const page = await browser.newPage();
const dataUrl = await page.evaluate(
  async ({ svg, S }) => {
    const img = new Image();
    img.src = 'data:image/svg+xml,' + encodeURIComponent(svg);
    await img.decode();
    const c = document.createElement('canvas');
    c.width = c.height = S;
    c.getContext('2d').drawImage(img, 0, 0);
    return c.toDataURL('image/webp', 0.7);
  },
  { svg, S },
);
await browser.close();
const buf = Buffer.from(dataUrl.split(',')[1], 'base64');
await writeFile(OUT, buf);
console.log(`${path.relative(root, OUT)}: ${S}×${S}, ${(buf.length / 1024).toFixed(1)} KB`);

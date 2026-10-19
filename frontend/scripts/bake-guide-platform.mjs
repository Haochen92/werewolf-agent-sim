/**
 * Bakes the guide introduction's platform picture (owner 2026-10-18): the platform as the game
 * draws it, the full room of nine with six of them kept and spaced evenly between the lamp
 * posts, the signs, tags, plates, ledge and snow hidden. A kept place may show another of the cast
 * (`SWAP`, owner 2026-10-18: the kitsune and the automaton), sized as `puppetBox` sizes a figure.
 * Bake again if the station's picture, its train or the cast changes.
 *
 * Needs a running build with the workbench (any port; the testing port is 3121).
 * Run from frontend/: `node scripts/bake-guide-platform.mjs http://localhost:3121`
 */
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(root, 'src/assets/site/guide/platform.webp');
const base = process.argv[2] ?? 'http://localhost:3121';

/** The nine aboard (`station?beat=4`) by their place: the six kept, and the gap between them. */
const KEEP = [0, 2, 3, 4, 6, 8];
const GAP = 180;
/** A kept place's figure (who the workbench stands there) shown as another of the cast. */
const SWAP = { 2: ['owl', 'kitsune'], 8: ['hare', 'automaton'] };
/** The crop, in stage units (one per css px at 1600×900): post to post, the canopy's beam left out. */
const CROP = { x: 272, y: 52, w: 1256 };
/** The size the guide's Introduction is laid out for. */
const SIZE = { w: 1422, h: 762 };

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1600, height: 900 },
  deviceScaleFactor: 1.2,
});
await page.goto(`${base}/workbench/station?beat=4&animate=0&strip=0`, {
  waitUntil: 'networkidle',
});
await page.waitForTimeout(1500);

// each swap's proportions (manifest.ts `BODY`) and picture, so the new figure stands on the same
// rail at the same body height as the one it replaces
const manifest = await readFile(path.join(root, 'src/assets/manifest.ts'), 'utf8');
const body = (c) => {
  const m = manifest.match(
    new RegExp(`\\n  ${c}: \\{ top: ([\\d.]+), body: ([\\d.]+) \\}`),
  );
  return { top: Number(m[1]), body: Number(m[2]) };
};
const swaps = await Promise.all(
  Object.entries(SWAP).map(async ([i, [from, to]]) => {
    const file = path.join(root, `src/assets/sprites/characters/${to}/base.webp`);
    const { width, height } = await sharp(file).metadata();
    const src = `data:image/webp;base64,${(await readFile(file)).toString('base64')}`;
    return { i: Number(i), from: body(from), to: body(to), aspect: width / height, src };
  }),
);
await page.evaluate((swaps) => {
  const figs = [...document.querySelectorAll('[data-aboard] > div')];
  for (const { i, from, to, aspect, src } of swaps) {
    const img = figs[i].querySelector('img');
    const box = img.parentElement;
    const [left, top, w, h] = ['left', 'top', 'width', 'height'].map((k) =>
      parseFloat(box.style[k]),
    );
    // puppetBox backwards for the one drawn, then forwards for the new one
    const ph = h * from.body;
    const rail = top + h * (from.top + from.body) - h * from.body * 0.08;
    const nh = ph / to.body;
    const nw = nh * aspect;
    Object.assign(box.style, {
      left: `${left + w / 2 - nw / 2}px`,
      top: `${rail - nh * (to.top + to.body) + nh * to.body * 0.08}px`,
      width: `${nw}px`,
      height: `${nh}px`,
    });
    img.removeAttribute('srcset');
    img.src = src;
  }
}, swaps);
await page.waitForTimeout(500);
await page.evaluate(
  ([keep, gap, cx]) => {
    for (const layer of ['instruments', 'floor', 'hud'])
      document.querySelector(`[data-layer="${layer}"]`).style.visibility = 'hidden';
    for (const el of document.querySelectorAll('[class*="plates"], [class*="snow"]'))
      el.style.visibility = 'hidden';
    [...document.querySelectorAll('[data-aboard] > div')].forEach((fig, i) => {
      const k = keep.indexOf(i);
      if (k < 0) {
        fig.style.visibility = 'hidden';
        return;
      }
      const r = fig.querySelector('img').getBoundingClientRect();
      const want = cx + (k - (keep.length - 1) / 2) * gap;
      fig.style.translate = `${want - (r.x + r.width / 2)}px 0`;
    });
  },
  [KEEP, GAP, CROP.x + CROP.w / 2],
);
await page.waitForTimeout(300);
const shot = await page.screenshot({
  clip: {
    x: CROP.x,
    y: CROP.y,
    width: CROP.w,
    height: Math.round((CROP.w * SIZE.h) / SIZE.w),
  },
});
await browser.close();
const info = await sharp(shot)
  .resize(SIZE.w, SIZE.h)
  .webp({ quality: 82, effort: 6 })
  .toFile(OUT);
console.log(
  `${path.relative(root, OUT)}: ${info.width}×${info.height}, ${Math.round(info.size / 1024)} KB`,
);

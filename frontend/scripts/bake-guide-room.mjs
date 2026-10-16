/**
 * Bakes the guide's night room (RoleCardDemo, owner 2026-10-16): the sigilist's compartment as
 * the game draws it, its painting, the night behind the glass and the candle's light, cropped to
 * the window, the table and the candle, with nothing placed in it (the photos, the card, the
 * labels). The guide stands the game's own card on the table over it, so a reader sees the room
 * the card lives in for the price of one small picture, not the room's three (about 12 MB
 * decoded). Bake again if the sigilist's room, the night sky or the room's light changes.
 *
 * Needs a running build with the workbench (any port; the testing port is 3121).
 * Run from frontend/: `node scripts/bake-guide-room.mjs http://localhost:3121`
 */
import { writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(root, 'src/assets/site/guide/sigilist-room.webp');
const base = process.argv[2] ?? 'http://localhost:3121';

/**
 * The crop, in stage units (one unit per css px at a 1600×900 viewport): the room right of the
 * photos. RoleCardDemo.tsx keeps the same numbers to stand the card where the room plan puts it.
 */
const CROP = { x: 880, y: 120, w: 680, h: 700 };
/** Pixels per unit: the guide shows the crop at most 560 css px wide (1.7 px per css px at this). */
const SCALE = 1.4;

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1600, height: 900 },
  deviceScaleFactor: SCALE,
});
// the ten-seat game's night 1, the sigilist's (seat 4's) room in the X-ray replay
await page.goto(`${base}/workbench/rnight?beat=4&viewer=xray&hud=replay&animate=0&strip=0`, {
  waitUntil: 'networkidle',
});
const card = await page.locator('[data-card]').first().getAttribute('data-card');
if (card !== 'sigilist') throw new Error(`expected the sigilist's room, found ${card}`);
// the room alone: its painting, the sky, the haze and the light; nothing placed in it
await page.addStyleTag({
  content: `[data-layer="figures"], [data-layer="stand"], [data-layer="instruments"],
    [data-layer="hud"], nextjs-portal { visibility: hidden !important; }`,
});
await page.evaluate(async () => {
  await document.fonts.ready;
  await Promise.all([...document.images].map((i) => i.decode().catch(() => null)));
});
await page.waitForTimeout(500);
const png = await page.screenshot({
  clip: { x: CROP.x, y: CROP.y, width: CROP.w, height: CROP.h },
});
await browser.close();
const webp = await sharp(png).webp({ quality: 80 }).toBuffer();
await writeFile(OUT, webp);
const meta = await sharp(webp).metadata();
console.log(
  `${path.relative(root, OUT)}: ${meta.width}×${meta.height}, ${(webp.length / 1024).toFixed(1)} KB`,
);

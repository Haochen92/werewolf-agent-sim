/**
 * Draws The Ninth Express's mark (owner, 2026-10-18, from the hero's mock): a gold ring round a
 * pale-gold serif 9 on the night's navy, the 9 being EB Garamond's own lining figure a weight
 * above the title's (700, so it holds at a favicon's size): the mark and the name are one hand.
 * The headlamp it replaces is in git history. One badge, drawn at three levels of detail,
 * because a mark that reads at 64px turns to mud at 16px:
 *
 * - `mark.svg` (48px and up, the hero's rule): the bevelled ring, a fine inner ring, the 9
 * - `mark-md.svg` (24–40px, the nav): the ring a little heavier, the inner ring gone, a larger 9
 * - `mark-sm.svg` (16–20px, also `src/app/icon.svg`, the favicon): the ring heavier still and
 *   the 9 as large as the ring allows
 *
 * and the badge gilded brighter for the first two (`mark-lamp*.svg`), which the nav shows while
 * the brand is pointed at. The home-screen icons (`public/icons/*`, `src/app/apple-icon.png`)
 * are the full badge on the house's dark, the maskable one inside its safe circle.
 *
 * The output is committed; rerun this after changing the badge.
 * Run from frontend/: `node scripts/brand-mark.mjs`
 */
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(root, 'src/assets/brand');

/** EB Garamond's lining 9 (`nine.lf`) at wght 700, font units (y up), OFL. */
const NINE =
  'M70.9 -49.9Q56.4 -49.9 50.5 -44.5Q44.6 -39.1 44.6 -34.5Q44.6 -22.9 53.7 -17.1Q62.7 -11.4 72.6 -10.5Q109.1 -6.4 146.6 15.1Q184 36.7 218.4 68.5Q252.7 100.4 279 134Q299.5 161.2 321.9 199.6Q344.3 238 360.2 285.8Q376.2 333.6 376.2 389Q376.2 422.5 367.6 456.1Q358.9 489.6 344 517.2Q329 544.7 310 561.5Q291.1 578.2 270.6 578.2Q246.8 578.2 229.8 565.7Q212.7 553.1 204.1 528.4Q195.6 503.7 195.6 466.4Q195.6 436.4 206.4 408.2Q217.2 380.1 234.3 362Q251.3 343.9 270.7 343.9Q285.3 343.9 295 347Q304.7 350.2 313.8 354.3Q335 362.9 338 352.1Q340.9 341.4 330.7 329.4Q326.5 321.8 320.6 316.4Q314.7 311 309.1 305.8Q302.1 299.2 286.3 290Q270.5 280.7 251.7 273.9Q232.9 267.1 214.7 267.1Q177.4 267.1 141.2 286.5Q105 305.8 81.2 339.7Q57.5 373.5 57.5 416.9Q57.5 449.2 76.2 486.3Q94.8 523.3 127.7 555.7Q160.5 588.1 203 608.5Q245.5 629 293.8 629Q337.2 629 375.8 610.3Q414.4 591.6 443.9 559.6Q473.5 527.5 490.3 486.1Q507.1 444.6 507.1 400Q507.1 337.2 484.4 281Q461.6 224.8 427.6 178.4Q393.5 132.1 359 98.5Q335.3 75.9 298.6 50.2Q261.9 24.5 220.5 1.7Q179.2 -21.1 139.7 -35.5Q100.2 -49.9 70.9 -49.9Z';
/** The 9's ink box in font units: x 44.6–507.1, y −49.9–629. */
const NINE_BOX = { x0: 44.6, x1: 507.1, y0: -49.9, y1: 629 };

/** The gold, as the hero's rule and the tickets' light have it; gilded, it catches the lamp. */
const GOLD = {
  dim: { ring: ['#f4dc98', '#d4a54f', '#7d561d'], nine: ['#fbe7b0', '#ecc876', '#c09245'] },
  lit: { ring: ['#fff5d2', '#f2cd72', '#a87b32'], nine: ['#fffaea', '#fde3a0', '#e0b660'] },
};
const NAVY = ['#1a2448', '#0b1024'];

/** The 9 scaled to `h` units tall and centred in the 100-unit box (a hair above, by eye). */
function nine(h, fill) {
  const s = h / (NINE_BOX.y1 - NINE_BOX.y0);
  const tx = 50 - ((NINE_BOX.x0 + NINE_BOX.x1) / 2) * s;
  const ty = 49 + ((NINE_BOX.y0 + NINE_BOX.y1) / 2) * s;
  return `<path d="${NINE}" fill="${fill}" transform="translate(${tx.toFixed(2)} ${ty.toFixed(2)}) scale(${s.toFixed(5)} ${(-s).toFixed(5)})"/>`;
}

function mark({ detail, on = false }) {
  const g = on ? GOLD.lit : GOLD.dim;
  // ring width and the 9's height by detail: heavier and larger as the badge gets smaller
  const { ringW, nineH } = {
    full: { ringW: 5, nineH: 52 },
    md: { ringW: 6.5, nineH: 56 },
    small: { ringW: 9, nineH: 62 },
  }[detail];
  const r = 50 - ringW / 2 - 0.5;
  const id = `${detail}${on ? 'L' : ''}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
<defs>
<!-- the 9 is drawn in font units (y up) and flipped, so its gradient runs bottom to top -->
<radialGradient id="n${id}" cx=".42" cy=".38" r=".7"><stop offset="0" stop-color="${NAVY[0]}"/><stop offset="1" stop-color="${NAVY[1]}"/></radialGradient>
<linearGradient id="r${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${g.ring[0]}"/><stop offset=".5" stop-color="${g.ring[1]}"/><stop offset="1" stop-color="${g.ring[2]}"/></linearGradient>
<linearGradient id="g${id}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="${g.nine[0]}"/><stop offset=".55" stop-color="${g.nine[1]}"/><stop offset="1" stop-color="${g.nine[2]}"/></linearGradient>
</defs>
<circle cx="50" cy="50" r="${r}" fill="url(#n${id})"/>
<circle cx="50" cy="50" r="${r}" fill="none" stroke="url(#r${id})" stroke-width="${ringW}"/>
${detail === 'full' ? `<circle cx="50" cy="50" r="${(r - ringW / 2 - 3.2).toFixed(2)}" fill="none" stroke="${g.ring[1]}" stroke-opacity=".4" stroke-width=".9"/>\n` : ''}${nine(nineH, `url(#g${id})`)}
</svg>
`;
}

const files = {
  [path.join(OUT, 'mark.svg')]: mark({ detail: 'full' }),
  [path.join(OUT, 'mark-md.svg')]: mark({ detail: 'md' }),
  [path.join(OUT, 'mark-sm.svg')]: mark({ detail: 'small' }),
  [path.join(OUT, 'mark-lamp.svg')]: mark({ detail: 'full', on: true }),
  [path.join(OUT, 'mark-lamp-md.svg')]: mark({ detail: 'md', on: true }),
  [path.join(root, 'src/app/icon.svg')]: mark({ detail: 'small' }),
};
for (const [file, svg] of Object.entries(files)) {
  writeFileSync(file, svg);
  console.log(path.relative(root, file));
}

// the home-screen icons: the full badge on the house's dark (manifest.ts `background_color`)
const HOUSE = '#0c0a07';
const icons = [
  { file: 'public/icons/icon-192.png', size: 192, badge: 0.8 },
  { file: 'public/icons/icon-512.png', size: 512, badge: 0.8 },
  // a maskable icon may be cut to a circle 80% of its width: the badge stays inside it
  { file: 'public/icons/maskable-512.png', size: 512, badge: 0.72 },
  { file: 'src/app/apple-icon.png', size: 180, badge: 0.8 },
];
for (const icon of icons) {
  const b = Math.round(icon.size * icon.badge);
  const badge = await sharp(Buffer.from(mark({ detail: 'full' })), {
    density: 72 * (b / 100) * 1.0,
  })
    .resize(b, b)
    .png()
    .toBuffer();
  await sharp({
    create: { width: icon.size, height: icon.size, channels: 4, background: HOUSE },
  })
    .composite([{ input: badge, gravity: 'center' }])
    .png()
    .toFile(path.join(root, icon.file));
  console.log(icon.file);
}

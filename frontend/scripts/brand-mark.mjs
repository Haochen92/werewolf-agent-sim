/**
 * Draws the Carriage Nine mark: a brass escutcheon whose keyhole is a 9, with the night and
 * its moon seen through it. One shape, drawn at three levels of detail, because a mark that
 * reads at 64px turns to mud at 16px:
 *
 * - `mark.svg` (48px and up): the disc, its rim, two screws, the 9, the moon, two sparkles
 * - `mark-md.svg` (24–40px, the nav): the disc, a heavier rim, the 9 and the moon
 * - `mark-sm.svg` (16–20px, also `src/app/icon.svg`, the favicon): the disc and a larger 9
 *
 * and the X-ray's state of the first two (`mark-xray*.svg`): the keyhole cut through to the
 * film's dark and its cyan grid, the way the X-ray shows what the agents think.
 *
 * The output is committed; rerun this after changing the shape.
 * Run from frontend/: `node scripts/brand-mark.mjs`
 */
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(root, 'src/assets/brand');

// the site's own colours: aged brass, the stage's night, the X-ray's film and cyan
const C = {
  brass: '#ad8a50',
  rim: '#7a5f33',
  screw: '#e3c88c',
  night: '#111a2e',
  moon: '#ebe6d6',
  film: '#0b191f',
  sure: '#7fdcf2',
  xrayMoon: '#e9f7fb',
};
const f = (n) => +n.toFixed(2);

/**
 * The keyhole 9, in a 64-unit box: a round bowl, and a thick stem down its right edge that
 * hooks left and ends round. `t` is the stem's width, `hy` where the hook's curve begins.
 */
function nine({ cx = 31, cy = 23, r = 12, t = 9, hy = 39 } = {}) {
  const right = cx + r;
  const inner = right - t;
  const hx = cx - 2;
  const R = right - hx;
  const ri = inner - hx;
  // where the stem's inner edge meets the bowl, rounded off so the join has no step
  const crotchY = cy + Math.sqrt(r * r - (inner - cx) ** 2);
  const startX = inner - 2;
  const startY = cy + Math.sqrt(r * r - (startX - cx) ** 2);
  const ob = hy + R; // the hook's outer bottom
  const ib = hy + ri; // and its inner bottom
  return [
    `M${right} ${cy}`,
    `L${right} ${hy}`,
    `A${R} ${R} 0 0 1 ${hx} ${ob}`,
    `C${f(hx - 3.6)} ${ob} ${f(hx - 6.6)} ${f(ob - 0.6)} ${f(hx - 8.4)} ${f(ob - 2)}`,
    // a blunt, rounded end rather than a comma's point
    `Q${f(hx - 9.8)} ${f(ob - 3.2)} ${f(hx - 8.7)} ${f(ob - 4.6)}`,
    `C${f(hx - 6.6)} ${f(ib + 1.6)} ${f(hx - 3.4)} ${ib} ${hx} ${ib}`,
    `A${ri} ${ri} 0 0 0 ${inner} ${hy}`,
    `L${inner} ${f(crotchY + 2.4)}`,
    `Q${inner} ${f(crotchY)} ${startX} ${f(startY)}`,
    `A${r} ${r} 0 1 1 ${right} ${cy}Z`,
  ].join('');
}

/** A crescent: the circle (x, y, r) less the circle (x2, y2, r2). */
function crescent(x, y, r, x2, y2, r2) {
  const dx = x2 - x;
  const dy = y2 - y;
  const d = Math.hypot(dx, dy);
  const a = (r * r - r2 * r2 + d * d) / (2 * d);
  const h = Math.sqrt(r * r - a * a);
  const mx = x + (a * dx) / d;
  const my = y + (a * dy) / d;
  const p1 = [f(mx + (h * dy) / d), f(my - (h * dx) / d)];
  const p2 = [f(mx - (h * dy) / d), f(my + (h * dx) / d)];
  return `M${p1[0]} ${p1[1]}A${r} ${r} 0 1 0 ${p2[0]} ${p2[1]}A${r2} ${r2} 0 0 1 ${p1[0]} ${p1[1]}Z`;
}

/** A four-point sparkle centred on (x, y), `s` from the centre to each point. */
const sparkle = (x, y, s) =>
  `M${x} ${y - s}Q${x} ${y} ${x + s} ${y}Q${x} ${y} ${x} ${y + s}` +
  `Q${x} ${y} ${x - s} ${y}Q${x} ${y} ${x} ${y - s}Z`;

const KEY = nine();
const MOON = crescent(28.7, 19.4, 4.6, 30.9, 17.9, 3.95);
const STARS = sparkle(38.6, 30.4, 2.3) + sparkle(36.9, 36.2, 1.5);

function mark({ detail, xray = false }) {
  const full = detail === 'full';
  const small = detail === 'small';
  const parts = [`<circle cx="32" cy="32" r="${small ? 32 : 31.5}" fill="${C.brass}"/>`];
  if (!small) {
    parts.push(
      `<circle cx="32" cy="32" r="27.4" fill="none" stroke="${C.rim}" stroke-width="${full ? 1.3 : 2}"/>`,
    );
  }
  if (full) {
    parts.push(
      `<circle cx="32" cy="4.4" r="1.5" fill="${C.screw}"/>`,
      `<circle cx="32" cy="59.6" r="1.5" fill="${C.screw}"/>`,
    );
  }
  // the 9's mass sits a little left of its box, so it moves right onto the disc's centre;
  // the smallest mark has no rim, so its 9 grows into the room
  const place = small
    ? 'translate(32 32) scale(1.14) translate(-31.4 -32)'
    : 'translate(0.6 0)';
  const inner = [];
  if (xray) {
    const grid = [];
    for (let v = 12; v <= 56; v += 4) grid.push(`M${v} 8V58M16 ${v}H48`);
    inner.push(
      `<clipPath id="cn-key"><path d="${KEY}"/></clipPath>`,
      `<path d="${KEY}" fill="${C.film}"/>`,
      `<path clip-path="url(#cn-key)" d="${grid.join('')}" stroke="${C.sure}" stroke-width="0.5" opacity="0.45"/>`,
      `<path d="${KEY}" fill="none" stroke="${C.sure}" stroke-width="1.4" stroke-linejoin="round"/>`,
    );
  } else {
    inner.push(`<path d="${KEY}" fill="${C.night}"/>`);
  }
  if (!small) inner.push(`<path d="${MOON}" fill="${xray ? C.xrayMoon : C.moon}"/>`);
  if (full) inner.push(`<path d="${STARS}" fill="${xray ? C.sure : C.moon}"/>`);
  parts.push(`<g transform="${place}">${inner.join('')}</g>`);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">${parts.join('')}</svg>\n`;
}

const files = {
  [path.join(OUT, 'mark.svg')]: mark({ detail: 'full' }),
  [path.join(OUT, 'mark-md.svg')]: mark({ detail: 'md' }),
  [path.join(OUT, 'mark-sm.svg')]: mark({ detail: 'small' }),
  [path.join(OUT, 'mark-xray.svg')]: mark({ detail: 'full', xray: true }),
  [path.join(OUT, 'mark-xray-md.svg')]: mark({ detail: 'md', xray: true }),
  [path.join(root, 'src/app/icon.svg')]: mark({ detail: 'small' }),
};
for (const [file, svg] of Object.entries(files)) {
  writeFileSync(file, svg);
  console.log(path.relative(root, file));
}

/**
 * Draws the Carriage Nine mark: a brass escutcheon whose keyhole is a 9, cut through to the
 * night, with the moon where the 9's counter would be. The 9 is a heavy geometric one, the
 * family of the site's own headings, so it holds its shape at favicon size. Everything is lit
 * from the upper left, like the cast. One shape, drawn at three levels of detail:
 *
 * - `mark.svg` (48px and up): the bevel and face, two screws, the cut with its bevelled edge
 *   and the brass's shadow falling into it, and the moon
 * - `mark-md.svg` (24–40px, the nav): the bevel and face, a clean cut and the moon
 * - `mark-sm.svg` (16–20px, also `src/app/icon.svg`, the favicon): the lit disc, a larger 9
 *
 * and the lamp state of the first two (`mark-lamp*.svg`), which the nav shows while the brand
 * is pointed at: a light comes on in the carriage, and the keyhole glows amber from the moon.
 *
 * The output is committed; rerun this after changing the shape.
 * Run from frontend/: `node scripts/brand-mark.mjs`
 */
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(root, 'src/assets/brand');

// Polished brass (a lit highlight down to its shadow side) against a true night blue, not
// near-black, so the pair has snap; the lamp's amber for the pointed-at state.
const C = {
  brassHi: '#f6dc9a',
  brass: '#d4a24a',
  brassLo: '#8a5f1f',
  bevelHi: '#fbe6b0',
  bevelLo: '#5e3f12',
  edge: '#3d2708', // the shadow line where the bevel meets the face
  lipHi: '#fff0c4', // the cut's lower-right edge, catching the light
  lipLo: '#7a5217', // and its upper-left edge, in shade
  night: '#1d3163',
  nightDeep: '#0a1330',
  moon: '#f7f0da',
  moonShade: '#d8c99e',
  lampHi: '#ffe9ad',
  lamp: '#eaa73a',
  lampLo: '#8a4712',
  lampDark: '#3a1b06',
  lampMoon: '#fffdf5',
  lampMoonShade: '#f3e2b4',
  halo: '#fff4d0',
};
const f = (n) => +n.toFixed(2);

/**
 * The keyhole 9, in a 64-unit box: a round bowl of radius `R` whose underside flattens into a
 * thick tail, the right side running on down and sweeping in to a broad foot. The whole 9,
 * counter included, is the cut; the moon (radius `COUNTER`) floats where the counter would be,
 * so the 9 still reads by its bright middle.
 */
function nine({
  cx = 32,
  cy = 25.5,
  R = 14,
  crotch = [31.2, 37.2],
  underDeg = 128,
  rightDeg = 6,
  bottom = [36, 52.4],
  tip = [20.4, 47.2],
} = {}) {
  const pt = (deg) => [
    f(cx + R * Math.cos((deg * Math.PI) / 180)),
    f(cy + R * Math.sin((deg * Math.PI) / 180)),
  ];
  const [u0, u1] = pt(underDeg);
  const [r0, r1] = pt(rightDeg);
  return [
    `M${crotch[0]} ${crotch[1]}`,
    // the bowl's underside, flattened where the tail takes it over
    `Q${f(crotch[0] - 3.4)} ${f(crotch[1] + 0.9)} ${u0} ${u1}`,
    `A${R} ${R} 0 1 1 ${r0} ${r1}`,
    // the right side runs on down and sweeps in to the foot
    `C${f(r0 + 0.3)} ${f(r1 + 11.5)} ${f(r0 - 1.6)} ${f(bottom[1] - 3.2)} ${bottom[0]} ${bottom[1]}`,
    // the foot: a short, slightly bowed cut to the tip
    `Q${f((bottom[0] + tip[0]) / 2 - 0.3)} ${f(bottom[1] - 0.7)} ${tip[0]} ${tip[1]}`,
    // the tail's inner edge, nearly straight, back up to the bowl
    `C${f(tip[0] + 4.4)} ${f(tip[1] - 2.4)} ${f(crotch[0] - 1.2)} ${f(crotch[1] + 4.4)} ${crotch[0]} ${crotch[1]}Z`,
  ].join('');
}

const COUNTER = 4.8;
const KEY = nine();
const MOON = `<circle cx="32" cy="25.5" r="${COUNTER}" fill="url(#cn-moon)"/>`;

function mark({ detail, lamp = false }) {
  const full = detail === 'full';
  const small = detail === 'small';
  const defs = [
    // the face and the bevel, lit from the upper left
    `<linearGradient id="cn-face" x1="0.15" y1="0.1" x2="0.85" y2="0.95"><stop offset="0" stop-color="${C.brassHi}"/><stop offset="0.5" stop-color="${C.brass}"/><stop offset="1" stop-color="${C.brassLo}"/></linearGradient>`,
    `<linearGradient id="cn-bevel" x1="0.2" y1="0.1" x2="0.8" y2="0.9"><stop offset="0" stop-color="${C.bevelHi}"/><stop offset="0.45" stop-color="${C.brass}"/><stop offset="1" stop-color="${C.bevelLo}"/></linearGradient>`,
    // the seam where the bevel meets the face: shaded along the upper left, lit along the lower right
    `<linearGradient id="cn-seam" x1="0.15" y1="0.1" x2="0.85" y2="0.9"><stop offset="0" stop-color="${C.edge}" stop-opacity="0.9"/><stop offset="0.55" stop-color="${C.edge}" stop-opacity="0.15"/><stop offset="1" stop-color="${C.lipHi}" stop-opacity="0.7"/></linearGradient>`,
    // through the cut: the night, deeper at the upper left where the brass shades it; or, with
    // the lamp on, amber light spreading out from the moon
    lamp
      ? `<radialGradient id="cn-night" cx="0.5" cy="0.32" r="0.85"><stop offset="0" stop-color="${C.lampHi}"/><stop offset="0.32" stop-color="${C.lamp}"/><stop offset="0.7" stop-color="${C.lampLo}"/><stop offset="1" stop-color="${C.lampDark}"/></radialGradient>`
      : `<linearGradient id="cn-night" x1="0.1" y1="0" x2="0.9" y2="1"><stop offset="0" stop-color="${C.nightDeep}"/><stop offset="1" stop-color="${C.night}"/></linearGradient>`,
    `<radialGradient id="cn-moon" cx="0.38" cy="0.35" r="0.75"><stop offset="0" stop-color="${lamp ? C.lampMoon : C.moon}"/><stop offset="1" stop-color="${lamp ? C.lampMoonShade : C.moonShade}"/></radialGradient>`,
    `<clipPath id="cn-key"><path d="${KEY}"/></clipPath>`,
  ];
  const parts = [];
  if (small) {
    parts.push(`<circle cx="32" cy="32" r="32" fill="url(#cn-face)"/>`);
  } else {
    // a raised bevel, and the face inside it with a seam where the two meet
    parts.push(
      `<circle cx="32" cy="32" r="31.5" fill="url(#cn-bevel)"/>`,
      `<circle cx="32" cy="32" r="28" fill="url(#cn-face)"/>`,
      `<circle cx="32" cy="32" r="28" fill="none" stroke="url(#cn-seam)" stroke-width="${full ? 0.9 : 1.2}"/>`,
    );
  }
  if (full) {
    parts.push(
      `<circle cx="32" cy="2.3" r="1.2" fill="${C.bevelLo}"/><circle cx="31.8" cy="2.1" r="0.9" fill="${C.bevelHi}"/>`,
      `<circle cx="32" cy="61.7" r="1.2" fill="${C.bevelLo}"/><circle cx="31.8" cy="61.5" r="0.9" fill="${C.brassHi}"/>`,
    );
  }
  // the tail reaches further left than the bowl's right side, so the 9 moves a little right
  // onto the disc's centre; the smallest mark has no bevel, so its 9 grows into the room
  const place = small
    ? 'translate(32 32) scale(1.18) translate(-32.6 -32)'
    : 'translate(0.6 0)';
  const inner = [];
  if (full) {
    // the cut's bevelled edge, in shade along the upper left and lit along the lower right
    // (large only: smaller, the two slivers read as a smudge, not depth)
    inner.push(
      `<path d="${KEY}" transform="translate(-0.55 -0.55)" fill="${C.lipLo}"/>`,
      `<path d="${KEY}" transform="translate(0.55 0.55)" fill="${C.lipHi}"/>`,
    );
  }
  inner.push(`<path d="${KEY}" fill="url(#cn-night)"/>`);
  if (full && !lamp) {
    // the brass's shadow falling into the cut from its upper-left edge
    inner.push(
      `<path clip-path="url(#cn-key)" d="${KEY}" transform="translate(1.3 1.3)" fill="none" stroke="${C.nightDeep}" stroke-width="2.2" opacity="0.6"/>`,
    );
  }
  if (lamp)
    inner.push(
      `<circle cx="32" cy="25.5" r="${COUNTER + 2.5}" fill="${C.halo}" opacity="0.35"/>`,
    );
  inner.push(MOON);
  parts.push(`<g transform="${place}">${inner.join('')}</g>`);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs>${defs.join('')}</defs>${parts.join('')}</svg>\n`;
}

const files = {
  [path.join(OUT, 'mark.svg')]: mark({ detail: 'full' }),
  [path.join(OUT, 'mark-md.svg')]: mark({ detail: 'md' }),
  [path.join(OUT, 'mark-sm.svg')]: mark({ detail: 'small' }),
  [path.join(OUT, 'mark-lamp.svg')]: mark({ detail: 'full', lamp: true }),
  [path.join(OUT, 'mark-lamp-md.svg')]: mark({ detail: 'md', lamp: true }),
  [path.join(root, 'src/app/icon.svg')]: mark({ detail: 'small' }),
};
for (const [file, svg] of Object.entries(files)) {
  writeFileSync(file, svg);
  console.log(path.relative(root, file));
}

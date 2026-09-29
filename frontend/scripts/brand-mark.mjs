/**
 * Draws The Ninth Express's mark: the train's one headlamp at night, an iron housing and a
 * brass bezel round a lit lens, with a keyhole 9 cut dark into the glass and the moon as its
 * light (the owner's bench, `claude_artifacts/design/logo/ninth-express-marks.html`). One
 * lamp, drawn at three levels of detail, because a mark that reads at 64px turns to mud at
 * 16px:
 *
 * - `mark.svg` (48px and up): the halo round the lamp, the housing, bezel, lens and its glint,
 *   the 9 with the moon's glow, and snow crossing the beam
 * - `mark-md.svg` (24–40px, the nav): the housing, bezel and lens filling the box, a larger 9
 * - `mark-sm.svg` (16–20px, also `src/app/icon.svg`, the favicon): the bezel and lens only,
 *   and the 9 as large as the lens allows
 *
 * and the lamp turned up for the first two (`mark-lamp*.svg`), which the nav shows while the
 * brand is pointed at: the lens burns whiter and the moon's glow spreads.
 *
 * The output is committed; rerun this after changing the lamp.
 * Run from frontend/: `node scripts/brand-mark.mjs`
 */
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(root, 'src/assets/brand');

// the bench's own colours: cast iron, lit brass, the lens's warm light, the night's navy
const C = {
  rimHi: '#e9cd84',
  rim: '#a8843f',
  rimLo: '#4e3612',
  seat: '#3f2b0d', // the dark seat the lens sits in, inside the bezel
  ironHi: '#5a5044',
  iron: '#2a2419',
  ironLo: '#0f0c07',
  navy: '#1d2a55',
  navyDeep: '#0a1024',
  moon: '#fff8e4',
  moonShade: '#e6d9b4',
  glow: '#fff3c4',
  halo: '#f4d68a',
  snow: '#f4ecd4',
};

/** The 9 in a 100-unit box: a round bowl and a thick, round-ended tail swept down and left. */
const BOWL = { cx: 50, cy: 41, r: 19.5 };
const TAIL = 'M 69 41 C 69 60, 62 71, 42 78.5';
const TAIL_W = 12.5;

/** The lens: warm light falling off to the bezel; turned up, it burns whiter further out. */
function lensStops(on) {
  return on
    ? '<stop offset="0" stop-color="#ffffff"/><stop offset=".45" stop-color="#fff1c2"/><stop offset=".8" stop-color="#f6c865"/><stop offset="1" stop-color="#c78a2e"/>'
    : '<stop offset="0" stop-color="#fff6d8"/><stop offset=".55" stop-color="#f1cf7c"/><stop offset="1" stop-color="#9c6a22"/>';
}

function mark({ detail, on = false }) {
  const full = detail === 'full';
  const small = detail === 'small';
  const defs = [
    `<linearGradient id="rim" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${C.rimHi}"/><stop offset=".45" stop-color="${C.rim}"/><stop offset="1" stop-color="${C.rimLo}"/></linearGradient>`,
    // the housing's iron; with the lamp turned up, warmed by its own light
    `<linearGradient id="iron" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${on ? '#9a7a45' : C.ironHi}"/><stop offset=".5" stop-color="${on ? '#5a4220' : C.iron}"/><stop offset="1" stop-color="${on ? '#2a1c0a' : C.ironLo}"/></linearGradient>`,
    `<radialGradient id="lens" cx=".5" cy=".5" r=".5">${lensStops(on)}</radialGradient>`,
    `<radialGradient id="navy" cx=".6" cy=".7" r=".75"><stop offset="0" stop-color="${C.navy}"/><stop offset="1" stop-color="${C.navyDeep}"/></radialGradient>`,
    `<radialGradient id="moon" cx=".45" cy=".4" r=".7"><stop offset="0" stop-color="${C.moon}"/><stop offset="1" stop-color="${C.moonShade}"/></radialGradient>`,
    `<radialGradient id="halo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="${C.halo}" stop-opacity="${on ? 0.75 : 0.55}"/><stop offset=".6" stop-color="${C.halo}" stop-opacity="${on ? 0.2 : 0.12}"/><stop offset="1" stop-color="${C.halo}" stop-opacity="0"/></radialGradient>`,
    `<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2"/></filter>`,
  ];
  // the lamp's rings, outermost first: the large mark leaves room round it for the halo; the
  // nav's fills its box; the favicon's drops the iron housing so the lens can be larger
  const ring = full
    ? { iron: 42, bezel: 37.5, seat: 34, lens: 32.5, nine: 0.72 }
    : small
      ? { iron: 0, bezel: 49.5, seat: 45, lens: 43.5, nine: 0.98 }
      : { iron: 49, bezel: 44, seat: 40.2, lens: 38.6, nine: 0.86 };
  const parts = [];
  if (full) parts.push(`<circle cx="50" cy="50" r="50" fill="url(#halo)"/>`);
  if (ring.iron) parts.push(`<circle cx="50" cy="50" r="${ring.iron}" fill="url(#iron)"/>`);
  parts.push(
    `<circle cx="50" cy="50" r="${ring.bezel}" fill="url(#rim)"/>`,
    `<circle cx="50" cy="50" r="${ring.seat}" fill="${C.seat}"/>`,
    `<circle cx="50" cy="50" r="${ring.lens}" fill="url(#lens)"/>`,
  );
  if (!small) {
    // the glint on the glass, upper left
    const g = ring.lens * 0.92;
    const at = (deg) => [
      (50 + g * Math.cos((deg * Math.PI) / 180)).toFixed(2),
      (50 + g * Math.sin((deg * Math.PI) / 180)).toFixed(2),
    ];
    const [x0, y0] = at(207);
    const [x1, y1] = at(243);
    parts.push(
      `<path d="M ${x0} ${y0} A ${g.toFixed(2)} ${g.toFixed(2)} 0 0 1 ${x1} ${y1}" fill="none" stroke="${C.moon}" stroke-width="${full ? 1.8 : 2.4}" stroke-linecap="round" opacity=".7"/>`,
    );
  }
  // the keyhole in the glass: the dark 9, and the moon where its bowl is, glowing
  const nine = [
    `<circle cx="${BOWL.cx}" cy="${BOWL.cy}" r="${BOWL.r}" fill="url(#navy)"/>`,
    `<path d="${TAIL}" fill="none" stroke="url(#navy)" stroke-width="${TAIL_W}" stroke-linecap="round"/>`,
  ];
  if (!small) {
    nine.push(
      `<circle cx="${BOWL.cx}" cy="${BOWL.cy}" r="${on ? 17 : 13}" fill="${C.glow}" opacity="${on ? 0.95 : 0.6}" filter="url(#glow)"/>`,
    );
  }
  nine.push(`<circle cx="${BOWL.cx}" cy="${BOWL.cy}" r="9.5" fill="url(#moon)"/>`);
  parts.push(
    `<g transform="translate(50 50) scale(${ring.nine}) translate(-50 -50)">${nine.join('')}</g>`,
  );
  if (full) {
    // a little snow crossing the beam
    for (const [x, y, r] of [
      [12, 20, 0.9],
      [88, 30, 0.7],
      [20, 84, 0.8],
      [80, 80, 1],
      [8, 55, 0.6],
      [92, 62, 0.9],
      [50, 6, 0.7],
    ]) {
      parts.push(`<circle cx="${x}" cy="${y}" r="${r}" fill="${C.snow}" opacity=".7"/>`);
    }
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs>${defs.join('')}</defs>${parts.join('')}</svg>\n`;
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

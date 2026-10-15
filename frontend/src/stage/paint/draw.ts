/**
 * The small drawing helpers every paint generator and vector prop is built from: an inked
 * path, a stitched seam, a string, a flame, a cut-out's soft shadow, a spotlight's beam.
 *
 * Copied from the design kit (kits/stage-kit.js) with types added. They return SVG markup
 * as strings, because the backdrop is drawn once per phase and never changes while shown:
 * building it as one string and handing it to the browser is cheaper and simpler than a
 * tree of components with nothing to update.
 */
import { BOARD, BOARD2, CAR, K2 } from './materials';

export { BOARD, BOARD2, K2 };
export const brass = CAR.brass;

/** A repeatable pseudo-random number in [0, 1): the same (i, k) always gives the same value. */
export const rnd = (i: number, k: number): number => {
  const v = Math.sin(i * 127.1 + k * 311.7) * 43758.5453;
  return v - Math.floor(v);
};

const hex = (h: string): number[] => {
  h = h.replace('#', '');
  if (h.length === 3)
    h = h
      .split('')
      .map((c) => c + c)
      .join('');
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
};
const toHex = (r: number[]): string =>
  '#' +
  r
    .map((v) =>
      Math.round(Math.max(0, Math.min(255, v)))
        .toString(16)
        .padStart(2, '0'),
    )
    .join('');

/** Blend two hex colours; t = 0 gives a, t = 1 gives b. */
export const mix = (a: string, b: string, t: number): string =>
  toHex(hex(a).map((v, i) => v + (hex(b)[i] - v) * t));

/** A filled path with the ink outline every prop wears. */
export const inkP = (d: string, f: string, w: number, x = ''): string =>
  `<path d="${d}" fill="${f}" stroke="${K2}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round" ${x}/>`;

/** A dashed line that reads as stitching on felt. */
export const stitch = (d: string, col: string, w: number, o = 0.7): string =>
  `<path d="${d}" fill="none" stroke="${col}" stroke-width="${w}" stroke-dasharray="${w * 2.4} ${w * 2.4}" stroke-linecap="round" opacity="${o}"/>`;

/** A candle-style flame centred at (x, y), k its scale. Flickers via the `sk-flk` class. */
export const flameAt = (x: number, y: number, k: number): string =>
  `<g class="sk-flk">${inkP(`M${x},${y - 10 * k} C${x + 6 * k},${y - 3 * k} ${x + 5 * k},${y + 6 * k} ${x},${y + 8 * k} C${x - 5 * k},${y + 6 * k} ${x - 6 * k},${y - 3 * k} ${x},${y - 10 * k}Z`, '#f0a33a', 1.3 * k)}<path d="M${x},${y - 4 * k} C${x + 3 * k},${y} ${x + 2.4 * k},${y + 5 * k} ${x},${y + 6 * k} C${x - 2.4 * k},${y + 5 * k} ${x - 3 * k},${y} ${x},${y - 4 * k}Z" fill="#fff0b8"/></g>`;

/* a pale string with a dark edge, readable on a light wall and a dark one */
export const twine = (x1: number, y1: number, x2: number, y2: number, s: number): string =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#24180c" stroke-opacity=".8" stroke-width="${3 * s}"/><line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#d9c9a0" stroke-width="${1.4 * s}"/>`;

/* quiet cut-outs: a soft shadow on the wall, no ply edge. P is the id prefix whose shadf filter the scene defines */
export const cutout = (P: string, s: number, m: string, depth = 1): string => {
  const e = (3 + depth * 2) * s;
  return `<g filter="url(#${P}shadf)" opacity=".75" transform="translate(${(e * 1.6).toFixed(1)},${(e * 1.4).toFixed(1)})">${m}</g>${m}`;
};

/* a special's visible beam: a narrow cone from above, drawn faint (the light overlay leaves its footprint open) */
export const beam = (x: number, y0: number, y1: number, rx: number, dark = 50): string =>
  `<path d="M${(x - rx * 0.35).toFixed(0)},${y0} H${(x + rx * 0.35).toFixed(0)} L${(x + rx).toFixed(0)},${(y1 + rx * 0.4).toFixed(0)} H${(x - rx).toFixed(0)}Z" fill="#fff8e0" opacity="${(0.05 + (0.05 * dark) / 100).toFixed(3)}" style="mix-blend-mode:screen"/>`;

/** A rectangle [x, y, w, h] in units. */
export type Rect = [number, number, number, number];
/** A glow source: centre, radius, and colour (as a scene reports it) or strength (once lit). */
export type Glow = [number, number, number, string | number];
/** A special (a narrow spot from above): x, top, bottom, half-width, strength. */
export type Special = [number, number, number, number, number];

/**
 * A role's sigil: the small mark that stands for a role wherever there is no room for its
 * figure (a card's corner, the X-ray badge, the file's role list, a chip turned over). The
 * owner's felt set (the sigil bench, 2026-09-30; the twelve-role set, 2026-10-07): each ONE
 * silhouette plus a few detail pieces, on a 48 grid drawn in a `-2 -2 52 52` box (the felt's
 * edge reaches ~3.2 past the grid). The plain villager's and the plain wolf's sigils are their
 * sides' own marks, the cottage and the wolf's head (`MARKS`, which `FactionMark` backs with a
 * badge or a pennant when a side, not a role, is meant); the other ten are the role's own tool.
 *
 * Two ways to draw one glyph:
 * - `felt` — the silhouette in the side's cloth, the pieces in its second tone and accent, a
 *   dark edge and dashed stitching. Its own colours: for paper and cream, where it sits as an
 *   object (the cards, the wing badge, the file, the ledger's tabs, the notices).
 * - `stamp` (the default) — one colour, `currentColor`: the silhouette fattened, the pieces
 *   knocked out as holes through a mask. For marks printed into a surface in the holder's ink
 *   (faction bands, brass plates, the transcript, the read card's truth, the chips).
 * `small` (under ~26 px) drops the stitching and the `fine` lines, which only blur that small;
 * a numeric `width` under 26 implies it. Flat felt: the bench's felt-texture filter stays off
 * the stage (no live filters there).
 */
import { Fragment, useId, type ReactNode, type SVGProps } from 'react';
import { MATERIALS as M } from '../paint/materials';
import { factionOf, type Faction } from '../roles';

export type Tone = 'felt' | 'tone2' | 'ink' | 'accent' | 'hi';

export interface Part {
  r: Tone;
  d: string;
  /** This accent's own colour in place of the side's (the candle's flame, the pyramid's eye). */
  acc?: string;
  /** A fat felt piece: also stroked 4 wide in its own colour. */
  ex?: boolean;
  /** Stitched along its own edge too. */
  st?: boolean;
  /** Outlined along its edge in the ink (a petal laid on a petal, the hat's brim). */
  edge?: boolean;
  /** A stroked line this wide, not a fill. */
  w?: number;
  /** A stroked line drawn over a wider ink line, so it reads on the felt (the puppet's strings). */
  ol?: boolean;
  /** Dropped when small. */
  fine?: boolean;
  /** In the stamp: unset → a hole (a `tone2` or `felt` piece: left out); false → left out; 'keep' → solid. */
  ko?: boolean | 'keep';
}

export interface Glyph {
  /** The silhouette: the felt's cloth and the stamp's shape. */
  base: string;
  parts: Part[];
  /** The stitching's path: unset → along `base`; '' → none. */
  stitch?: string;
  /** Whole-glyph rotation about the centre, in degrees. */
  rot?: number;
}

/** A side's felt: its cloth, second tone, the ink of its edges, an accent and a highlight. */
export type Palette = Record<Tone, string>;

const f2 = (n: number) => +n.toFixed(2);
const circ = (cx: number, cy: number, r: number) =>
  `M${cx - r} ${cy}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
const ell = (cx: number, cy: number, rx: number, ry: number) =>
  `M${cx - rx} ${cy}a${rx} ${ry} 0 1 0 ${2 * rx} 0a${rx} ${ry} 0 1 0 ${-2 * rx} 0Z`;
const rect = (x: number, y: number, w: number, h: number) => `M${x} ${y}h${w}v${h}h${-w}Z`;
const dia = (cx: number, cy: number, r: number) =>
  `M${cx} ${cy - r}L${cx + r} ${cy}L${cx} ${cy + r}L${cx - r} ${cy}Z`;
/** A straight bar from one point to another, `w` wide. */
const bar = (x1: number, y1: number, x2: number, y2: number, w: number) => {
  const dx = x2 - x1,
    dy = y2 - y1,
    L = Math.hypot(dx, dy),
    px = (-dy / L) * (w / 2),
    py = (dx / L) * (w / 2);
  return `M${f2(x1 + px)} ${f2(y1 + py)}L${f2(x2 + px)} ${f2(y2 + py)}L${f2(x2 - px)} ${f2(y2 - py)}L${f2(x1 - px)} ${f2(y1 - py)}Z`;
};
const star4 = (cx: number, cy: number, R: number, r: number) => {
  let s = '';
  for (let i = 0; i < 8; i++) {
    const a = -Math.PI / 2 + (i * Math.PI) / 4,
      q = i % 2 ? r : R;
    s += (i ? 'L' : 'M') + f2(cx + q * Math.cos(a)) + ' ' + f2(cy + q * Math.sin(a));
  }
  return s + 'Z';
};
/** The sole of a wingtip shoe, toe up, centred on (cx, cy). */
const sole = (cx: number, cy: number) =>
  `M${cx} ${cy - 12}Q${cx + 6} ${cy - 11.5} ${cx + 5.4} ${cy - 2.6}Q${cx + 3.4} ${cy + 1.8} ${cx + 3.7} ${cy + 6.4}Q${cx + 3.9} ${cy + 12} ${cx} ${cy + 12}Q${cx - 3.9} ${cy + 12} ${cx - 3.7} ${cy + 6.4}Q${cx - 3.4} ${cy + 1.8} ${cx - 5.4} ${cy - 2.6}Q${cx - 6} ${cy - 11.5} ${cx} ${cy - 12}Z`;
const heel = (cx: number, cy: number) =>
  `M${cx - 3.75} ${cy + 5}H${cx + 3.75}Q${cx + 3.9} ${cy + 12} ${cx} ${cy + 12}Q${cx - 3.9} ${cy + 12} ${cx - 3.75} ${cy + 5}Z`;
const brogue = (cx: number, cy: number) =>
  (
    [
      [-3, -6],
      [-1.5, -8.3],
      [0, -8.8],
      [1.5, -8.3],
      [3, -6],
    ] as const
  )
    .map(([x, y]) => circ(cx + x, cy + y, 0.6))
    .join('');

const RAVEN =
  'M5 16L12 13Q15 8 21 9Q25 10 26.5 15Q33 19 37 26L45 36.5L40.5 39.5L35 35.5Q28 38 21 35.5Q14 31.5 13 23L11.5 19Z';
const CAP_LEFT = 'M24 30Q20 10 11 8Q5 7.5 3 14Q8 13.5 11.5 18Q13 26 10 33H24Z';
const CAP_RIGHT = 'M24 30Q28 10 37 8Q43 7.5 45 14Q40 13.5 36.5 18Q35 26 38 33H24Z';

/**
 * The four sides' marks (the faction bench, 2026-10-07): the town's cottage, the wolves' head,
 * the neutral-evil perched raven, the neutral-benign two-point jester cap. Bare, the first two
 * are also the plain villager's and the plain wolf's sigils.
 */
export const MARKS: Record<Faction, Glyph> = {
  villagers: {
    base: 'M10 24L24 11L30 16.57V12H34V20.29L38 24H35V39H13V24Z',
    parts: [
      { r: 'tone2', d: 'M10 24L24 11L38 24Z' + rect(30, 12, 4, 8.3), ex: true, st: true },
      { r: 'ink', d: 'M21 39V31.5H27V39Z' },
      { r: 'accent', d: rect(15.5, 27, 4.5, 4.5) },
    ],
  },
  wolves: {
    base: 'M24 12L30 13L37 5L38.5 19L42 27L36 29L31 37L24 42L17 37L12 29L6 27L9.5 19L11 5L18 13Z',
    parts: [
      {
        r: 'tone2',
        d: 'M19.5 27.5H28.5L31 36.5L24 41.5L17 36.5Z M12.2 8.5L17.3 13.8L13.6 16.5Z M35.8 8.5L30.7 13.8L34.4 16.5Z',
      },
      { r: 'accent', d: 'M15.5 22L21 23.5L19 25.5Z M32.5 22L27 23.5L29 25.5Z' },
      { r: 'ink', d: 'M21.5 33.5H26.5L24 36.5Z' },
    ],
  },
  serial_killer: {
    base: RAVEN + rect(22, 35, 2, 6) + rect(27.5, 35, 2, 6) + 'M12 41.5H40V44.5H12Z',
    stitch: RAVEN,
    parts: [
      { r: 'tone2', d: 'M22 18Q33 20 39.5 33.5Q30 33 22 27.5Q19 23 22 18Z', st: true },
      { r: 'tone2', d: 'M12 41.5H40V44.5H12Z', ex: true },
      { r: 'accent', d: circ(17.2, 13.3, 1.5) },
      { r: 'ink', d: 'M5 16L12 13L11.5 19Z', ko: false },
    ],
  },
  neutral_benign: {
    base:
      CAP_LEFT +
      ' ' +
      CAP_RIGHT +
      rect(8, 32, 32, 7.5) +
      circ(3.6, 17, 2.8) +
      circ(44.4, 17, 2.8),
    stitch: rect(8, 32, 32, 7.5),
    parts: [
      { r: 'felt', d: CAP_LEFT, st: true },
      { r: 'tone2', d: CAP_RIGHT, ex: true, st: true },
      { r: 'accent', d: circ(3.6, 17, 2.8) + circ(44.4, 17, 2.8), ex: true, ko: false },
      { r: 'ink', d: dia(24, 35.75, 2.2), fine: true },
    ],
  },
};

// the bench's paths, unchanged (role-sigils-set, 2026-10-07: the four originals' drawings are
// the 2026-09-30 ones; the eight new roles are the bench's chosen variants)
const GLYPHS: Record<string, Glyph> = {
  villager: MARKS.villagers,
  healer: {
    base: 'M19 8H29V19H40V29H29V40H19V29H8V19H19Z',
    parts: [{ r: 'accent', d: 'M21.6 21.6L26.4 26.4M26.4 21.6L21.6 26.4', w: 2 }],
  },
  investigator: {
    base:
      circ(19, 19, 12) +
      'M28.62 24.38L42.12 37.88L37.88 42.12L24.38 28.62Z M30.55 25.45L33.05 27.95L27.95 33.05L25.45 30.55Z',
    stitch: circ(19, 19, 11.9) + 'M29.3 25.1L41.4 37.2M25.1 29.3L37.2 41.4',
    parts: [
      { r: 'tone2', d: circ(19, 19, 8), ko: true },
      { r: 'hi', d: 'M13.6 17Q14 13.6 17.4 13', w: 1.6, fine: true },
      { r: 'accent', d: 'M30.55 25.45L33.05 27.95L27.95 33.05L25.45 30.55Z', ex: true },
    ],
  },
  vigilante: {
    rot: 30,
    base:
      'M17 22V18Q17 6 24 4Q31 6 31 18V22Z' + rect(17, 22, 14, 18) + rect(15.5, 40, 17, 3.5),
    parts: [
      { r: 'tone2', d: 'M17 22V18Q17 6 24 4Q31 6 31 18V22Z', ex: true },
      { r: 'accent', d: rect(15.5, 25, 17, 2.6) },
      { r: 'ink', d: 'M17 37.6H31', w: 1.2, fine: true },
    ],
  },
  // a candle in a chamberstick: the saucer, its finger loop, the stick and the flame
  sentinel: {
    base:
      'M6 35Q24 40 42 35Q41 40 36 41.5Q24 44 12 41.5Q7 40 6 35Z' +
      rect(17, 31, 14, 5) +
      rect(19, 13, 10, 20) +
      circ(40.5, 30, 5.2) +
      'M24 2.8Q28.5 8 27.2 10.5Q24 13.5 20.8 10.5Q19.5 8 24 2.8Z',
    stitch: 'M6 35Q24 40 42 35Q41 40 36 41.5Q24 44 12 41.5Q7 40 6 35Z',
    parts: [
      { r: 'hi', d: rect(19, 13, 10, 20), ex: true, ko: false, st: true },
      { r: 'ink', d: circ(40.5, 30, 2.2) },
      {
        r: 'accent',
        acc: '#ffb547',
        d: 'M24 2.8Q28.5 8 27.2 10.5Q24 13.5 20.8 10.5Q19.5 8 24 2.8Z',
        ex: true,
        ko: false,
      },
      { r: 'ink', d: 'M24 11.5V13.6', w: 1, fine: true },
    ],
  },
  // two wingtip soles (shoes, not paws, so they never echo the wolf's head)
  trailseer: {
    rot: -8,
    base: sole(31, 15.5) + sole(17, 32),
    parts: [
      { r: 'tone2', d: heel(31, 15.5) + heel(17, 32), ex: true },
      { r: 'ink', d: 'M27.3 20H34.7M13.3 36.5H20.7', w: 1.2 },
      { r: 'ink', d: brogue(31, 15.5) + brogue(17, 32), fine: true },
    ],
  },
  // a two-tone pyramid with an eye, no ring (so it never reads as a round faction badge)
  sigilist: {
    base: 'M23.8 5.8L41.6 30.4L23.8 37.2L6.4 30.4Z',
    parts: [
      { r: 'tone2', d: 'M23.8 5.8V37.2L6.4 30.4Z', ex: true },
      { r: 'ink', d: 'M23.8 6.6V36.4', w: 1, fine: true },
      { r: 'accent', acc: '#efe2cf', d: circ(23.8, 22, 5) },
      { r: 'ink', d: circ(23.8, 22, 2.8), ko: 'keep' },
    ],
  },
  // a rose bud: dark cup and spiral heart, matched side petals, one front petal, two skirt petals
  chanteuse: {
    base: 'M14 15Q14.5 4.5 24 4Q33.5 4.5 34 15Q29 19.5 24 19.5Q19 19.5 14 15Z M15 8.5Q9.5 8 9.5 13Q10 18 12 21Q12.5 27 15 31Q16.5 23 17.5 16Q18 11 15 8.5Z M33 8.5Q38.5 8 38.5 13Q38 18 36 21Q35.5 27 33 31Q31.5 23 30.5 16Q30 11 33 8.5Z M19.5 13Q20.5 8.6 24.5 8.6Q28.8 8.8 28.8 12.6Q28 16.6 24 16.8Q20 16.6 19.5 13Z M14.5 17Q24 22.5 33.5 17Q34 27 29.5 32.5Q24 36.5 18.5 32.5Q14 27 14.5 17Z M17 30Q10.5 27.5 5 30Q9 37.5 16 39.5Q21 40.5 24 38Q19 35 17 30Z M31 30Q37.5 27.5 43 30Q39 37.5 32 39.5Q27 40.5 24 38Q29 35 31 30Z M22.7 38H25.3V45H22.7Z',
    stitch: '',
    parts: [
      {
        r: 'tone2',
        d: 'M14 15Q14.5 4.5 24 4Q33.5 4.5 34 15Q29 19.5 24 19.5Q19 19.5 14 15Z',
        edge: true,
      },
      {
        r: 'felt',
        d: 'M15 8.5Q9.5 8 9.5 13Q10 18 12 21Q12.5 27 15 31Q16.5 23 17.5 16Q18 11 15 8.5Z',
        edge: true,
      },
      {
        r: 'felt',
        d: 'M33 8.5Q38.5 8 38.5 13Q38 18 36 21Q35.5 27 33 31Q31.5 23 30.5 16Q30 11 33 8.5Z',
        edge: true,
      },
      {
        r: 'felt',
        d: 'M19.5 13Q20.5 8.6 24.5 8.6Q28.8 8.8 28.8 12.6Q28 16.6 24 16.8Q20 16.6 19.5 13Z',
        edge: true,
      },
      { r: 'ink', d: 'M21.4 11.6Q24.4 9.8 27.4 11Q25 13 21.4 11.6Z' },
      {
        r: 'tone2',
        d: 'M17 30Q10.5 27.5 5 30Q9 37.5 16 39.5Q21 40.5 24 38Q19 35 17 30Z',
        edge: true,
      },
      {
        r: 'tone2',
        d: 'M31 30Q37.5 27.5 43 30Q39 37.5 32 39.5Q27 40.5 24 38Q29 35 31 30Z',
        edge: true,
      },
      {
        r: 'felt',
        d: 'M14.5 17Q24 22.5 33.5 17Q34 27 29.5 32.5Q24 36.5 18.5 32.5Q14 27 14.5 17Z',
        edge: true,
        st: true,
      },
      {
        r: 'ink',
        d: 'M14.5 17Q24 22.5 33.5 17Q34 27 29.5 32.5Q24 36.5 18.5 32.5Q14 27 14.5 17',
        w: 1.1,
        fine: true,
      },
      {
        r: 'accent',
        acc: '#f7efe9',
        d: circ(10.2, 31.6, 0.9) + circ(35.6, 36.4, 0.8),
        fine: true,
      },
    ],
  },
  // a top hat with a wand leaning across its front; the pale wand tips stand in for the accent
  illusionist: {
    base:
      'M14.5 10Q14.5 7.6 17 7.6H31Q33.5 7.6 33.5 10L32.4 31.5H15.6Z M6.5 33Q6.5 29.8 11.5 30.4Q24 32 36.5 30.4Q41.5 29.8 41.5 33Q41.5 37.4 24 37.8Q6.5 37.4 6.5 33Z' +
      bar(11, 43, 37.5, 12.5, 3.8),
    stitch: 'M14.5 10Q14.5 7.6 17 7.6H31Q33.5 7.6 33.5 10L32.4 31.5H15.6Z',
    parts: [
      { r: 'tone2', d: 'M15.3 25.4H32.7L32.4 30.4H15.6Z' },
      { r: 'hi', d: 'M18 11V23', w: 1, fine: true, ko: false },
      {
        r: 'felt',
        d: 'M6.5 33Q6.5 29.8 11.5 30.4Q24 32 36.5 30.4Q41.5 29.8 41.5 33Q41.5 37.4 24 37.8Q6.5 37.4 6.5 33Z',
        ex: true,
        edge: true,
      },
      { r: 'ink', d: 'M12 31.4Q24 33.2 36 31.4', w: 1, fine: true },
      { r: 'ink', d: bar(11, 43, 37.5, 12.5, 3.8), ex: true, ko: false },
      {
        r: 'hi',
        d: bar(11, 43, 13.6, 40, 3.8) + bar(34.9, 15.5, 37.5, 12.5, 3.8),
        ex: true,
        ko: false,
      },
      { r: 'ink', d: bar(11, 43, 37.5, 12.5, 6.2), w: 1, fine: true },
    ],
  },
  // a marionette's control cross, three strings working a little figure
  necromancer: {
    base:
      bar(7, 9, 41, 9, 4.4) +
      bar(24, 4, 24, 16, 4.4) +
      circ(24, 28.5, 3.8) +
      'M19.5 33.5H28.5L30.5 44H17.5Z' +
      bar(20, 34.5, 14.5, 39.5, 2.8) +
      bar(28, 34.5, 33.5, 39.5, 2.8),
    stitch: 'M8.5 9H39.5',
    parts: [
      {
        r: 'hi',
        d: 'M9.5 10.5L14.5 38M24 17.5V24.5M38.5 10.5L33.5 38',
        w: 1.1,
        ol: true,
        ko: 'keep',
      },
      {
        r: 'tone2',
        d:
          circ(24, 28.5, 3.8) +
          'M19.5 33.5H28.5L30.5 44H17.5Z' +
          bar(20, 34.5, 14.5, 39.5, 2.8) +
          bar(28, 34.5, 33.5, 39.5, 2.8),
        ex: true,
      },
      { r: 'accent', d: dia(24, 38.5, 2) },
    ],
  },
  // two stacks of coins, the taller one's top face in gold
  speculator: {
    base:
      'M20 15V37Q20 41.5 31 41.5Q42 41.5 42 37V15Z' +
      ell(31, 15, 11, 4.2) +
      'M6 27V37Q6 41.5 15 41.5Q24 41.5 24 37V27Z' +
      ell(15, 27, 9, 3.6),
    stitch: '',
    parts: [
      {
        r: 'ink',
        d: 'M20 20.5Q31 25 42 20.5M20 26Q31 30.5 42 26M20 31.5Q31 36 42 31.5',
        w: 1,
      },
      {
        r: 'felt',
        d: 'M6 27V37Q6 41.5 15 41.5Q24 41.5 24 37V27Z' + ell(15, 27, 9, 3.6),
        ex: true,
      },
      { r: 'ink', d: 'M6 32Q15 35.6 24 32', w: 1 },
      { r: 'accent', d: ell(31, 15, 8.6, 3), ko: false },
      { r: 'tone2', d: ell(15, 27, 7, 2.5) },
    ],
  },
  // a crystal ball on a claw stand, a swirl inside and a star on the glass
  fortune_teller: {
    base: circ(24, 19, 14) + 'M15 32Q24 36 33 32L36 40Q36 43 33 43H15Q12 43 12 40Z',
    stitch: circ(24, 19, 14),
    parts: [
      { r: 'tone2', d: 'M15 32Q24 36 33 32L36 40Q36 43 33 43H15Q12 43 12 40Z', ex: true },
      {
        r: 'tone2',
        d: 'M12.5 22Q18 15 24.5 20.5Q30 25.5 35.6 19Q35 27 28.5 29.5Q22 31 18.5 26.5Q16 24 12.5 22Z',
      },
      {
        r: 'ink',
        d: 'M18 37Q17 40.5 15.5 42.5M24 37V42.5M30 37Q31 40.5 32.5 42.5',
        w: 1,
        fine: true,
      },
      { r: 'hi', d: 'M15.5 15Q17 10 21.5 8.5', w: 1.8, fine: true },
      { r: 'accent', d: star4(29.5, 12.5, 3.8, 1.1) },
    ],
  },
  wolf: MARKS.wolves,
  serial_killer: {
    base: 'M31 6Q15 -1 5 22Q15 11 31 15Z M29.2 7H33.2L35 44H31Z' + rect(25.5, 27, 5, 3.4),
    parts: [
      { r: 'tone2', d: 'M31 6Q15 -1 5 22Q15 11 31 15Z', ex: true },
      { r: 'accent', d: rect(28.6, 15.5, 6, 3.2) },
      { r: 'ink', d: 'M9 18.8Q16 10.5 29.5 12.6', w: 1.1, fine: true },
    ],
  },
};

/** The roles the stage can draw, in the bench's order (town, wolves, neutral evil, neutral benign). */
export const SIGIL_ROLES: readonly string[] = Object.keys(GLYPHS);

/** Each side's felt, from the stage's materials (the inks are the sides' existing inks). */
export const FELT: Record<Faction, Palette> = {
  villagers: {
    felt: M.townFelt,
    tone2: M.townFelt2,
    ink: M.townInk,
    accent: M.townAccent,
    hi: M.townHi,
  },
  wolves: {
    felt: M.wolfFelt,
    tone2: M.wolfFelt2,
    ink: M.wolfInk,
    accent: M.wolfAccent,
    hi: M.wolfHi,
  },
  serial_killer: {
    felt: M.skFelt,
    tone2: M.skFelt2,
    ink: M.skInk,
    accent: M.skAccent,
    hi: M.skHi,
  },
  neutral_benign: {
    felt: M.benignFelt,
    tone2: M.benignFelt2,
    ink: M.benignInk,
    accent: M.benignAccent,
    hi: M.benignHi,
  },
};

export const VIEWBOX = '-2 -2 52 52';
export const J = { strokeLinejoin: 'round', strokeLinecap: 'round' } as const;

// every fill and stroke is spelled out: a holder's `stroke`/`fill` (the site sprite's group, the
// old line marks' CSS) must never reach the pieces, nor the mask's black and white
function piece(p: Part, col: string, fat = false, under?: string) {
  if (p.w)
    return (
      <>
        {under ? (
          <path d={p.d} fill="none" stroke={under} strokeWidth={f2(p.w + 1.8)} {...J} />
        ) : null}
        <path d={p.d} fill="none" stroke={col} strokeWidth={p.w} {...J} />
      </>
    );
  return fat ? (
    <path d={p.d} fill={col} stroke={col} strokeWidth={4} {...J} />
  ) : (
    <path d={p.d} fill={col} stroke="none" />
  );
}

const turn = (g: Glyph) => (g.rot ? `rotate(${g.rot} 24 24)` : undefined);

/** The glyph in felt: the cloth, its pieces, the edge and the stitching. */
export function Felt({ g, c, small }: { g: Glyph; c: Palette; small: boolean }) {
  const stitch = g.stitch ?? g.base;
  return (
    <g transform={turn(g)}>
      <path d={g.base} fill={c.ink} stroke={c.ink} strokeWidth={6.4} {...J} />
      <path d={g.base} fill={c.felt} stroke={c.felt} strokeWidth={4} {...J} />
      {g.parts.map((p, i) =>
        small && p.fine ? null : (
          <Fragment key={i}>
            {piece(
              p,
              p.r === 'accent' && p.acc ? p.acc : c[p.r],
              p.ex,
              p.ol ? c.ink : undefined,
            )}
            {p.edge ? (
              <path
                d={p.d}
                fill="none"
                stroke={c.ink}
                strokeWidth={small ? 1.6 : 1.2}
                {...J}
              />
            ) : null}
            {p.st && !small ? (
              <path
                d={p.d}
                fill="none"
                stroke={c.ink}
                strokeWidth={0.9}
                strokeDasharray="1.6 1.5"
                opacity={0.75}
                {...J}
              />
            ) : null}
          </Fragment>
        ),
      )}
      {stitch && !small ? (
        <path
          d={stitch}
          fill="none"
          stroke={c.ink}
          strokeWidth={1}
          strokeDasharray="1.7 1.5"
          opacity={0.9}
          {...J}
        />
      ) : null}
    </g>
  );
}

/**
 * The glyph as mask content: the silhouette solid, the pieces holes. `invert` cuts the glyph
 * out of a solid ground instead (a mark through a badge), the holes then filled.
 */
export function Cut({
  g,
  small,
  invert = false,
}: {
  g: Glyph;
  small: boolean;
  invert?: boolean;
}) {
  const on = invert ? '#000' : '#fff',
    off = invert ? '#fff' : '#000';
  return (
    <g transform={turn(g)}>
      <path d={g.base} fill={on} stroke={on} strokeWidth={6.4} {...J} />
      {g.parts.map((p, i) => {
        const ko = p.ko ?? (p.r !== 'tone2' && p.r !== 'felt');
        if (ko === false || (small && p.fine)) return null;
        if (ko === 'keep')
          return (
            <Fragment key={i}>
              {p.w ? (
                <path d={p.d} fill="none" stroke={on} strokeWidth={f2(p.w + 0.6)} {...J} />
              ) : (
                piece(p, on)
              )}
            </Fragment>
          );
        return <Fragment key={i}>{piece(p, off)}</Fragment>;
      })}
    </g>
  );
}

function Stamp({ g, small, id }: { g: Glyph; small: boolean; id: string }) {
  return (
    <>
      <defs>
        <mask id={id} maskUnits="userSpaceOnUse" x={-2} y={-2} width={52} height={52}>
          <Cut g={g} small={small} />
        </mask>
      </defs>
      <rect
        x={-2}
        y={-2}
        width={52}
        height={52}
        fill="currentColor"
        stroke="none"
        mask={`url(#${id})`}
      />
    </>
  );
}

/** A mask id from `useId`, whose punctuation is no use in url(#…). */
export const maskId = (prefix: string, id: string) =>
  `${prefix}-${id.replace(/[^\w-]/g, '')}`;

/**
 * The stamps for the site's icon sprite (components/site/IconSprite), which draws `PATHS[role]`
 * inside a 40-grid `<symbol>` under a stroked, unfilled group: each is a nested `<svg>` that
 * refits the 52 box to 40 and paints itself, the small form (the sprite's icons are 14–38 px),
 * with a mask id of its own per role.
 */
export const PATHS: Record<string, ReactNode> = Object.fromEntries(
  Object.entries(GLYPHS).map(([role, g]) => [
    role,
    <svg key={role} x={0} y={0} width={40} height={40} viewBox={VIEWBOX}>
      <Stamp g={g} small id={`sg-mask-${role}`} />
    </svg>,
  ]),
);

export function Sigil({
  role,
  variant = 'stamp',
  small,
  ...rest
}: {
  role: string;
  /** `felt` in the side's own colours, or a one-colour `stamp` in `currentColor`. */
  variant?: 'felt' | 'stamp';
  /** Drawn under ~26 px: no stitching, no fine lines. Unset: a numeric `width` under 26. */
  small?: boolean;
} & SVGProps<SVGSVGElement>) {
  // two sigils on one page must not share a mask
  const id = maskId('sigil', useId());
  const g = GLYPHS[role];
  const f = factionOf(role);
  if (!g || !f) return null;
  const sm = small ?? (typeof rest.width === 'number' && rest.width < 26);
  return (
    <svg
      viewBox={VIEWBOX}
      aria-hidden="true"
      data-sigil={role}
      data-variant={variant}
      {...rest}
    >
      {variant === 'felt' ? (
        <Felt g={g} c={FELT[f]} small={sm} />
      ) : (
        <Stamp g={g} small={sm} id={id} />
      )}
    </svg>
  );
}

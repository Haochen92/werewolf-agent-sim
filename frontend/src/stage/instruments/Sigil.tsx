/**
 * A role's sigil: the small mark that stands for a role wherever there is no room for its
 * figure (a card's corner, the X-ray badge, the file's role list, a chip turned over). The
 * owner's felt set (2026-09-30, the sigil bench): a cottage, a cross, a magnifier, a tilted
 * bullet, a wolf's head and a fat-bladed scythe, each ONE silhouette plus a few detail pieces,
 * on a 48 grid drawn in a `-2 -2 52 52` box (the felt's edge reaches ~3.2 past the grid).
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

type Tone = 'tone2' | 'ink' | 'accent' | 'hi';

interface Part {
  r: Tone;
  d: string;
  /** A fat felt piece: also stroked 4 wide in its own colour. */
  ex?: boolean;
  /** Stitched along its own edge too. */
  st?: boolean;
  /** A stroked line this wide, not a fill. */
  w?: number;
  /** Dropped when small. */
  fine?: boolean;
  /** In the stamp: unset → a hole (a `tone2` piece: left out); false → left out; 'keep' → solid. */
  ko?: boolean | 'keep';
}

interface Glyph {
  f: 'town' | 'wolf' | 'killer';
  /** The silhouette: the felt's cloth and the stamp's shape. */
  base: string;
  parts: Part[];
  /** The stitching's path: unset → along `base`; '' → none. */
  stitch?: string;
  /** Whole-glyph rotation about the centre, in degrees. */
  rot?: number;
}

const circ = (cx: number, cy: number, r: number) =>
  `M${cx - r} ${cy}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
const rect = (x: number, y: number, w: number, h: number) => `M${x} ${y}h${w}v${h}h${-w}Z`;

// the bench's paths, unchanged (sigil-set.js, 2026-09-30)
const GLYPHS: Record<string, Glyph> = {
  villager: {
    f: 'town',
    base: 'M10 24L24 11L30 16.57V12H34V20.29L38 24H35V39H13V24Z',
    parts: [
      { r: 'tone2', d: 'M10 24L24 11L38 24Z' + rect(30, 12, 4, 8.3), ex: true, st: true },
      { r: 'ink', d: 'M21 39V31.5H27V39Z' },
      { r: 'accent', d: rect(15.5, 27, 4.5, 4.5) },
    ],
  },
  healer: {
    f: 'town',
    base: 'M19 8H29V19H40V29H29V40H19V29H8V19H19Z',
    parts: [{ r: 'accent', d: 'M21.6 21.6L26.4 26.4M26.4 21.6L21.6 26.4', w: 2 }],
  },
  investigator: {
    f: 'town',
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
    f: 'town',
    rot: 30,
    base:
      'M17 22V18Q17 6 24 4Q31 6 31 18V22Z' + rect(17, 22, 14, 18) + rect(15.5, 40, 17, 3.5),
    parts: [
      { r: 'tone2', d: 'M17 22V18Q17 6 24 4Q31 6 31 18V22Z', ex: true },
      { r: 'accent', d: rect(15.5, 25, 17, 2.6) },
      { r: 'ink', d: 'M17 37.6H31', w: 1.2, fine: true },
    ],
  },
  wolf: {
    f: 'wolf',
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
    f: 'killer',
    base: 'M31 6Q15 -1 5 22Q15 11 31 15Z M29.2 7H33.2L35 44H31Z' + rect(25.5, 27, 5, 3.4),
    parts: [
      { r: 'tone2', d: 'M31 6Q15 -1 5 22Q15 11 31 15Z', ex: true },
      { r: 'accent', d: rect(28.6, 15.5, 6, 3.2) },
      { r: 'ink', d: 'M9 18.8Q16 10.5 29.5 12.6', w: 1.1, fine: true },
    ],
  },
};

// each side's felt, from the stage's materials (the inks are the sides' existing inks)
const FELT: Record<Glyph['f'], { felt: string } & Record<Tone, string>> = {
  town: {
    felt: M.townFelt,
    tone2: M.townFelt2,
    ink: M.townInk,
    accent: M.townAccent,
    hi: M.townHi,
  },
  wolf: {
    felt: M.wolfFelt,
    tone2: M.wolfFelt2,
    ink: M.wolfInk,
    accent: M.wolfAccent,
    hi: M.wolfHi,
  },
  killer: {
    felt: M.skFelt,
    tone2: M.skFelt2,
    ink: M.skInk,
    accent: M.skAccent,
    hi: M.skHi,
  },
};

const VIEWBOX = '-2 -2 52 52';
const J = { strokeLinejoin: 'round', strokeLinecap: 'round' } as const;

// every fill and stroke is spelled out: a holder's `stroke`/`fill` (the site sprite's group, the
// old line marks' CSS) must never reach the pieces, nor the mask's black and white
function piece(p: Part, col: string, fat = false) {
  if (p.w) return <path d={p.d} fill="none" stroke={col} strokeWidth={p.w} {...J} />;
  return fat ? (
    <path d={p.d} fill={col} stroke={col} strokeWidth={4} {...J} />
  ) : (
    <path d={p.d} fill={col} stroke="none" />
  );
}

const turn = (g: Glyph) => (g.rot ? `rotate(${g.rot} 24 24)` : undefined);

function Felt({ g, small }: { g: Glyph; small: boolean }) {
  const c = FELT[g.f];
  const stitch = g.stitch ?? g.base;
  return (
    <g transform={turn(g)}>
      <path d={g.base} fill={c.ink} stroke={c.ink} strokeWidth={6.4} {...J} />
      <path d={g.base} fill={c.felt} stroke={c.felt} strokeWidth={4} {...J} />
      {g.parts.map((p, i) =>
        small && p.fine ? null : (
          <Fragment key={i}>
            {piece(p, c[p.r], p.ex)}
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

function Stamp({ g, small, id }: { g: Glyph; small: boolean; id: string }) {
  return (
    <>
      <defs>
        <mask id={id} maskUnits="userSpaceOnUse" x={-2} y={-2} width={52} height={52}>
          <g transform={turn(g)}>
            <path d={g.base} fill="#fff" stroke="#fff" strokeWidth={6.4} {...J} />
            {g.parts.map((p, i) => {
              const ko = p.ko ?? p.r !== 'tone2';
              if (ko === false || (small && p.fine)) return null;
              return (
                <Fragment key={i}>{piece(p, ko === 'keep' ? '#fff' : '#000')}</Fragment>
              );
            })}
          </g>
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
  // two sigils on one page must not share a mask; useId's punctuation is no use in url(#…)
  const id = `sigil-${useId().replace(/[^\w-]/g, '')}`;
  const g = GLYPHS[role];
  if (!g) return null;
  const sm = small ?? (typeof rest.width === 'number' && rest.width < 26);
  return (
    <svg
      viewBox={VIEWBOX}
      aria-hidden="true"
      data-sigil={role}
      data-variant={variant}
      {...rest}
    >
      {variant === 'felt' ? <Felt g={g} small={sm} /> : <Stamp g={g} small={sm} id={id} />}
    </svg>
  );
}

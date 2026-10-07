/**
 * A side's mark, where a side and not a role is meant: the village, the wolves, the lone
 * killers, the neutrals (the owner's faction set, 2026-10-07). The cottage and the wolf's
 * head were the villager's and the wolf's sigils; bare, they still are (`Sigil`), so what
 * says "this is a side, not a card" is the backing. Three formats:
 * - `badge` — the mark sewn on a round ink patch with a felt rim and stitching: the side as an
 *   object (the verdict board, the slate's watermark, the landing card's seal).
 * - `pennant` — the same on a hanging pennant: the side as a flag on something that belongs to
 *   it (a role card's foot, the ending's result).
 * - `mark` — the bare mark, no backing: inline by a word at text size (the archive's "Won by",
 *   the filter chips), where a backing would be a blot.
 * As with sigils, `felt` paints the side's own colours and `stamp` (one colour, `currentColor`)
 * cuts the mark out of the backing through a mask; `small` (under ~26 px, or a numeric `width`
 * under 26) drops the stitching and fine lines. The neutral-evil mark's second tone is deeper
 * than its sigils' (the raven's wing, `MATERIALS.skShade`). Flat: no texture filter.
 */
import { useId, type SVGProps } from 'react';
import { MATERIALS as M } from '../paint/materials';
import { FACTION_NAME, type Faction } from '../roles';
import { Cut, FELT, Felt, J, MARKS, VIEWBOX, maskId, type Palette } from './Sigil';

export type MarkFormat = 'badge' | 'pennant' | 'mark';

const PALETTE: Record<Faction, Palette> = {
  ...FELT,
  serial_killer: { ...FELT.serial_killer, tone2: M.skShade },
};

/**
 * Each mark's box on the 48 grid (the bench measured its base path once; the stage cannot at
 * render time): centre and the longer side plus the felt's edge, for fitting into a backing.
 */
const BOX: Record<Faction, { cx: number; cy: number; s: number }> = {
  villagers: { cx: 24, cy: 25, s: 34.4 },
  wolves: { cx: 24, cy: 23.5, s: 43.4 },
  serial_killer: { cx: 25, cy: 26.67, s: 46.4 },
  neutral_benign: { cx: 24, cy: 23.73, s: 52.8 },
};

const circ = (cx: number, cy: number, r: number) =>
  `M${cx - r} ${cy}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;

/** The backings: the shape, its inner stitch line, where the mark centres, its scale and the room it has. */
const BACK = {
  badge: { d: circ(24, 24, 21.5), st: circ(24, 24, 18.6), cy: 24, k: 0.64, fit: 29 },
  pennant: {
    d: 'M7.5 3.5H40.5V35.5L24 45L7.5 35.5Z',
    st: 'M10.5 6.5H37.5V33.7L24 41.5L10.5 33.7Z',
    cy: 21,
    k: 0.58,
    fit: 26.5,
  },
} as const;

/** The transform that seats a side's mark in a backing. */
function place(f: Faction, shape: keyof typeof BACK) {
  const b = BOX[f],
    B = BACK[shape],
    k = Math.min(B.k, B.fit / b.s);
  return `translate(24 ${B.cy}) scale(${k.toFixed(3)}) translate(${-b.cx} ${-b.cy})`;
}

export function FactionMark({
  faction,
  format = 'badge',
  variant = 'felt',
  small,
  ...rest
}: {
  faction: Faction;
  format?: MarkFormat;
  /** `felt` in the side's own colours, or a one-colour `stamp` in `currentColor`. */
  variant?: 'felt' | 'stamp';
  /** Drawn under ~26 px: no stitching, no fine lines. Unset: a numeric `width` under 26. */
  small?: boolean;
} & SVGProps<SVGSVGElement>) {
  const id = maskId('fm', useId());
  const g = MARKS[faction];
  if (!g) return null;
  const sm = small ?? (typeof rest.width === 'number' && rest.width < 26);
  const c = PALETTE[faction];
  let inner;
  if (format === 'mark') {
    inner =
      variant === 'felt' ? (
        <Felt g={g} c={c} small={sm} />
      ) : (
        <>
          <defs>
            <mask id={id} maskUnits="userSpaceOnUse" x={-2} y={-2} width={52} height={52}>
              <Cut g={g} small={sm} />
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
  } else {
    const B = BACK[format];
    const at = place(faction, format);
    inner =
      variant === 'felt' ? (
        <>
          <path d={B.d} fill={c.ink} stroke={c.felt} strokeWidth={2} {...J} />
          {!sm ? (
            <path
              d={B.st}
              fill="none"
              stroke={c.felt}
              strokeWidth={0.9}
              strokeDasharray="1.7 1.5"
              opacity={0.8}
              {...J}
            />
          ) : null}
          <g transform={at}>
            <Felt g={g} c={c} small={sm} />
          </g>
        </>
      ) : (
        <>
          <defs>
            <mask id={id} maskUnits="userSpaceOnUse" x={-2} y={-2} width={52} height={52}>
              <path d={B.d} fill="#fff" stroke="#fff" strokeWidth={2} {...J} />
              <path d={B.st} fill="none" stroke="#000" strokeWidth={0.9} {...J} />
              {/* the mark cut through the backing is always the small form: its holes are tiny */}
              <g transform={at}>
                <Cut g={g} small invert />
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
  return (
    <svg
      viewBox={VIEWBOX}
      role="img"
      aria-label={FACTION_NAME[faction]}
      data-faction={faction}
      data-format={format}
      data-variant={variant}
      {...rest}
    >
      {inner}
    </svg>
  );
}

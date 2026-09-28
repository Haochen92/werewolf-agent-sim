'use client';

/**
 * The ballot chip: a felt token, drawn inside the vote's SVG. Its back is plain, a stitched
 * ring and the house star, so a chip in the jar says nothing about who dropped it; its face is
 * the voter's head in a paper ring with the seat's numeral (the same face as a hung chip), or,
 * for the abstain saucer's place card, an empty dashed ring.
 *
 * `FlatChip` is a chip lying on a surface, seen from the house: a squashed disc with its edge
 * showing, back up (anonymous, in the jar) or face up (counted, on a plate). Numbers from the
 * vote bench (rev 64 `chipBack`, `chipFace`, `chipFlat`).
 */
import { useId } from 'react';
import { SPRITES, type Character } from '@/assets/manifest';
import { headRect } from '../cast/ChipSprite';
import { stitch } from '../paint/draw';
import { K2 } from '../paint/materials';

export const CHIP = {
  back: '#3a4660',
  edge: '#252d42',
  ring: '#d9c9a0',
  face: '#efe4cb',
  faceEdge: '#cbb992',
  you: '#e0a63a',
} as const;

const star = (x: number, y: number, k: number) =>
  `M${x},${y - k} L${x + k * 0.28},${y - k * 0.28} L${x + k},${y} L${x + k * 0.28},${y + k * 0.28} L${x},${y + k} L${x - k * 0.28},${y + k * 0.28} L${x - k},${y} L${x - k * 0.28},${y - k * 0.28}Z`;

/** A chip seen face-on, back showing: the stitched ring and the star. */
export function ChipBack({ x, y, r }: { x: number; y: number; r: number }) {
  const a = r * 0.72;
  return (
    <g>
      <circle cx={x} cy={y} r={r} fill={CHIP.back} stroke={K2} strokeWidth={1.8} />
      <g
        dangerouslySetInnerHTML={{
          __html: stitch(
            `M${x - a},${y} a${a},${a} 0 1 0 ${2 * a},0 a${a},${a} 0 1 0 ${-2 * a},0`,
            CHIP.ring,
            1.1,
            0.9,
          ),
        }}
      />
      <path d={star(x, y, r * 0.34)} fill={CHIP.ring} />
    </g>
  );
}

export interface ChipFaceProps {
  x: number;
  y: number;
  r: number;
  /** The seat's numeral and its character; null draws the abstain ring. */
  seat: number | null;
  character?: Character;
  /** The viewer's own chip: an amber rim. */
  you?: boolean;
  /** Stroke widths are multiplied by this (a flattened chip thickens them back). */
  sw?: number;
}

/** A chip seen face-on, face showing: the head and the seat's numeral, or the empty ring. */
export function ChipFace({ x, y, r, seat, character, you, sw = 1 }: ChipFaceProps) {
  const clip = 'vc' + useId().replace(/[^A-Za-z0-9_-]/g, '');
  const rim = (
    <circle
      cx={x}
      cy={y}
      r={r}
      fill={CHIP.face}
      stroke={you ? CHIP.you : K2}
      strokeWidth={(you ? 3 : 1.8) * sw}
    />
  );
  if (seat === null || !character) {
    return (
      <g>
        {rim}
        <circle
          cx={x}
          cy={y}
          r={r * 0.62}
          fill="none"
          stroke="#8d7a55"
          strokeWidth={2 * sw}
          strokeDasharray={`${3 * sw} ${2.4 * sw}`}
        />
      </g>
    );
  }
  const bx = x + r * 0.7,
    by = y + r * 0.68,
    br = Math.max(4, r * 0.36);
  return (
    <g>
      {rim}
      <clipPath id={clip}>
        <circle cx={x} cy={y} r={r * 0.84} />
      </clipPath>
      <g clipPath={`url(#${clip})`}>
        <rect x={x - r} y={y - r} width={2 * r} height={2 * r} fill="#e4d5b3" />
        <image
          href={SPRITES.day[character].head.src}
          {...headRect(character, x, y, r * 1.68)}
        />
      </g>
      <circle cx={bx} cy={by} r={br} fill={K2} stroke={CHIP.face} strokeWidth={1.2 * sw} />
      <text
        x={bx}
        y={by + br * 0.36}
        textAnchor="middle"
        fontFamily="var(--font-stage-sans, Outfit), system-ui, sans-serif"
        fontWeight={700}
        fontSize={br * 1.15}
        fill={CHIP.face}
      >
        {seat}
      </text>
    </g>
  );
}

export interface FlatChipProps {
  x: number;
  y: number;
  r: number;
  /** Face up with this face; omit for back up (anonymous). */
  face?: Omit<ChipFaceProps, 'x' | 'y' | 'r' | 'sw'> | null;
  /** Its thickness, as a fraction of the radius: the step a tower of them climbs by. */
  t?: number;
}

/** A chip lying on its back (anonymous) or face up, the edge showing below the top. */
export function FlatChip({ x, y, r, face, t = 0.2 }: FlatChipProps) {
  const ec = face ? CHIP.faceEdge : CHIP.edge;
  const ry = r * 0.42;
  return (
    <g>
      <ellipse
        cx={x}
        cy={y + r * t}
        rx={r}
        ry={ry}
        fill={ec}
        stroke={K2}
        strokeWidth={1.3}
      />
      <rect x={x - r} y={y} width={2 * r} height={r * t} fill={ec} />
      <path
        d={`M${x - r},${y} v${r * t} M${x + r},${y} v${r * t}`}
        stroke={K2}
        strokeWidth={1.3}
      />
      {t > 0.3 ? (
        <g
          dangerouslySetInnerHTML={{
            __html: stitch(
              `M${x - r * 0.8},${y + r * t * 0.5 + r * 0.3} Q${x},${y + r * t * 0.5 + r * 0.5} ${x + r * 0.8},${y + r * t * 0.5 + r * 0.3}`,
              face ? '#8d7a55' : CHIP.ring,
              1,
              0.8,
            ),
          }}
        />
      ) : null}
      {face ? (
        <g transform={`translate(0,${(y * (1 - 0.42)).toFixed(2)}) scale(1,0.42)`}>
          <ChipFace x={x} y={y} r={r} sw={1 / 0.7} {...face} />
        </g>
      ) : (
        <>
          <ellipse
            cx={x}
            cy={y}
            rx={r}
            ry={ry}
            fill={CHIP.back}
            stroke={K2}
            strokeWidth={1.3}
          />
          <ellipse
            cx={x}
            cy={y}
            rx={r * 0.68}
            ry={r * 0.28}
            fill="none"
            stroke={CHIP.ring}
            strokeWidth={1}
            strokeDasharray="2 2"
          />
        </>
      )}
    </g>
  );
}

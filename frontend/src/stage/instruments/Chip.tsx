'use client';

/**
 * A seat's chip hung on its string: the token the table is shown as whenever the puppets are
 * not at the stand (the deal, the night lobby, the morning). The face is the character's head
 * in a paper ring with the seat's numeral on a dark badge, drawn over the sprite in vector.
 *
 * - `whole`: hanging on its string.
 * - `saved`: the healer's ribbon tied on the string above it.
 * - `fallen`: the string gives way and the chip drops out of the frame. Only a beat played
 *   forward draws it; at rest a fallen chip is simply not there, and the scene leaves it out.
 *
 * The chip can also show a sigil in place of the head (the investigator's reading), turning
 * over to it when played. An edge says something about the seat without moving it: red for a
 * packmate, amber for the one being looked at ("nothing moves to say chosen").
 *
 * Numbers from benches 67 and 75 (`hungChip`, `chipFace`).
 */
import { useId } from 'react';
import { SPRITES, type Character } from '@/assets/manifest';
import { MATERIALS } from '../paint/materials';
import { factionOf, type Faction } from '../roles';
import { Flip } from './Flip';
import { Sigil } from './Sigil';
import { StringDrop, type Hang } from './StringDrop';
import { tieY } from './flies';

export type ChipState = 'whole' | 'fallen' | 'saved';

export interface ChipProps {
  /** The chip's centre and radius, in units. */
  x: number;
  y: number;
  r: number;
  seat: number;
  character: Character;
  state?: ChipState;
  /** This viewer's own seat: an amber rim. */
  you?: boolean;
  /** A ring round the chip: a packmate (red), or the one in the light (amber). */
  edge?: 'pack' | 'lit' | null;
  /** Show this role's sigil in place of the head. */
  sigil?: string | null;
  /** Turn over to the sigil (played). */
  turn?: boolean;
  /** What plays on the string: lowered, raised, or (for `fallen`) the drop. */
  move?: Exclude<Hang, 'fall'> | null;
  delay?: number;
  /** When a fallen chip drops (seconds). */
  fallDelay?: number;
  turnDelay?: number;
}

const FACE = '#efe4cb',
  INK = MATERIALS.ink;

const FACTION_INK: Record<Faction, string> = {
  villagers: MATERIALS.town,
  wolves: MATERIALS.wolf,
  serial_killer: MATERIALS.sk,
};

/** The chip's face, drawn in its own box: centre (r, 4 + r), the string tied on at (r, 0). */
function Face({
  r,
  seat,
  character,
  you,
}: {
  r: number;
  seat: number;
  character: Character;
  you?: boolean;
}) {
  const clip = 'cf' + useId().replace(/[^A-Za-z0-9_-]/g, '');
  const cx = r,
    cy = 4 + r;
  const bx = cx + r * 0.7,
    by = cy + r * 0.68,
    br = Math.max(4, r * 0.36);
  const head = r * 1.72;
  return (
    <svg style={svgBox(r)} aria-hidden="true">
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill={FACE}
        stroke={you ? MATERIALS.amber : INK}
        strokeWidth={you ? 3 : 1.8}
      />
      <clipPath id={clip}>
        <circle cx={cx} cy={cy} r={r * 0.84} />
      </clipPath>
      <g clipPath={`url(#${clip})`}>
        <rect x={cx - r} y={cy - r} width={2 * r} height={2 * r} fill="#e4d5b3" />
        <image
          href={SPRITES.day[character].chip.src}
          x={cx - head / 2}
          y={cy - head / 2}
          width={head}
          height={head}
          preserveAspectRatio="xMidYMid slice"
        />
      </g>
      <circle cx={bx} cy={by} r={br} fill={INK} stroke={FACE} strokeWidth={1.2} />
      <text
        x={bx}
        y={by + br * 0.36}
        textAnchor="middle"
        fontFamily="var(--font-stage-sans, Outfit), system-ui, sans-serif"
        fontWeight={700}
        fontSize={br * 1.15}
        fill={FACE}
      >
        {seat}
      </text>
    </svg>
  );
}

/** The chip turned to a role's sigil, in the faction's ink on paper. */
function SigilFace({ r, role }: { r: number; role: string }) {
  const f = factionOf(role);
  return (
    <div style={svgBox(r)}>
      <svg
        style={{ position: 'absolute', inset: 0, overflow: 'visible' }}
        aria-hidden="true"
      >
        <circle cx={r} cy={4 + r} r={r} fill={FACE} stroke={INK} strokeWidth={1.8} />
      </svg>
      <Sigil
        role={role}
        strokeWidth={1}
        style={{
          position: 'absolute',
          left: r * 0.28,
          top: 4 + r * 0.28,
          width: r * 1.44,
          height: r * 1.44,
          color: f ? FACTION_INK[f] : INK,
        }}
      />
    </div>
  );
}

const svgBox = (r: number) =>
  ({
    position: 'absolute',
    left: 0,
    top: 0,
    width: 2 * r,
    height: 2 * r + 4,
    overflow: 'visible',
  }) as const;

/** The healer's bow on the string, with its little cross, just above the chip. */
function Ribbon({ r }: { r: number }) {
  const x = r,
    ry = -r * 0.45;
  return (
    <svg style={svgBox(r)} aria-hidden="true">
      <path
        d={`M${x},${ry} c-8,-9 -14,2 -2,5 c-12,3 -6,14 2,-5 c8,-9 14,2 2,5 c12,3 6,14 -2,-5Z`}
        fill={MATERIALS.amber}
        stroke={INK}
        strokeWidth={1.4}
      />
      <path
        d={`M${x - 3},${ry + 3} l-4,12 M${x + 3},${ry + 3} l4,12`}
        stroke={MATERIALS.amber}
        strokeWidth={3}
        strokeLinecap="round"
      />
      <path
        d={`M${x - 2.4},${ry} h4.8 M${x},${ry - 2.4} v4.8`}
        stroke={MATERIALS.wolf}
        strokeWidth={1.8}
      />
    </svg>
  );
}

export function Chip({
  x,
  y,
  r,
  seat,
  character,
  state = 'whole',
  you,
  edge,
  sigil,
  turn = false,
  move,
  delay,
  fallDelay = 0,
  turnDelay = 0,
}: ChipProps) {
  const face = <Face r={r} seat={seat} character={character} you={you} />;
  const shown = sigil ? (
    <Flip
      back={face}
      face={<SigilFace r={r} role={sigil} />}
      turn={turn}
      delay={turnDelay}
    />
  ) : (
    face
  );
  const ring = edge ? (
    <svg style={svgBox(r)} aria-hidden="true">
      <circle
        cx={r}
        cy={4 + r}
        r={r + 5}
        fill="none"
        stroke={edge === 'pack' ? MATERIALS.wolf : MATERIALS.amber}
        strokeWidth={edge === 'pack' ? 3.5 : 2.5}
      />
    </svg>
  ) : null;
  const top = tieY(y, r);
  return (
    <StringDrop
      x={x}
      y={top}
      w={2 * r}
      h={2 * r + 4}
      loop
      move={state === 'fallen' ? 'fall' : move}
      delay={state === 'fallen' ? fallDelay : delay}
    >
      {shown}
      {ring}
      {state === 'saved' ? <Ribbon r={r} /> : null}
    </StringDrop>
  );
}

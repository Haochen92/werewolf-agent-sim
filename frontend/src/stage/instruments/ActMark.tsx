'use client';

/**
 * The marks a night's acts leave, drawn large beneath a chip at the morning: a bite (the
 * wolves), a knife (the serial killer), a bullet (the vigilante), the plaster (the healer's
 * save) and the lens (the investigator's reading, on that seat's screen only). Flat, inked,
 * in the sigils' line: symbols of an act, not objects. The wire names the attacker's type,
 * never the attacker, so a mark says what was done and never by whom.
 *
 * `k` is the mark's half-size in units. Played, a mark pops in (bench rev 67 `markIn`).
 * Ported from bench 67's `actIcon`, drawn here at k = 50 and scaled.
 */
import { motion } from 'motion/react';
import type { AttackerType } from '@/types/contracts';
import { useMotionScale } from '../motion';

export type ActKind = 'bite' | 'knife' | 'bullet' | 'plaster' | 'lens';

/** The mark an attacker type leaves (`night_result.attacker_types`). */
export const ATTACK_MARK: Record<AttackerType, ActKind> = {
  wolves: 'bite',
  serial_killer: 'knife',
  vigilante: 'bullet',
};

const INK = '#24180c',
  K = 50,
  W = K * 0.16;

function Plaster() {
  const strip = (a: number) => (
    <rect
      transform={`rotate(${a})`}
      x={-K}
      y={-K * 0.28}
      width={2 * K}
      height={K * 0.56}
      rx={K * 0.28}
      fill={a < 0 ? '#8fd1d6' : '#e8c39a'}
      stroke={INK}
      strokeWidth={W}
    />
  );
  const holes = [
    [-0.18, -0.14],
    [0, -0.14],
    [0.18, -0.14],
    [-0.18, 0.14],
    [0, 0.14],
    [0.18, 0.14],
  ];
  return (
    <>
      {strip(45)}
      {strip(-45)}
      <rect
        x={-K * 0.34}
        y={-K * 0.34}
        width={K * 0.68}
        height={K * 0.68}
        rx={K * 0.1}
        fill="#e8c39a"
        stroke={INK}
        strokeWidth={W}
      />
      {holes.map(([dx, dy]) => (
        <circle key={`${dx},${dy}`} cx={dx * K} cy={dy * K} r={K * 0.045} fill={INK} />
      ))}
    </>
  );
}

function Bite() {
  const tooth = {
    fill: '#f6f1e4',
    stroke: INK,
    strokeWidth: W * 0.8,
    strokeLinejoin: 'round',
  } as const;
  const jaw = {
    fill: 'none',
    stroke: INK,
    strokeWidth: W * 1.4,
    strokeLinecap: 'round',
  } as const;
  return (
    <>
      <path d={`M${-K * 0.9},${-K * 0.2} q${K * 0.9},${-K * 0.9} ${K * 1.8},0`} {...jaw} />
      <path
        d={`M${-K * 0.6},${-K * 0.42} l${K * 0.2},${K * 0.7} l${K * 0.2},${-K * 0.55}Z M${K * 0.2},${-K * 0.55} l${K * 0.2},${K * 0.7} l${K * 0.2},${-K * 0.55}Z`}
        {...tooth}
      />
      <path d={`M${-K * 0.9},${K * 0.35} q${K * 0.9},${K * 0.9} ${K * 1.8},0`} {...jaw} />
      <path
        d={`M${-K * 0.5},${K * 0.62} l${K * 0.16},${-K * 0.5} l${K * 0.16},${K * 0.4}Z M${K * 0.2},${K * 0.66} l${K * 0.16},${-K * 0.5} l${K * 0.16},${K * 0.4}Z`}
        {...tooth}
      />
    </>
  );
}

function Bullet() {
  return (
    <g transform="rotate(-30)">
      <rect
        x={-K * 0.9}
        y={-K * 0.3}
        width={K * 1.2}
        height={K * 0.6}
        rx={K * 0.08}
        fill="#c9a25e"
        stroke={INK}
        strokeWidth={W}
      />
      <path
        d={`M${K * 0.3},${-K * 0.3} h${K * 0.25} q${K * 0.45},0 ${K * 0.55},${K * 0.3} q${-K * 0.1},${K * 0.3} ${-K * 0.55},${K * 0.3} h${-K * 0.25}Z`}
        fill="#e3503f"
        stroke={INK}
        strokeWidth={W}
      />
      <path d={`M${-K * 0.9},${-K * 0.3} v${K * 0.6}`} stroke={INK} strokeWidth={W * 1.6} />
      <path
        d={`M${-K * 0.6},${-K * 0.12} h${K * 0.7}`}
        stroke="#fff"
        strokeOpacity={0.5}
        strokeWidth={W * 0.7}
      />
    </g>
  );
}

function Knife() {
  return (
    <g transform="rotate(-40)">
      <path
        d={`M${-K * 0.95},0 h${K * 1.1} q${K * 0.6},0 ${K * 0.8},${-K * 0.32} q${-K * 0.4},${-K * 0.05} ${-K * 0.8},${K * 0.02} h${-K * 1.1}Z`}
        fill="#cfd3d6"
        stroke={INK}
        strokeWidth={W}
      />
      <rect
        x={-K * 0.95}
        y={-K * 0.22}
        width={K * 0.65}
        height={K * 0.44}
        rx={K * 0.1}
        fill="#5a3418"
        stroke={INK}
        strokeWidth={W}
      />
      <circle cx={-K * 0.65} cy={0} r={K * 0.06} fill="#c9a25e" />
    </g>
  );
}

function Lens() {
  const c = -K * 0.15,
    r = K * 0.55,
    handle = `M${K * 0.25},${K * 0.25} l${K * 0.55},${K * 0.55}`;
  return (
    <>
      <circle
        cx={c}
        cy={c}
        r={r}
        fill="#d6ecec"
        fillOpacity={0.35}
        stroke="#c9a25e"
        strokeWidth={W * 1.6}
      />
      <circle cx={c} cy={c} r={r + W} fill="none" stroke={INK} strokeWidth={W * 0.6} />
      <path d={handle} stroke={INK} strokeWidth={W * 2.6} strokeLinecap="round" />
      <path d={handle} stroke="#5a3418" strokeWidth={W * 1.8} strokeLinecap="round" />
    </>
  );
}

const DRAW: Record<ActKind, () => React.ReactNode> = {
  plaster: Plaster,
  bite: Bite,
  bullet: Bullet,
  knife: Knife,
  lens: Lens,
};

export interface ActMarkProps {
  kind: ActKind;
  /** Centre and half-size, in units. */
  x: number;
  y: number;
  k: number;
  /** Pop in (played), after this many seconds; false = at rest. */
  arrive?: number | false;
}

export function ActMark({ kind, x, y, k, arrive = false }: ActMarkProps) {
  const m = useMotionScale();
  const Draw = DRAW[kind];
  const half = k * 1.3;
  return (
    <motion.svg
      viewBox={`${-K * 1.3} ${-K * 1.3} ${K * 2.6} ${K * 2.6}`}
      style={{
        position: 'absolute',
        left: x - half,
        top: y - half,
        width: 2 * half,
        height: 2 * half,
        overflow: 'visible',
      }}
      aria-label={kind}
      role="img"
      initial={arrive === false ? false : { scale: 0.2, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{
        duration: 0.5 * m,
        delay: (arrive || 0) * m,
        ease: [0.3, 1.5, 0.5, 1],
      }}
    >
      <Draw />
    </motion.svg>
  );
}

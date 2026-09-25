'use client';

/**
 * The wall clock in the dining car, hung on its string at the left: brass, a paper face,
 * two hands. It carries the time the scene needs said. At night it starts at midnight and
 * its hands move on toward dawn as acts come in; on a seat's turn it can carry a red ring
 * for the seconds left.
 *
 * The dining car's paint draws a clock that only keeps the phase's hour; a scene that needs
 * the hands to move turns that one off (`wallClock: false`) and hangs this in its place, at
 * the paint's own position (`diningCarPlan().clock`). The drawing is the kit's
 * (`wallClock`, `clockAt`); the moving hands and the ring are bench 67's `clockFace`.
 *
 * The room's night tint falls on the brass and the string, as it does on the paint's clock;
 * the face stays pale, lit by its special, so the hands read.
 */
import { motion } from 'motion/react';
import { useMotionScale } from '../motion';
import { CAR, K2, ROOMLIGHT, type Phase } from '../paint/materials';
import { STAGE_H, STAGE_W } from '../units';

export interface WallClockProps {
  /** Centre and radius, from the dining car's plan. */
  x: number;
  y: number;
  r: number;
  /** The time shown, in hours past midnight (0 = midnight, 6 = dawn); fractions move the minute hand. */
  time: number;
  /** Played: the hands sweep on from this time. */
  from?: number | null;
  /** The red ring: the fraction of the turn left, or null for none. */
  ring?: number | null;
  /** The hour's paint, for the room's tint on the brass. */
  phase: Phase;
}

const angle = (t: number) => ({
  hour: ((t % 12) / 12) * 360,
  minute: (t % 1) * 360,
});

function Hand({
  x,
  y,
  len,
  width,
  deg,
  fromDeg,
  k,
}: {
  x: number;
  y: number;
  len: number;
  width: number;
  deg: number;
  fromDeg: number | null;
  k: number;
}) {
  return (
    <motion.g
      initial={fromDeg === null ? false : { rotate: fromDeg }}
      animate={{ rotate: deg }}
      transition={{ duration: 1.2 * k, ease: [0.4, 0.2, 0.3, 1] }}
    >
      {/* an invisible ring the hand's length: it centres the box the hand turns about on the pivot */}
      <circle cx={x} cy={y} r={len} fill="none" />
      <path
        d={`M${x},${y} v${-len}`}
        stroke={K2}
        strokeWidth={width}
        strokeLinecap="round"
      />
    </motion.g>
  );
}

export function WallClock({
  x,
  y,
  r,
  time,
  from = null,
  ring = null,
  phase,
}: WallClockProps) {
  const k = useMotionScale();
  const H = STAGE_H,
    R = r * 0.8;
  // played, the hands turn forward by the time that passed, never back the short way
  const was = from === null ? null : angle(from);
  const to = was
    ? {
        hour: was.hour + (time - (from ?? time)) * 30,
        minute: was.minute + (time - (from ?? time)) * 360,
      }
    : angle(time);
  const tint = ROOMLIGHT[phase];
  const dots = Array.from({ length: 12 }, (_, i) => {
    const a = (i / 12) * Math.PI * 2;
    return (
      <circle
        key={i}
        cx={x + Math.cos(a) * r * 0.66}
        cy={y + Math.sin(a) * r * 0.66}
        r={i % 3 ? 1.4 : 2.4}
        fill={K2}
      />
    );
  });
  const ringPath = (() => {
    if (ring == null) return null;
    const f = Math.max(0, Math.min(1, ring)),
      a = -Math.PI / 2 + 2 * Math.PI * f,
      rr = R * 0.9;
    if (f >= 1)
      return <circle cx={x} cy={y} r={rr} fill="none" stroke="#e3503f" strokeWidth={3.5} />;
    return (
      <path
        d={`M${x},${y - rr} A${rr},${rr} 0 ${f > 0.5 ? 1 : 0} 1 ${x + Math.cos(a) * rr},${y + Math.sin(a) * rr}`}
        fill="none"
        stroke="#e3503f"
        strokeWidth={3.5}
        strokeOpacity={0.9}
      />
    );
  })();
  return (
    <svg
      viewBox={`0 0 ${STAGE_W} ${STAGE_H}`}
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        overflow: 'visible',
      }}
      aria-hidden="true"
    >
      <g className="sk-hang" style={{ filter: 'drop-shadow(8px 7px 5px rgba(0,0,0,.37))' }}>
        <line
          x1={x}
          y1={0}
          x2={x}
          y2={y - r - 0.03 * H}
          stroke={K2}
          strokeOpacity={0.8}
          strokeWidth={3}
        />
        <line
          x1={x}
          y1={0}
          x2={x}
          y2={y - r - 0.03 * H}
          stroke="#d9c9a0"
          strokeWidth={1.4}
        />
        <circle
          cx={x}
          cy={y - r - 0.018 * H}
          r={8}
          fill="none"
          stroke={CAR.brass}
          strokeWidth={3}
        />
        <rect
          x={x - 5}
          y={y - r - 0.01 * H}
          width={10}
          height={0.012 * H}
          fill={CAR.brass}
          stroke={K2}
          strokeWidth={1.2}
        />
        <circle cx={x} cy={y} r={r} fill={CAR.brass} stroke={K2} strokeWidth={2.4} />
        {tint.tint ? (
          <circle
            cx={x}
            cy={y}
            r={r + 1.2}
            fill={tint.tint}
            opacity={tint.a}
            style={{ mixBlendMode: 'multiply' }}
          />
        ) : null}
        <circle cx={x} cy={y} r={R} fill="#ecdfc3" stroke={K2} strokeWidth={2} />
        <circle
          cx={x}
          cy={y}
          r={R * 0.8}
          fill="none"
          stroke={K2}
          strokeWidth={1}
          strokeDasharray={`1.2 ${R * 0.8 * 0.5236 - 1.2}`}
        />
        {dots}
        {ringPath}
        <Hand
          x={x}
          y={y}
          len={R * 0.5}
          width={2.2}
          deg={to.hour}
          fromDeg={was ? was.hour : null}
          k={k}
        />
        <Hand
          x={x}
          y={y}
          len={R * 0.72}
          width={2.2}
          deg={to.minute}
          fromDeg={was ? was.minute : null}
          k={k}
        />
        <circle cx={x} cy={y} r={1.8} fill={K2} />
      </g>
    </svg>
  );
}

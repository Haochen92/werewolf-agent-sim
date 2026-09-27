'use client';

/**
 * The wall clock in the dining car, hung on its cord at the left: the owner's painted brass
 * case and face (SPRITES.props.wallClock, no hands), with two hands drawn over it. It carries
 * the time the scene needs said: the hour's own time by default (CarPaint hangs it so), and
 * at night it starts at midnight and its hands move on toward dawn as acts come in; on a
 * seat's turn it can carry a red ring for the seconds left.
 *
 * It hangs where the car's plan says (`diningCarPlan().clock`): the picture is sized so its
 * ring of twelve dots sits where the kit's dots were (0.66 r), so the face is the kit's face
 * (0.8 r) and the hands (bench 67's `clockFace`) turn about its centre.
 *
 * The room's tint falls on the case and the chain, as it did on the kit's clock (the brass);
 * the face stays pale, lit by its special, so the hands read. It sways on its cord with the
 * shadow it throws on the wall (the rooms' atmosphere).
 */
import { motion, type Transition } from 'motion/react';
import { useId } from 'react';
import { SPRITES } from '@/assets/manifest';
import { useMotionScale } from '../motion';
import { K2, ROOMLIGHT, type Phase } from '../paint/materials';
import { STAGE_H, STAGE_W } from '../units';

/**
 * The picture (wall-clock.webp, 422×608) in its own pixels: the face's centre, the radius of its
 * ring of dots and of its cream face, and the top of the chain, where the cord ties on.
 */
const CLOCK_PX = { cx: 210.53, cy: 385.78, dots: 134.34, face: 160, top: 4.5 };

/** Its shadow on the wall, thrown by the key light: how far it falls and how dark. */
const SHADOW = { dx: 18, dy: 15, a: 0.46 };

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
  /** Played: the hour the room was at before; its tint fades off the brass with the car's. */
  tintFrom?: Phase | null;
  fade?: Transition;
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
  tintFrom = null,
  fade,
}: WallClockProps) {
  const k = useMotionScale();
  const id = 'wc' + useId().replace(/[^A-Za-z0-9_-]/g, '');
  const R = r * 0.8;
  // played, the hands turn forward by the time that passed, never back the short way
  const was = from === null ? null : angle(from);
  const to = was
    ? {
        hour: was.hour + (time - (from ?? time)) * 30,
        minute: was.minute + (time - (from ?? time)) * 360,
      }
    : angle(time);
  // the picture, sized so its dots lie at 0.66 r: kp units a pixel
  const img = SPRITES.props.wallClock,
    kp = (0.66 * r) / CLOCK_PX.dots,
    ix = x - CLOCK_PX.cx * kp,
    iy = y - CLOCK_PX.cy * kp,
    iw = img.width * kp,
    ih = img.height * kp;
  // the baked shadow: the silhouette 128 px tall with a 12 px margin (manifest.ts)
  const sh = SPRITES.shadow.wall.clock,
    su = ih / 128;
  const tintRect = (p: Phase) =>
    ROOMLIGHT[p].tint ? (
      <rect
        x={ix}
        y={iy}
        width={iw}
        height={ih}
        fill={ROOMLIGHT[p].tint ?? undefined}
        opacity={ROOMLIGHT[p].a}
        mask={`url(#${id}m)`}
        clipPath={`url(#${id}c)`}
      />
    ) : null;
  const old = tintFrom && tintFrom !== phase ? tintRect(tintFrom) : null;
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
      <defs>
        {/* the picture's own shape, and everything but its face: where the room's tint falls */}
        <mask
          id={`${id}m`}
          maskUnits="userSpaceOnUse"
          x={ix}
          y={iy}
          width={iw}
          height={ih}
          style={{ maskType: 'alpha' }}
        >
          <image href={img.src} x={ix} y={iy} width={iw} height={ih} />
        </mask>
        <clipPath id={`${id}c`}>
          <path
            clipRule="evenodd"
            d={`M${ix},${iy} h${iw} v${ih} h${-iw}Z M${x - CLOCK_PX.face * kp},${y} a${CLOCK_PX.face * kp},${CLOCK_PX.face * kp} 0 1 0 ${2 * CLOCK_PX.face * kp},0 a${CLOCK_PX.face * kp},${CLOCK_PX.face * kp} 0 1 0 ${-2 * CLOCK_PX.face * kp},0Z`}
          />
        </clipPath>
      </defs>
      <g className="sk-hang">
        <image
          href={sh.src}
          x={ix + (iw - sh.width * su) / 2 + SHADOW.dx}
          y={iy - 12 * su + SHADOW.dy}
          width={sh.width * su}
          height={sh.height * su}
          opacity={SHADOW.a}
        />
        <line
          x1={x}
          y1={0}
          x2={x}
          y2={iy + CLOCK_PX.top * kp}
          stroke={K2}
          strokeOpacity={0.8}
          strokeWidth={3}
        />
        <line
          x1={x}
          y1={0}
          x2={x}
          y2={iy + CLOCK_PX.top * kp}
          stroke="#d9c9a0"
          strokeWidth={1.4}
        />
        <image href={img.src} x={ix} y={iy} width={iw} height={ih} />
        {tintRect(phase)}
        {old ? (
          <motion.g initial={{ opacity: 1 }} animate={{ opacity: 0 }} transition={fade}>
            {old}
          </motion.g>
        ) : null}
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

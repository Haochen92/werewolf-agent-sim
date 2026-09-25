'use client';

/**
 * A thing hung on a string from the flies: the one apparatus the night and the deal use for
 * everything (the chips, the cards, later the verdict board). The string runs from above the
 * frame down to where it ties on; the thing hangs from that point.
 *
 * It moves in three ways, and only when told to (a beat played forward): lowered from out of
 * the frame, raised back out of it, or let fall (the string gives way: the thing drops out of
 * the bottom of the frame turning as it goes, and the cut string is drawn back up). At rest it
 * simply hangs, and a thing that has been raised or has fallen is not drawn at all: that is
 * the caller's business, so seeking to a beat never shows anything half-way.
 *
 * Positions are in units. The timings are the benches' (rev 67, rev 75): down 1 s, up 0.9 s,
 * the fall 0.9 s, on the kit's eases; the speed control scales them all.
 */
import { motion } from 'motion/react';
import type { CSSProperties, ReactNode } from 'react';
import { useMotionScale } from '../motion';
import { STAGE_H } from '../units';

export type Hang = 'lower' | 'raise' | 'fall';

export interface StringDropProps {
  /** The string's line. */
  x: number;
  /** Where the string ties on: the top of the thing. */
  y: number;
  /** The thing's box, hung centred under the tie. */
  w: number;
  h: number;
  /** What plays; omit for at rest. */
  move?: Hang | null;
  /** Seconds before it starts (at normal speed). */
  delay?: number;
  /** Seconds it takes (default: the bench's for that move). */
  duration?: number;
  /** Where the string starts; default above the frame. */
  from?: number;
  /** The brass loop the string ties to. */
  loop?: boolean;
  /** Hide the string (the thing is still hung by it, just not drawn: a card under a chip). */
  bare?: boolean;
  className?: string;
  style?: CSSProperties;
  children?: ReactNode;
}

const EASE = {
  lower: [0.35, 0.75, 0.4, 1],
  raise: [0.5, 0, 0.7, 0.4],
  fall: [0.5, 0, 0.9, 0.6],
} as const;
const DURATION = { lower: 1, raise: 0.9, fall: 0.9 } as const;

/** The pale string with a dark edge, readable on light wall and dark (paint/draw.ts `twine`). */
export function Twine({ x, y0, y1 }: { x: number; y0: number; y1: number }) {
  return (
    <svg
      aria-hidden="true"
      style={{
        position: 'absolute',
        left: x - 3,
        top: y0,
        width: 6,
        height: Math.max(0, y1 - y0),
        overflow: 'visible',
      }}
    >
      <line
        x1={3}
        y1={0}
        x2={3}
        y2="100%"
        stroke="#24180c"
        strokeOpacity={0.8}
        strokeWidth={3}
      />
      <line x1={3} y1={0} x2={3} y2="100%" stroke="#d9c9a0" strokeWidth={1.4} />
    </svg>
  );
}

export function StringDrop({
  x,
  y,
  w,
  h,
  move,
  delay = 0,
  duration,
  from = -40,
  loop = false,
  bare = false,
  className,
  style,
  children,
}: StringDropProps) {
  const k = useMotionScale();
  const t = {
    duration: (duration ?? (move ? DURATION[move] : 0)) * k,
    delay: delay * k,
    ease: move ? EASE[move] : undefined,
  };
  // far enough up that the thing and its tie are out of the frame
  const out = -(y + h + 40);
  const box: CSSProperties = {
    position: 'absolute',
    left: x - w / 2,
    top: y,
    width: w,
    height: h,
  };
  const string = bare ? null : (
    <>
      <Twine x={w / 2} y0={from - y} y1={0} />
      {loop ? (
        <svg
          aria-hidden="true"
          style={{ position: 'absolute', left: w / 2 - 7, top: -7, width: 14, height: 14 }}
        >
          <circle cx={7} cy={7} r={5} fill="none" stroke="#b08a4a" strokeWidth={2} />
        </svg>
      ) : null}
    </>
  );

  if (move === 'fall') {
    // the string gives way: the thing drops and turns, the cut string is drawn back up
    return (
      <div className={className} style={{ ...box, ...style }}>
        <motion.div
          style={{ position: 'absolute', inset: 0 }}
          initial={{ y: 0 }}
          animate={{ y: out }}
          transition={{ ...t, ease: EASE.raise, delay: t.delay + 0.1 * k }}
        >
          {string}
        </motion.div>
        <motion.div
          style={{ position: 'absolute', inset: 0, originX: 0.5, originY: 0 }}
          initial={{ y: 0, rotate: 0, opacity: 1 }}
          animate={{ y: STAGE_H - y + 40, rotate: 28, opacity: [1, 1, 0] }}
          transition={t}
        >
          {children}
        </motion.div>
      </div>
    );
  }

  return (
    <motion.div
      className={className}
      style={{ ...box, ...style }}
      // `false` would start at the target: a raise has to start from where it hangs
      initial={move === 'lower' ? { y: out } : move === 'raise' ? { y: 0 } : false}
      animate={{ y: move === 'raise' ? out : 0 }}
      transition={t}
    >
      {string}
      {children}
    </motion.div>
  );
}

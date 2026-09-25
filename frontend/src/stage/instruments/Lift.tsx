'use client';

/**
 * The lift: the platform inside the trap that brings things up through the floor and takes
 * them back down. It raises the vote's table (and lowers it again with the count on it), and at
 * the lynch it raises the voted-out seat's role card. What rides it comes out of the hole and
 * goes back into it: everything below the hole's foot is cut away, so nothing shows under the
 * floor on the way.
 *
 * `slab` draws the platform itself, a square of boards under what it carries (the table's);
 * the card rides it bare, behind the stand's box. At rest the lift is simply up; a scene that
 * has sent it down leaves it out. Timings from the benches: the table up 1.4 s after 0.55 s,
 * down 1.5 s after 0.35 s (rev 64); the card up 1.3 s after 0.3 s (rev 65).
 */
import { motion } from 'motion/react';
import type { ReactNode } from 'react';
import { useMotionScale } from '../motion';
import { BOARD, BOARD2, K2 } from '../paint/materials';
import { STAGE_H, STAGE_W, type StageGeometry } from '../units';
import { trapGeometry } from './Floor';

export type LiftMove = 'rise' | 'sink';

export interface LiftProps {
  g: StageGeometry;
  /** How far below its resting place the load starts (rise) or ends (sink), in units. */
  travel: number;
  /** What plays; omit for up, at rest. */
  move?: LiftMove | null;
  delay?: number;
  duration?: number;
  ease?: [number, number, number, number];
  /** Draw the platform under the load. */
  slab?: boolean;
  children?: ReactNode;
}

const TIMING = {
  rise: { delay: 0.55, duration: 1.4, ease: [0.35, 0.75, 0.4, 1] },
  sink: { delay: 0.35, duration: 1.5, ease: [0.6, 0.05, 0.7, 0.6] },
} as const;

/** The lift's platform: boards inside the opening, a dark rim left round them. */
function Slab({ g }: { g: StageGeometry }) {
  const t = trapGeometry(g),
    rim = Math.max(4, 0.011 * STAGE_W);
  const x = t.x0 + rim,
    w = t.trapW - 2 * rim,
    top = t.holeTop + rim,
    h = t.holeBot - rim - top;
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
      <path
        d={`M${x},${top} h${w} v${h} h${-w}Z`}
        fill={BOARD}
        stroke={K2}
        strokeWidth={2}
        strokeLinejoin="round"
      />
      <path
        d={`M${x + 6},${top + h * 0.5} H${x + w - 6}`}
        stroke={BOARD2}
        strokeWidth={1.4}
        opacity={0.7}
      />
      <rect x={x} y={top} width={w} height={h} fill="#000" opacity={0.12} />
    </svg>
  );
}

export function Lift({
  g,
  travel,
  move,
  delay,
  duration,
  ease,
  slab = false,
  children,
}: LiftProps) {
  const k = useMotionScale();
  const t = trapGeometry(g),
    rim = Math.max(4, 0.011 * STAGE_W),
    clipY = t.holeBot - rim;
  const tm = move ? TIMING[move] : null;
  const transition = {
    delay: (delay ?? tm?.delay ?? 0) * k,
    duration: (duration ?? tm?.duration ?? 0) * k,
    ease: ease ?? (tm ? [...tm.ease] : undefined),
  };
  // the cut: a box from well above the frame down to the platform's foot; the world inside it
  // is put back at its own coordinates
  const above = STAGE_H;
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        top: -above,
        width: STAGE_W,
        height: above + clipY,
        overflow: 'hidden',
        pointerEvents: 'none',
      }}
    >
      <motion.div
        style={{
          position: 'absolute',
          left: 0,
          top: above,
          width: STAGE_W,
          height: STAGE_H,
        }}
        initial={move === 'rise' ? { y: travel } : move === 'sink' ? { y: 0 } : false}
        animate={{ y: move === 'sink' ? travel : 0 }}
        transition={transition}
      >
        {slab ? <Slab g={g} /> : null}
        {children}
      </motion.div>
    </div>
  );
}

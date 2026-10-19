'use client';

/**
 * The lift: brings things up into the shot from below and takes them back down. It raises the
 * vote's table from under the frame's foot (and lowers it again with the count on it), and at
 * the lynch the voted-out seat's role card behind the stand. Everything below its cut is cut
 * away, so nothing shows coming up: the frame's foot for the table (it stands whole on the
 * floor, 2026-10-19), the stand's floor for the card.
 *
 * At rest the lift is simply up; a scene that has sent it down leaves it out. Timings from the
 * benches: the table up 1.4 s after 0.55 s, down 1.5 s after 0.35 s (rev 64); the card up 1.3 s
 * after 0.3 s (rev 65).
 *
 * While it moves the load is its own compositor layer, so the
 * browser slides the picture it already has instead of redrawing the table every frame; not on
 * a phone, where that layer is full-stage for the whole beat and takes the light, the grade and
 * the HUD onto layers with it (build log §8.7): there the table is redrawn as it moves. `box`
 * bounds the moving load to what rides it (Bounded.tsx): without it the load is a full-stage
 * box, repainted whole each frame on a phone (§8.10).
 */
import { motion, useMotionValue } from 'motion/react';
import type { ReactNode } from 'react';
import { useMotionScale, useSteps } from '../motion';
import { STAGE_H, STAGE_W, type StageGeometry } from '../units';
import type { Box } from './Bounded';

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
  /** The load's bounds at rest, in units (its top may be above the frame): the moving box. */
  box?: Box;
  /** Where the load is cut, in units: by default the floor under the stand, behind its box. */
  cut?: number;
  children?: ReactNode;
}

const TIMING = {
  rise: { delay: 0.55, duration: 1.4, ease: [0.35, 0.75, 0.4, 1] },
  sink: { delay: 0.35, duration: 1.5, ease: [0.6, 0.05, 0.7, 0.6] },
} as const;

export function Lift({
  g,
  travel,
  move,
  delay,
  duration,
  ease,
  box,
  cut,
  children,
}: LiftProps) {
  const k = useMotionScale();
  const step = useSteps();
  // the stand's floor: a lip under the rail, where the old trap's foot was
  const clipY = cut ?? g.railY + 0.057 * STAGE_H - Math.max(4, 0.011 * STAGE_W);
  const tm = move ? TIMING[move] : null;
  const transition = step({
    delay: (delay ?? tm?.delay ?? 0) * k,
    duration: (duration ?? tm?.duration ?? 0) * k,
    ease: ease ?? (tm ? [...tm.ease] : undefined),
  });
  // the load's offset below its resting place
  const y = useMotionValue(move === 'rise' ? travel : 0);
  // the cut: a box from well above the frame down to the cut; the world inside it
  // is put back at its own coordinates
  const above = STAGE_H;
  // the moving box: the load's bounds, or the stage; inside it the stage's coordinates
  const bx = box ? Math.max(box.x, 0) : 0,
    by = box ? Math.max(box.y, -above) : 0,
    bw = box ? Math.min(box.x + box.w, STAGE_W) - bx : STAGE_W,
    bh = box ? Math.min(box.y + box.h, clipY) - by : STAGE_H;
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
        // on a phone the load keeps no layer (stage.css `[data-lift-load]`): a full-stage layer
        // for the beat, and every layer drawn over it, is what the phone cannot hold (§8.7)
        data-lift-load=""
        style={{
          position: 'absolute',
          left: bx,
          top: above + by,
          width: bw,
          height: bh,
          overflow: box ? 'hidden' : undefined,
          willChange: move ? 'transform' : undefined,
          y,
        }}
        initial={move === 'rise' ? { y: travel } : move === 'sink' ? { y: 0 } : false}
        animate={{ y: move === 'sink' ? travel : 0 }}
        transition={transition}
      >
        <div
          style={{
            position: 'absolute',
            left: -bx,
            top: -by,
            width: STAGE_W,
            height: STAGE_H,
          }}
        >
          {children}
        </div>
      </motion.div>
    </div>
  );
}

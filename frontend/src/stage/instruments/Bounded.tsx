'use client';

/**
 * A moving wrapper no bigger than what it moves. A figure or a card is placed in stage
 * coordinates, so the easy wrapper to move it with is a full-stage box; but a browser repaints
 * the whole of a moving box each frame, not only what is drawn in it, and on a phone with no
 * GPU layer for the move (build log §8.7) that was the whole stage repainted every frame, the
 * wing's grey dead tiles and the light under them with it (§8.10). This box is the load's own
 * bounds (with `pad` round them for a shadow or a glow), clipped, and inside it the stage's
 * coordinates are put back, so what rides it is placed as before. Moves in percent are of the
 * box now: give them in units.
 */
import { motion, type HTMLMotionProps } from 'motion/react';
import type { ReactNode } from 'react';
import { STAGE_H, STAGE_W } from '../units';

export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface BoundedProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
  box: Box;
  /** Room round the box for what hangs over it (a shadow, a glow), in units. */
  pad?: number;
  children?: ReactNode;
}

export function Bounded({ box, pad = 0, children, style, ...motionProps }: BoundedProps) {
  const left = box.x - pad,
    top = box.y - pad;
  return (
    <motion.div
      {...motionProps}
      style={{
        ...style,
        position: 'absolute',
        left,
        top,
        width: box.w + 2 * pad,
        height: box.h + 2 * pad,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: -left,
          top: -top,
          width: STAGE_W,
          height: STAGE_H,
        }}
      >
        {children}
      </div>
    </motion.div>
  );
}

/** The band the stand fades in: the pit's full width from a little above the rail down. */
export function standBand(railY: number, above = 100): Box {
  return { x: 0, y: railY - above, w: STAGE_W, h: STAGE_H - railY + above };
}

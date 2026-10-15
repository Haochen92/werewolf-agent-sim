'use client';

/**
 * A thing turned over in place: a card from its back to its face, a chip from its head to a
 * sigil. It squeezes to an edge and opens again, and the side showing swaps at the edge, so
 * nothing moves across the stage to say it changed (bench rev 75 `flip`: 0.85 s, linear).
 *
 * Not played, it shows the side it has landed on; played, it starts from the other one.
 */
import { motion } from 'motion/react';
import type { ReactNode } from 'react';
import { useMotionScale } from '../motion';

export function Flip({
  back,
  face,
  turn,
  delay = 0,
}: {
  /** What shows before the turn. */
  back: ReactNode;
  /** What shows after it (and at rest). */
  face: ReactNode;
  /** Play the turn. */
  turn: boolean;
  delay?: number;
}) {
  const k = useMotionScale();
  const fill = { position: 'absolute', inset: 0 } as const;
  if (!turn) return <div style={fill}>{face}</div>;
  const t = { duration: 0.85 * k, delay: delay * k, ease: 'linear' as const };
  const swap = { ...t, times: [0, 0.5, 0.5, 1] };
  return (
    <motion.div
      style={fill}
      initial={{ scaleX: 1 }}
      animate={{ scaleX: [1, 0.05, 1] }}
      transition={{ ...t, times: [0, 0.5, 1] }}
    >
      <motion.div
        style={fill}
        initial={{ opacity: 1 }}
        animate={{ opacity: [1, 1, 0, 0] }}
        transition={swap}
      >
        {back}
      </motion.div>
      <motion.div
        style={fill}
        initial={{ opacity: 0 }}
        animate={{ opacity: [0, 0, 1, 1] }}
        transition={swap}
      >
        {face}
      </motion.div>
    </motion.div>
  );
}

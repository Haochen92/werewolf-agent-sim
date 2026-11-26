'use client';

/**
 * A thing turned over in place: a card from its back to its face, a chip from its head to a
 * sigil. It squeezes to an edge and opens again, and the side showing swaps at the edge, so
 * nothing moves across the stage to say it changed (bench rev 75 `flip`: 0.85 s, linear).
 *
 * Not played, it shows the side it has landed on; played, it starts from the other one.
 *
 * On a phone the squeeze steps at film's rate like every other move (`useSteps`), and the sides
 * swap by `visibility`, not an opacity fade: an animated opacity gives each side a GPU layer for
 * the length of the turn, and the deal's ten cards turning at once made twenty, the layer churn
 * build log §8.9 warns of (owner, 2026-10-22: the deal lagged on a phone; a trace of the face-up
 * beat read 1.2 s of main thread in 2 s, Layerize alone 225 ms). The swap was already instant
 * at the edge, so it reads the same.
 */
import { motion } from 'motion/react';
import type { ReactNode } from 'react';
import { useMotionScale, useSteps } from '../motion';

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
  const step = useSteps();
  const fill = { position: 'absolute', inset: 0 } as const;
  if (!turn) return <div style={fill}>{face}</div>;
  const t = { duration: 0.85 * k, delay: delay * k, ease: 'linear' as const };
  const swap = { ...t, times: [0, 0.5, 0.5, 1] };
  return (
    <motion.div
      style={fill}
      initial={{ scaleX: 1 }}
      animate={{ scaleX: [1, 0.05, 1] }}
      // the ease runs per half of the turn, so the steps are counted over half its length
      transition={{
        ...t,
        times: [0, 0.5, 1],
        ease: step({ ...t, duration: t.duration / 2 }).ease,
      }}
    >
      <motion.div
        style={fill}
        initial={{ visibility: 'visible' }}
        animate={{ visibility: ['visible', 'visible', 'hidden', 'hidden'] }}
        transition={swap}
      >
        {back}
      </motion.div>
      <motion.div
        style={fill}
        initial={{ visibility: 'hidden' }}
        animate={{ visibility: ['hidden', 'hidden', 'visible', 'visible'] }}
        transition={swap}
      >
        {face}
      </motion.div>
    </motion.div>
  );
}

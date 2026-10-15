'use client';

/**
 * The curtain between the platform and the game: a plain dark sheet over the whole stage, the
 * bleed included, saying where the game begins. It falls over the departed platform
 * (`closing`), holds while the game is on its way, and lifts off the game's first beat
 * (`opening`). The replay page's departure (`StationDeparture`) holds it down and the page
 * fades the whole platform away instead, as the replay theatre's stage is laid out apart.
 *
 * A curtain that mounts lifting starts down: the platform swaps its whole scene for the curtain
 * as it lifts, which remounts it, and it would otherwise vanish at once.
 */
import { motion } from 'motion/react';
import { Layer } from '../Stage';
import { useMotionScale } from '../motion';
import { CURTAIN } from './station';
import styles from './Station.module.css';

export type CurtainState = 'closing' | 'opening';

export function Curtain({
  state,
  line,
}: {
  state: CurtainState;
  /** What the wait is, under the curtain's words, while it holds. */
  line?: string | null;
}) {
  const k = useMotionScale();
  return (
    <Layer name="hud">
      <motion.div
        className={styles.curtain}
        data-curtain={state}
        initial={{ opacity: state === 'closing' ? 0 : 1 }}
        animate={{ opacity: state === 'closing' ? 1 : 0 }}
        transition={{
          duration: (state === 'closing' ? CURTAIN.close : CURTAIN.open) * k,
          ease: 'easeInOut',
        }}
      >
        <p>The deal begins in the dining car</p>
        {line ? (
          <small className={styles.curtainLine} role="status">
            {line}
          </small>
        ) : null}
      </motion.div>
    </Layer>
  );
}

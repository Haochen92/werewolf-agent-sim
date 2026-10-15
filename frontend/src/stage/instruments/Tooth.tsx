'use client';

/**
 * One wolf's vote, as a tooth on the photo it chose. The pack's night ends when the second
 * tooth lands; a lone wolf's has one. The packmate's tooth sits on the left of the chin and
 * yours on the right, so two votes on one photo read as a bite, and two on different photos
 * read as a split.
 *
 * `land` plays the tooth dropping onto the photo as the vote arrives; without it the tooth is
 * simply there. A tooth is a mark arriving, not the photo moving: the photo stays still.
 */
import { motion } from 'motion/react';
import { useMotionScale, useSteps } from '../motion';
import styles from './NightRoom.module.css';

export interface ToothProps {
  /** The packmate's tooth sits left, yours (or the lone wolf's) right. */
  side: 'left' | 'right';
  /** Drop in after this many seconds; false = at rest. */
  land?: number | false;
}

export function Tooth({ side, land = false }: ToothProps) {
  const k = useMotionScale();
  const step = useSteps();
  const x = side === 'left' ? 36 : 52;
  return (
    <motion.svg
      className={styles.tooth}
      viewBox="0 0 100 100"
      aria-hidden="true"
      data-tooth={side}
      initial={land === false ? false : { opacity: 0, y: -24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={step({
        duration: 0.45 * k,
        delay: (land || 0) * k,
        ease: [0.3, 0.8, 0.4, 1],
      })}
    >
      <path
        d={`M${x} 58l6 16 6-16z`}
        fill="#f6f1e4"
        stroke="#24180c"
        strokeWidth="2.5"
        strokeLinejoin="round"
      />
    </motion.svg>
  );
}

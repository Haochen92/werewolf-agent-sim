'use client';

/**
 * The pin in the chosen doll: the night room's one mark of choosing, a dressmaker's pin pushed
 * in at an angle, its round head in the colour of the acting side (the card's colour: amber for
 * the town's roles, red for the pack, violet for the killer). Vector, over the doll's picture,
 * so the doll itself stays exactly as drawn.
 *
 * A tapped choice pushes it in along its own line; a choice the room arrives at is simply
 * there. Un-choosing draws it back out. Its parent (NightRoom) keeps it in an AnimatePresence
 * that starts still, so only a change made in the room plays.
 */
import { motion } from 'motion/react';
import { factionOf } from '../roles';
import { useMotionScale } from '../motion';
import { K2 } from '../paint/materials';
import styles from './NightRoom.module.css';

/** The card's colours (tokens.css), by side. */
const HEAD = {
  villagers: 'var(--town)',
  wolves: 'var(--wolf)',
  serial_killer: 'var(--sk)',
};

/** The pin's line, up and to the right from where it enters (degrees above the horizontal). */
const ANGLE = 52;

export interface PinProps {
  /** The acting role: the head's colour. */
  role: string;
  /** The doll's width in units: the pin is sized to it. */
  w: number;
}

export function Pin({ role, w }: PinProps) {
  const k = useMotionScale();
  const a = (ANGLE * Math.PI) / 180,
    L = 0.38 * w,
    r = 0.075 * w,
    hx = Math.cos(a) * L,
    hy = -Math.sin(a) * L,
    // the push: it starts this far back along its own line
    back = 0.16 * w;
  const head = HEAD[factionOf(role) ?? 'villagers'];
  const box = L + r * 2;
  return (
    <span className={styles.pin} data-pin={role}>
      <svg
        aria-hidden="true"
        viewBox={`${-box} ${-box} ${2 * box} ${2 * box}`}
        style={{
          position: 'absolute',
          left: -box,
          top: -box,
          width: 2 * box,
          height: 2 * box,
          overflow: 'visible',
        }}
      >
        {/* where it went in: a small dent in the felt */}
        <ellipse cx={0} cy={0} rx={r * 0.5} ry={r * 0.32} fill="#1a100a" opacity={0.45} />
        <motion.g
          initial={{ x: Math.cos(a) * back, y: -Math.sin(a) * back, opacity: 0 }}
          animate={{ x: 0, y: 0, opacity: 1 }}
          exit={{ x: Math.cos(a) * back * 0.7, y: -Math.sin(a) * back * 0.7, opacity: 0 }}
          transition={{
            duration: 0.32 * k,
            delay: 0.1 * k,
            ease: [0.3, 0.7, 0.4, 1],
            opacity: { duration: 0.1 * k, delay: 0.1 * k },
          }}
        >
          <path
            d={`M0,0 L${hx},${hy}`}
            stroke={K2}
            strokeWidth={r * 0.55}
            strokeLinecap="round"
          />
          <path
            d={`M0,0 L${hx},${hy}`}
            stroke="#cfc8ba"
            strokeWidth={r * 0.28}
            strokeLinecap="round"
          />
          <circle
            cx={hx}
            cy={hy}
            r={r}
            style={{ fill: head }}
            stroke={K2}
            strokeWidth={r * 0.28}
          />
          <circle
            cx={hx - r * 0.32}
            cy={hy - r * 0.34}
            r={r * 0.3}
            fill="#fff"
            opacity={0.7}
          />
        </motion.g>
      </svg>
    </span>
  );
}

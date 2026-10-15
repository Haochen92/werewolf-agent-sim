'use client';

/**
 * The pin in the chosen photo: the night room's one mark of choosing, a dressmaker's pin pushed
 * through it at an angle, its round head in the colour of the acting side (the card's colour:
 * amber for the town's roles, red for the pack, violet for the killer). Vector, over the photo,
 * so the print itself stays exactly as it is.
 *
 * A tapped choice pushes it in along its own line; a choice the room arrives at is simply
 * there. Un-choosing draws it back out. Once the act is sent it goes fully `home`, a short
 * last push. Its parent (NightRoom) keeps it in an AnimatePresence that starts still, so only
 * a change made in the room plays. Past where it enters, the shaft is hidden: it is in the wall.
 */
import { useId } from 'react';
import { motion } from 'motion/react';
import { factionOf } from '../roles';
import { useMotionScale, useSteps } from '../motion';
import { K2 } from '../paint/materials';
import styles from './NightRoom.module.css';

/** The card's colours (tokens.css), by side: the pin's head and the sealed plate's seal. */
const HEAD = {
  villagers: 'var(--town)',
  wolves: 'var(--wolf)',
  serial_killer: 'var(--sk)',
  neutral_benign: 'var(--benign)',
};

/** The pin's line, up and to the right from where it enters (degrees above the horizontal). */
const ANGLE = 52;

/** The acting side's colour, for a role. */
export function pinColour(role: string): string {
  return HEAD[factionOf(role) ?? 'villagers'];
}

export interface PinProps {
  /** The acting role: the head's colour. */
  role: string;
  /** The photo's width in units: the pin is sized to it. */
  w: number;
  /** Where it goes in, as percentages across and down the photo. */
  at?: readonly [number, number];
  /** The act is sent: pushed fully home. */
  home?: boolean;
}

export function Pin({ role, w, at = [62, 40], home = false }: PinProps) {
  const k = useMotionScale();
  const step = useSteps();
  const clip = 'pin' + useId().replace(/[^A-Za-z0-9_-]/g, '');
  const a = (ANGLE * Math.PI) / 180,
    L = 0.38 * w,
    r = 0.075 * w,
    hx = Math.cos(a) * L,
    hy = -Math.sin(a) * L,
    // the push: it starts this far back along its own line
    back = 0.16 * w,
    // the last push once the act is sent
    deep = 0.08 * w;
  const head = pinColour(role);
  const box = L + r * 2;
  return (
    <span
      className={styles.pin}
      data-pin={role}
      style={{ left: `${at[0]}%`, top: `${at[1]}%` }}
    >
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
        <defs>
          {/* the side of the entry the pin shows on; past it the shaft is in the wall */}
          <clipPath id={clip}>
            <rect
              x={0}
              y={-box}
              width={box * 3}
              height={box * 2}
              transform={`rotate(${-ANGLE})`}
            />
          </clipPath>
        </defs>
        {/* where it went in: a small dent in the print */}
        <ellipse cx={0} cy={0} rx={r * 0.5} ry={r * 0.32} fill="#1a100a" opacity={0.45} />
        <g clipPath={`url(#${clip})`}>
          <motion.g
            data-home={home || undefined}
            initial={{ x: Math.cos(a) * back, y: -Math.sin(a) * back, opacity: 0 }}
            animate={
              home
                ? { x: -Math.cos(a) * deep, y: Math.sin(a) * deep, opacity: 1 }
                : { x: 0, y: 0, opacity: 1 }
            }
            exit={{ x: Math.cos(a) * back * 0.7, y: -Math.sin(a) * back * 0.7, opacity: 0 }}
            transition={
              home
                ? step({ duration: 0.2 * k, delay: 0.05 * k, ease: [0.5, 0, 0.2, 1] })
                : step({
                    duration: 0.32 * k,
                    delay: 0.1 * k,
                    ease: [0.3, 0.7, 0.4, 1],
                    opacity: { duration: 0.1 * k, delay: 0.1 * k },
                  })
            }
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
        </g>
      </svg>
    </span>
  );
}

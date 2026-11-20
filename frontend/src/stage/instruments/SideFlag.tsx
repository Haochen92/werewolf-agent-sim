'use client';

/**
 * A side's pennant on the night room's line, where the other rooms hang their photos: the
 * speculator's four picks (the town, the wolves, the lone killer, itself), each the side's own
 * felt pennant (`FactionMark`) pegged to the twine, its name on the wall under it.
 *
 * Chosen is light and a lift, as a photo is (`Photo`): the chosen pennant comes forward in the
 * candle's light, the others darken where they hang. The light is a filter on the pennant, not
 * a sheet over it, because the pennant is not a rectangle.
 */
import { motion } from 'motion/react';
import type { ReactNode } from 'react';
import type { Faction } from '../roles';
import { useMotionScale, useSteps } from '../motion';
import { FactionMark } from './FactionMark';
import { Peg } from './Photo';
import styles from './NightRoom.module.css';

/** How much the chosen pennant comes forward, as a photo does. */
const LIFT = 1.08;

/** How each pennant hangs off true, in degrees, by its place on the line. */
const TILT = [-2.2, 1.6, -1.3, 2.4];

/** The pennant's svg against its box: the 48 grid's pennant is 33 wide, from y 3.5. */
const SVG_K = 1.3,
  SVG_TOP = (3.5 / 48) * SVG_K;

/** At rest, chosen, and darkened around another: the pennant's light. */
const FILTER = {
  even: 'brightness(1) drop-shadow(3px 5px 6px rgba(8, 5, 3, 0.55))',
  lit: 'brightness(1.12) drop-shadow(0 0 10px rgba(255, 190, 110, 0.45))',
  dim: 'brightness(0.38) drop-shadow(3px 5px 6px rgba(8, 5, 3, 0.55))',
};

export interface SideFlagProps {
  /** The side whose pennant it is. */
  faction: Faction;
  /** Its name under it ("Town", "Yourself"), and the button's. */
  label: string;
  /** Its place on the line: how it hangs off true. */
  index: number;
  /** Its centre x and its top, in units, as a photo's. */
  x: number;
  top: number;
  w: number;
  h: number;
  light?: 'lit' | 'dim';
  /** Tapping the pennant chooses it; without this it is only shown. */
  onChoose?: () => void;
  /** The pin, drawn over it. */
  children?: ReactNode;
  /** Fade in on arrival, after this many seconds; false = at rest. */
  arrive?: number | false;
}

export function SideFlag({
  faction,
  label,
  index,
  x,
  top,
  w,
  h,
  light,
  onChoose,
  children,
  arrive = false,
}: SideFlagProps) {
  const k = useMotionScale();
  const step = useSteps();
  const Tag = onChoose ? motion.button : motion.div;
  return (
    <Tag
      type={onChoose ? 'button' : undefined}
      className={styles.photo}
      data-side={faction}
      data-light={light ?? 'even'}
      aria-label={onChoose ? label : undefined}
      aria-pressed={onChoose ? light === 'lit' : undefined}
      onClick={onChoose}
      style={{
        left: x - w / 2,
        top,
        width: w,
        height: h,
        transformOrigin: '50% 0',
        zIndex: light === 'lit' ? 2 : undefined,
      }}
      initial={arrive === false ? false : { opacity: 0, scale: 1 }}
      animate={{ opacity: 1, scale: light === 'lit' ? LIFT : 1 }}
      transition={{
        duration: 0.6 * k,
        delay: (arrive || 0) * k,
        scale: step({ duration: 0.4 * k, ease: [0.3, 0.7, 0.4, 1] }),
      }}
    >
      <span
        className={styles.hang}
        style={{ rotate: `${TILT[index % TILT.length]}deg`, transformOrigin: '50% 0' }}
      >
        <motion.span
          className={styles.flag}
          style={{
            left: (w * (1 - SVG_K)) / 2,
            top: -w * SVG_TOP,
            width: w * SVG_K,
            height: w * SVG_K,
          }}
          initial={false}
          animate={{ filter: FILTER[light ?? 'even'] }}
          transition={{ duration: 0.6 * k }}
        >
          <FactionMark faction={faction} format="pennant" aria-hidden="true" />
        </motion.span>
        <span className={styles.flagName} style={{ top: w * 1.08 }}>
          {label}
        </span>
        <Peg w={w} />
        {children}
      </span>
    </Tag>
  );
}

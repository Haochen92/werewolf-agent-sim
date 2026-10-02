'use client';

/**
 * A seat's photograph on the night room's line: the character's head portrait printed small,
 * a cream border a little aged, pegged to the twine under the rack (or on its own length of
 * twine below it, so a full line hangs at two heights). They appear only in the acting seat's
 * own room at night: they are the other seats, seen from your chair, and you choose one by
 * tapping it.
 *
 * The seat's numeral is written on the border in vector, never baked into the picture. Each
 * print hangs a little crooked, by its seat, so the same seat always hangs the same way.
 *
 * Chosen is light, and a small lift towards you: the chosen print brightens in the candle's
 * light and comes forward a touch (a scale, from its peg), the others darken where they hang.
 * The room's light does the rest.
 */
import { motion } from 'motion/react';
import type { ReactNode } from 'react';
import type { Character } from '@/assets/manifest';
import { ChipSprite } from '../cast/ChipSprite';
import { useMotionScale, useSteps } from '../motion';
import styles from './NightRoom.module.css';

/** How much the chosen print comes forward, and how dark the others go (0–1). */
const LIFT = 1.08,
  DIM = 0.62;

/** How each seat's print hangs off true, in degrees (a fixed table, so it never changes). */
const TILT = [-2.4, 1.7, -1.1, 2.9, -3.1, 0.8, 2.3, -1.8, 1.3];

export interface PhotoProps {
  character: Character;
  /** The numeral on its border, 1–9. */
  seat: number;
  /** Its centre x and its top, in units. */
  x: number;
  top: number;
  /** Its width in units (the height follows: PHOTO_H). */
  w: number;
  h: number;
  /** How far below the line its top hangs, in units: a short drop is pegged to the line itself. */
  drop: number;
  /** Lit: the chosen one. Dim: the room has dimmed around another. Neither: evenly lit. */
  light?: 'lit' | 'dim';
  /** Tapping the photo chooses it; without this it is only shown. */
  onChoose?: () => void;
  /** Marks over the photo (a tooth, the pin), drawn over it. */
  children?: ReactNode;
  /** Fade in on arrival, after this many seconds; false = at rest. */
  arrive?: number | false;
}

export function Photo({
  character,
  seat,
  x,
  top,
  w,
  h,
  drop,
  light,
  onChoose,
  children,
  arrive = false,
}: PhotoProps) {
  const k = useMotionScale();
  const step = useSteps();
  const Tag = onChoose ? motion.button : motion.div;
  const tilt = TILT[(seat - 1) % TILT.length] ?? 0;
  // the peg: a clothes-peg's two wooden legs and its spring, clipping the print's top edge
  const pw = w * 0.13,
    ph = w * 0.3;
  return (
    <Tag
      type={onChoose ? 'button' : undefined}
      className={styles.photo}
      data-seat={seat}
      data-light={light ?? 'even'}
      aria-label={onChoose ? `Seat ${seat}` : undefined}
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
      {/* crooked about where it hangs from the line, so a long drop swings from its knot */}
      <span
        className={styles.hang}
        style={{ rotate: `${tilt}deg`, transformOrigin: `50% ${-drop}px` }}
      >
        {drop > ph * 0.5 ? (
          <svg
            className={styles.string}
            viewBox={`0 0 4 ${drop}`}
            preserveAspectRatio="none"
            style={{ height: drop, top: -drop }}
            aria-hidden="true"
          >
            <path d={`M2,0 V${drop}`} stroke="#2a1d11" strokeWidth="2" />
            <path
              d={`M1.4,0 V${drop}`}
              stroke="#a88a66"
              strokeOpacity=".45"
              strokeWidth=".6"
            />
          </svg>
        ) : null}
        <span className={styles.print}>
          <span className={styles.picture}>
            <ChipSprite character={character} />
          </span>
          <svg className={styles.photoNumeral} viewBox="0 0 100 30" aria-hidden="true">
            <text x="50" y="26" textAnchor="middle" fontSize="30" fill="#2a1d10">
              {seat}
            </text>
          </svg>
          {/* the chosen print catches the candle; the others darken where they hang */}
          <motion.span
            className={styles.glow}
            initial={false}
            animate={{ opacity: light === 'lit' ? 1 : 0 }}
            transition={{ duration: 0.6 * k }}
          />
          <motion.span
            className={styles.dim}
            initial={false}
            animate={{ opacity: light === 'dim' ? DIM : 0 }}
            transition={{ duration: 0.6 * k }}
          />
        </span>
        <svg
          className={styles.peg}
          viewBox="0 0 13 30"
          style={{ left: (w - pw) / 2, top: -ph * 0.42, width: pw, height: ph }}
          aria-hidden="true"
        >
          <rect
            x="1"
            y="0.5"
            width="5.2"
            height="29"
            rx="1.6"
            fill="#b88c5a"
            stroke="#3a2412"
            strokeWidth=".8"
          />
          <rect
            x="6.8"
            y="0.5"
            width="5.2"
            height="29"
            rx="1.6"
            fill="#a47a4a"
            stroke="#3a2412"
            strokeWidth=".8"
          />
          <rect
            x="0.6"
            y="10.5"
            width="11.8"
            height="3.2"
            rx="1"
            fill="#8d8a84"
            stroke="#3a3530"
            strokeWidth=".6"
          />
          <path d="M2,2 V26" stroke="#e2c08e" strokeOpacity=".45" strokeWidth=".8" />
        </svg>
        {children}
      </span>
    </Tag>
  );
}

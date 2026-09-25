'use client';

/**
 * A seat's plush doll, hung by the head from a hook under the shelf. Dolls appear only in the
 * acting seat's own room at night (the handoff's token rule): they are the other seats, seen
 * from your chair, and you choose one by tapping it.
 *
 * Every doll is drawn at one head-to-toe height, whatever its ears or hat, so the row reads
 * as one row: `PLUSH_SCALE` corrects each sprite, and the crown of every head meets the end
 * of its string at the same height (ears, hats and antennae rise past it). The seat's
 * numeral is drawn over the sprite in vector, never baked into it.
 *
 * Chosen is light, never movement: a lit doll is a touch brighter, a dimmed one fades back.
 * The room's light does the rest.
 */
import Image from 'next/image';
import { motion } from 'motion/react';
import type { ReactNode } from 'react';
import { PLUSH_SCALE, SPRITES, type Character } from '@/assets/manifest';
import { useMotionScale } from '../motion';
import styles from './NightRoom.module.css';

/**
 * The share of a sprite's height (at scale 1) from the crown of the head to the feet,
 * measured by eye on the eleven third-generation dolls laid side by side with their scales.
 */
const HEAD_TO_TOE = 0.85;
/** A doll's head-to-toe height for its hook's width, as the shelf bench hangs them. */
export const DOLL_BODY_PER_WIDTH = 1.18;

/** Where a doll's picture sits, in units: its crown at `hangY`, centred on `x`. */
export function plushBox(character: Character, x: number, hangY: number, body: number) {
  const img = SPRITES.plush[character];
  const h = (body * PLUSH_SCALE[character]) / HEAD_TO_TOE,
    w = (h * img.width) / img.height;
  return { left: x - w / 2, top: hangY + body - h, w, h, aspect: img.width / img.height };
}

export interface PlushProps {
  character: Character;
  /** The numeral on its tummy, 1–9. */
  seat: number;
  /** The hook's x, and where its string ends (the crown of the head), in units. */
  x: number;
  hangY: number;
  /** The head-to-toe height every doll in the row shares, in units. */
  body: number;
  /** Lit: the chosen one. Dim: the room has dimmed around another. Neither: evenly lit. */
  light?: 'lit' | 'dim';
  /** Tapping the doll chooses it; without this the doll is only shown. */
  onChoose?: () => void;
  /** Marks on the doll (a tooth), drawn over it. */
  children?: ReactNode;
  /** Fade in on arrival, after this many seconds; false = at rest. */
  arrive?: number | false;
}

export function Plush({
  character,
  seat,
  x,
  hangY,
  body,
  light,
  onChoose,
  children,
  arrive = false,
}: PlushProps) {
  const k = useMotionScale();
  const box = plushBox(character, x, hangY, body);
  const nh = 38 * box.aspect;
  const look =
    light === 'dim'
      ? { opacity: 0.55, filter: 'saturate(0.6) brightness(0.85)' }
      : light === 'lit'
        ? { opacity: 1, filter: 'saturate(1) brightness(1.08)' }
        : { opacity: 1, filter: 'saturate(1) brightness(1)' };
  const Tag = onChoose ? motion.button : motion.div;
  return (
    <Tag
      type={onChoose ? 'button' : undefined}
      className={styles.plush}
      data-seat={seat}
      data-light={light ?? 'even'}
      aria-label={onChoose ? `Seat ${seat}` : undefined}
      aria-pressed={onChoose ? light === 'lit' : undefined}
      onClick={onChoose}
      style={{ left: box.left, top: box.top, width: box.w, height: box.h }}
      initial={arrive === false ? false : { ...look, opacity: 0 }}
      animate={look}
      transition={{ duration: 0.6 * k, delay: (arrive || 0) * k }}
    >
      <Image src={SPRITES.plush[character]} alt="" unoptimized draggable={false} />
      <svg
        className={styles.numeral}
        viewBox="0 0 100 100"
        style={{ left: '31%', top: `${66 - nh / 2}%`, width: '38%', height: `${nh}%` }}
        aria-hidden="true"
      >
        <circle cx="50" cy="50" r="46" fill="#efe4cb" stroke="#24180c" strokeWidth="5" />
        <circle
          cx="50"
          cy="50"
          r="36"
          fill="none"
          stroke="#8d7a55"
          strokeWidth="3"
          strokeDasharray="6 5"
        />
        <text x="50" y="68" textAnchor="middle" fontSize="54" fill="#24180c">
          {seat}
        </text>
      </svg>
      {children}
    </Tag>
  );
}

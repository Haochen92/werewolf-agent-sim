'use client';

/**
 * A seat's puppet at the stand: the felt figure (a WebP sprite) with the seat's numeral drawn
 * on its belly in vector, because a numeral is state and state is never baked into a sprite.
 *
 * Every character is scaled to one head-to-toe height, measured from its silhouette (`BODY`
 * in the manifest), so a tall-eared hare and a round onion stand at the same size and only
 * their ears and hats rise above the line. The feet stand a little below the rail, hidden by
 * the stand's box, as a glove puppet's would. The numbers are the cast module's `Cast.pup`
 * (docs/design_2026-09-25/kits/cast.js), with `dx` and `scale` for two or three at the stand.
 *
 * `arrive` plays the puppet rising into the stand from behind it; without it the puppet is
 * simply there, at rest, which is how every seek and refresh lands.
 */
import Image from 'next/image';
import { motion } from 'motion/react';
import { BODY, SPRITES, type Character, type DayState } from '@/assets/manifest';
import type { StageGeometry } from '../units';
import { useMotionScale } from '../motion';
import styles from './Puppet.module.css';

export interface PuppetProps {
  g: StageGeometry;
  character: Character;
  /** The numeral on the belly, 1–9. */
  seat: number;
  state: DayState;
  /** Offset from the stand's centre line, and a scale, for two or three at the stand. */
  dx?: number;
  scale?: number;
  /** Rise into the stand from below (seconds of delay before it starts); false = at rest. */
  arrive?: number | false;
  /** Called once the rise has finished. */
  onArrived?: () => void;
}

/** The rise, from the deal bench (rev 75): 0.8 s on the kit's ease. */
const RISE = { duration: 0.8, ease: [0.3, 0.8, 0.4, 1] as const };

/**
 * Nothing rises above this line, in units: the top strip's foot with a little air. The kit let
 * hats and antennae rise off the stage; the owner ruled (2026-09-26) that a cut head reads as
 * a mistake. A figure whose top would pass it sinks behind the rail first (the stand's pit
 * hides the feet), by at most `SINK`, and shrinks for whatever is left.
 */
const HEADROOM = 60;
const SINK = 100;

/** Where the figure's box sits, in units, for a character in a state. */
export function puppetBox(
  g: StageGeometry,
  character: Character,
  state: DayState,
  dx = 0,
  scale = 1,
) {
  const b = BODY[character],
    img = SPRITES.day[character][state],
    aspect = img.width / img.height;
  // the kit's placement: one body height, the feet a little below the rail
  let h = (g.ph * 0.98 * scale) / b.body;
  const topOf = (hh: number, sink: number) =>
    g.railY + sink - hh * (b.top + b.body) + hh * b.body * 0.08;
  let top = topOf(h, 0);
  const over = HEADROOM - top;
  if (over > 0) {
    const sink = Math.min(over, SINK);
    if (over > sink) h = (g.railY + sink - HEADROOM) / (b.top + b.body - b.body * 0.08);
    top = topOf(h, sink);
  }
  const w = h * aspect;
  return { left: g.cx + dx - w / 2, top, w, h, aspect };
}

export function Puppet({
  g,
  character,
  seat,
  state,
  dx = 0,
  scale = 1,
  arrive = false,
  onArrived,
}: PuppetProps) {
  const k = useMotionScale();
  const box = puppetBox(g, character, state, dx, scale);
  const b = BODY[character];
  // the numeral's disc: 24% of the figure's width, centred, 62% of the way down the body
  const nh = 24 * box.aspect;
  const ntop = b.top * 100 + b.body * 100 * 0.62 - nh / 2;
  return (
    <motion.div
      className={styles.pup}
      style={{ left: box.left, top: box.top, width: box.w, height: box.h }}
      initial={arrive === false ? false : { y: '100%' }}
      animate={{ y: 0 }}
      transition={{ ...RISE, duration: RISE.duration * k, delay: (arrive || 0) * k }}
      onAnimationComplete={onArrived}
    >
      <Image
        src={SPRITES.day[character][state]}
        alt=""
        unoptimized
        priority
        draggable={false}
        className={styles.sprite}
      />
      <svg
        className={styles.numeral}
        viewBox="0 0 100 100"
        style={{ left: '38%', top: `${ntop}%`, width: '24%', height: `${nh}%` }}
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
    </motion.div>
  );
}

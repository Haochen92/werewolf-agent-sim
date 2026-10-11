'use client';

/**
 * The marks a night's acts leave, pinned beneath a chip at the morning and on the print in the
 * replay's rooms: the acting role's felt sigil tacked on like a patch (owner, 2026-09-30,
 * replacing bench 67's line drawings). A bite is the wolf's head, a knife the serial killer's
 * scythe, a bullet the vigilante's, a sigil the sigilist's (a necromancer's reanimated body leaves
 * its own kind's mark), the plaster (the healer's save) the cross, the lens (the
 * investigator's reading, on that seat's screen only) the magnifier. The wire names the
 * attacker's type, never the attacker, and a type is a role: a mark still says what was done,
 * never by whom.
 *
 * `k` is the mark's half-size in units (the sigil's 48 grid spans 2k). Played, a mark pops in
 * (bench rev 67 `markIn`).
 */
import { motion } from 'motion/react';
import type { AttackerType } from '@/types/contracts';
import { useMotionScale, useSteps } from '../motion';
import { MATERIALS as M } from '../paint/materials';
import { Sigil } from './Sigil';

export type ActKind = 'bite' | 'knife' | 'bullet' | 'sigil' | 'plaster' | 'lens';

/** The mark an attacker type leaves (`night_result.attacker_types`). */
export const ATTACK_MARK: Record<AttackerType, ActKind> = {
  wolves: 'bite',
  serial_killer: 'knife',
  vigilante: 'bullet',
  sigilist: 'sigil',
  reanimated_wolves: 'bite',
  reanimated_vigilante: 'bullet',
  reanimated_sigilist: 'sigil',
};

/** The role whose sigil stands for each act. */
export const MARK_ROLE: Record<ActKind, string> = {
  bite: 'wolf',
  knife: 'serial_killer',
  bullet: 'vigilante',
  sigil: 'sigilist',
  plaster: 'healer',
  lens: 'investigator',
};

/** Where the tack goes through each patch, on the sigil's 48 grid (on its felt, after its turn). */
const TACK: Record<ActKind, readonly [number, number]> = {
  bite: [24, 17],
  knife: [23, 9.5],
  bullet: [20, 30.5],
  sigil: [24, 12],
  plaster: [24, 14],
  lens: [19, 9.5],
};

/** Under this half-size (units) the patch drops its stitching, as a small sigil does. */
const SMALL_K = 30;

export interface ActMarkProps {
  kind: ActKind;
  /** Centre and half-size, in units. */
  x: number;
  y: number;
  k: number;
  /** Pop in (played), after this many seconds; false = at rest. */
  arrive?: number | false;
}

export function ActMark({ kind, x, y, k, arrive = false }: ActMarkProps) {
  const m = useMotionScale();
  const step = useSteps();
  const role = MARK_ROLE[kind];
  const [tx, ty] = TACK[kind];
  const half = k * 1.3;
  const small = k < SMALL_K;
  // the grid's 0..48 sits at -24..24: the sigil's own box (-2..50) nests at -26
  const at = { x: -26, y: -26, width: 52, height: 52 } as const;
  return (
    <motion.svg
      viewBox={`${-24 * 1.3} ${-24 * 1.3} ${48 * 1.3} ${48 * 1.3}`}
      style={{
        position: 'absolute',
        left: x - half,
        top: y - half,
        width: 2 * half,
        height: 2 * half,
        overflow: 'visible',
      }}
      aria-label={kind}
      role="img"
      data-mark={role}
      initial={arrive === false ? false : { scale: 0.2, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={step({
        duration: 0.5 * m,
        delay: (arrive || 0) * m,
        ease: [0.3, 1.5, 0.5, 1],
      })}
    >
      {/* the patch's shadow on the print: its own silhouette, flat and offset (no live filter) */}
      <g opacity={0.38} style={{ color: '#0c0703' }}>
        <Sigil role={role} small {...at} x={at.x + 1.6} y={at.y + 2.4} />
      </g>
      <Sigil role={role} variant="felt" small={small} {...at} />
      {/* the tack through it: a brass head, its rim and a glint */}
      <g transform={`translate(${tx - 24} ${ty - 24})`}>
        <ellipse cx={0.9} cy={1.5} rx={4.4} ry={3.6} fill="#0c0703" opacity={0.4} />
        <circle r={4.2} fill={M.brassLo} />
        <circle r={3.3} fill={M.brass} />
        <circle cx={-1.1} cy={-1.1} r={1.3} fill={M.brassHi} />
      </g>
    </motion.svg>
  );
}

'use client';

/**
 * The morning roll (owner, 2026-09-30): what the night did, read as a list on the walnut
 * notice rather than as sentences in a box. One row per death, the seat's chip, "Seat 1 ·
 * Villager" and how it went, each attacker's felt sigil before the words; a seat that
 * survived an attack gets a row too (the healer's save, which the log names), and a quiet
 * night is the one line. The game master's own words stay in the transcript.
 *
 * Played, the rows come in one after another, at the pace the report's hold gives them.
 * The roll names no roles until the cards have come down (owner, 2026-09-30): at the shutter
 * it lists the seats and how they went; the game's end, every card already down, reads it whole.
 */
import { motion } from 'motion/react';
import type { AttackerType } from '@/types/contracts';
import type { Character } from '@/assets/manifest';
import { ChipSprite } from '../cast/ChipSprite';
import { useMotionScale } from '../motion';
import { ROLE_NAME, seatNumber } from '../roles';
import { Sigil } from './Sigil';
import styles from './MorningRoll.module.css';

/** One row: a death, or a seat that was attacked and saved. */
export type RollRow =
  | { kind: 'death'; player: string; role: string; types: AttackerType[] }
  | { kind: 'save'; player: string; types: AttackerType[] };

/** The attacker type's sigil: the role that did it (the wolves' is the wolf's). */
const SIGIL_OF: Record<AttackerType, string> = {
  wolves: 'wolf',
  serial_killer: 'serial_killer',
  vigilante: 'vigilante',
};
/** How a seat went, in the game's words per attacker type (the game master's line). */
export const DIED: Record<AttackerType, string> = {
  wolves: 'killed by the wolves',
  serial_killer: 'stabbed by the serial killer',
  vigilante: 'shot by the vigilante',
};
export const BY: Record<AttackerType, string> = {
  wolves: 'the wolves',
  serial_killer: 'the serial killer',
  vigilante: 'the vigilante',
};

/** The words of a row's cause. */
export function causeOf(row: RollRow): string {
  const by = row.types.map((t) => BY[t]).join(' and ');
  if (row.kind === 'save') return `attacked by ${by}, saved by the healer`;
  return row.types.length === 1 ? DIED[row.types[0]] : `attacked by ${by}, and fell`;
}

/** Seconds after the notice lands that the first row comes in, and between rows. */
const FIRST = 0.9;
const EACH = 0.6;

export function MorningRoll({
  rows,
  cast,
  me,
  arrive = false,
  roles = true,
}: {
  rows: readonly RollRow[];
  cast: readonly Character[];
  me: string | null;
  arrive?: boolean;
  /** Name each dead seat's role; off before its card has come down. */
  roles?: boolean;
}) {
  const k = useMotionScale();
  if (!rows.length) return <p className={styles.quiet}>No one died in the night.</p>;
  return (
    <ul className={styles.roll} data-roll>
      {rows.map((r, i) => {
        const n = seatNumber(r.player);
        const character = cast[n - 1];
        const sigils = [
          ...r.types.map((t) => SIGIL_OF[t]),
          ...(r.kind === 'save' ? ['healer'] : []),
        ];
        return (
          <motion.li
            key={`${r.kind}-${r.player}`}
            className={styles.row}
            data-roll-row={r.kind}
            initial={arrive ? { opacity: 0 } : false}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 * k, delay: (FIRST + i * EACH) * k }}
          >
            {character ? (
              <span className={styles.chip}>
                <ChipSprite character={character} />
              </span>
            ) : null}
            <span className={styles.what}>
              <span className={styles.who}>
                Seat {n}
                {r.player === me ? ' (you)' : ''}
                {roles && r.kind === 'death' ? ` · ${ROLE_NAME[r.role] ?? r.role}` : ''}
              </span>
              <span className={styles.cause}>
                {sigils.map((s) => (
                  <Sigil key={s} role={s} variant="felt" small className={styles.sigil} />
                ))}
                <span>{causeOf(r)}</span>
              </span>
            </span>
          </motion.li>
        );
      })}
    </ul>
  );
}

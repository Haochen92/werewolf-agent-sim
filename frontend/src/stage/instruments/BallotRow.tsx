'use client';

/**
 * The seated human's ballot: a row of the candidates' chips and, at its end, an empty plate
 * that means abstain. Tap one to choose it (it lights, the rest dim: nothing moves to say
 * chosen), then confirm on the brass plate below, which names the vote. Once sent, the row
 * gives way to "Your ballot is in", which only this seat sees.
 *
 * The candidates are the server's list and nothing else (`abstain` is a choice only when the
 * server lists it). Props in, the choice out through `onChoose` and `onConfirm`: the scene
 * owns what is chosen, the container what is sent.
 */
import { motion } from 'motion/react';
import type { Character } from '@/assets/manifest';
import { ChipSprite } from '../cast/ChipSprite';
import type { TurnClock } from '../countdown';
import { useMotionScale } from '../motion';
import { seatNumber } from '../roles';
import styles from './BallotRow.module.css';
import { CountText } from './CountText';

export interface BallotRowProps {
  /** The server's candidates: seats, and `abstain` if it is allowed. */
  candidates: readonly string[];
  cast: readonly Character[];
  /** The chip (or `abstain`) chosen so far, or null. */
  chosen: string | null;
  onChoose?: (c: string | null) => void;
  onConfirm?: () => void;
  /** Sent: the row gives way to "Your ballot is in". */
  sent?: boolean;
  /** This seat, for the "in" line's chip. */
  me: string;
  /** The turn's clock, or null for no deadline. */
  clock?: TurnClock | null;
  arrive?: boolean;
}

const plateLabel = (c: string | null) =>
  c === null ? 'Choose a seat' : c === 'abstain' ? 'Abstain' : `Vote seat ${seatNumber(c)}`;

export function BallotRow({
  candidates,
  cast,
  chosen,
  onChoose,
  onConfirm,
  sent = false,
  me,
  clock,
  arrive = false,
}: BallotRowProps) {
  const k = useMotionScale();
  const fade = {
    initial: arrive ? { opacity: 0 } : false,
    animate: { opacity: 1 },
    transition: { duration: 0.4 * k, delay: 0.3 * k },
  } as const;
  const head = (c: string) => (
    <span className={styles.head}>
      <ChipSprite character={cast[seatNumber(c) - 1]} />
    </span>
  );

  if (sent) {
    return (
      <motion.div className={`${styles.box} ${styles.in}`} {...fade} data-ballot="in">
        <header>
          <strong>Your ballot is in</strong>
          <span>no one sees it until voting closes</span>
        </header>
        <div className={styles.line}>
          {head(me)}
          <span className={styles.arr}>→</span>
          {chosen && chosen !== 'abstain' ? (
            <>
              {head(chosen)}
              <span>Seat {seatNumber(chosen)}</span>
            </>
          ) : (
            <span>Abstain</span>
          )}
        </div>
      </motion.div>
    );
  }

  const seats = candidates.filter((c) => c !== 'abstain');
  const canAbstain = candidates.includes('abstain');
  const cls = (c: string) =>
    [styles.vchip, chosen === c ? styles.on : chosen ? styles.off : '']
      .filter(Boolean)
      .join(' ');
  return (
    <motion.div className={styles.box} {...fade} data-ballot="open">
      <header>
        <strong>Your vote</strong>
        <span>Tap a chip{canAbstain ? ', or the empty plate to abstain' : ''}.</span>
        {clock ? (
          <span className={styles.count}>
            your seat’s agent votes for you in <CountText clock={clock} />
          </span>
        ) : null}
      </header>
      <div className={styles.row} role="radiogroup" aria-label="Your vote">
        {seats.map((c) => (
          <button
            key={c}
            type="button"
            role="radio"
            aria-checked={chosen === c}
            className={cls(c)}
            onClick={() => onChoose?.(chosen === c ? null : c)}
            data-seat={seatNumber(c)}
          >
            {head(c)}
            <b>{seatNumber(c)}</b>
          </button>
        ))}
        {canAbstain ? (
          <button
            type="button"
            role="radio"
            aria-checked={chosen === 'abstain'}
            className={cls('abstain')}
            onClick={() => onChoose?.(chosen === 'abstain' ? null : 'abstain')}
          >
            <span className={styles.dish} />
            <b>abstain</b>
          </button>
        ) : null}
      </div>
      <div className={styles.plate}>
        <button
          type="button"
          disabled={!chosen}
          onClick={onConfirm}
          data-plate={plateLabel(chosen)}
        >
          {plateLabel(chosen)}
        </button>
      </div>
    </motion.div>
  );
}

/**
 * One ballot as the count reads it out, in the box at the foot: the voter's chip, "votes", the
 * seat it voted for (or "abstains"). Public by then: the count is the moment ballots are named.
 */
export function BallotLine({
  voter,
  votee,
  cast,
  arrive = false,
}: {
  voter: string;
  votee: string;
  cast: readonly Character[];
  arrive?: boolean;
}) {
  const k = useMotionScale();
  const head = (c: string) => (
    <span className={styles.head}>
      <ChipSprite character={cast[seatNumber(c) - 1]} />
    </span>
  );
  return (
    <motion.div
      className={`${styles.box} ${styles.big}`}
      initial={arrive ? { opacity: 0 } : false}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 * k, delay: 0.7 * k }}
      data-ballot-line=""
    >
      <div className={styles.line}>
        {head(voter)}
        <span>Seat {seatNumber(voter)}</span>
        <span className={styles.arr}>{votee === 'abstain' ? 'abstains' : 'votes'}</span>
        {votee === 'abstain' ? null : (
          <>
            {head(votee)}
            <span>Seat {seatNumber(votee)}</span>
          </>
        )}
      </div>
    </motion.div>
  );
}

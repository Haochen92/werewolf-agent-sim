'use client';

/**
 * The read card: what the seat at the stand made of one other seat when it spoke, opened by
 * tapping that seat's tile on the wing (handoff §2 "The film"). The reads sit on the wing as
 * verdigris edges, and this card is the one close look at one of them: the guess, how sure,
 * why, and, since the X-ray holds the truth, how near it came: ● the role itself, ◐ the right
 * side, ○ no read or wrong. A small paper index card in the case file's style (owner,
 * 2026-09-29): it is a leaf of the speaker's file (its Reads), upright.
 *
 * It sits beside its seat, docked at the wing's edge. Tapping the seat again closes it. Its head
 * says whose read on whom, face by face: "[speaker] Seat 2's read on [target] Seat 5" (owner,
 * 2026-09-29: "Seat 5 the speaker's read" read both ways).
 */
import type { CSSProperties } from 'react';
import type { Character } from '@/assets/manifest';
import { ChipSprite } from '../cast/ChipSprite';
import { Sigil } from '../instruments/Sigil';
import { ROLE_NAME, factionOf, seatNumber, seatify } from '../roles';
import { MARK, readMark, type SeatRead } from './film-model';
import styles from './ReadCard.module.css';

export function ReadCard({
  seat,
  character,
  speaker,
  speakerCharacter,
  read,
  truth,
  left,
  top,
}: {
  /** The seat the read is on (the tapped tile), and who plays it. */
  seat: string;
  character: Character | undefined;
  /** The seat at the stand, whose read it is. */
  speaker: string;
  speakerCharacter: Character | undefined;
  read: SeatRead;
  /** The seat's real role, which the X-ray holds; null if this viewer does not. */
  truth: string | null;
  /**
   * Where the card docks, in units: the wing's edge, level with the seat. The stylesheet keeps
   * it on the stage at the bottom seats, at its height as drawn (which grows on a phone).
   */
  left: number;
  top: number;
}) {
  const guess = read.suspected_role;
  const sure = read.confidence === 'high';
  const f = factionOf(truth);
  return (
    <div
      className={styles.card}
      style={{ left, '--top': `${top}px` } as CSSProperties}
      data-read-card={seat}
      role="dialog"
      aria-label={`Seat ${seatNumber(speaker)}'s read on seat ${seatNumber(seat)}`}
    >
      <header>
        <span className={styles.chip}>
          {speakerCharacter ? <ChipSprite character={speakerCharacter} /> : null}
        </span>
        <span>Seat {seatNumber(speaker)}’s read on</span>
        <span className={styles.chip}>
          {character ? <ChipSprite character={character} /> : null}
        </span>
        <strong>Seat {seatNumber(seat)}</strong>
      </header>
      <div className={styles.guess}>
        <b className={sure ? styles.sure : undefined}>
          {guess === 'unclear' ? 'unclear' : (ROLE_NAME[guess] ?? guess).toLowerCase()}
        </b>
        <span>{sure ? 'sure' : 'not sure'}</span>
      </div>
      <p>{seatify(read.why)}</p>
      {truth ? (
        <footer>
          Truth:
          <span className={`${styles.truth} ${f ? styles[`c-${f}`] : ''}`}>
            <Sigil role={truth} small />
            {(ROLE_NAME[truth] ?? truth).toLowerCase()}
          </span>
          <span
            className={`${styles.mk} ${styles[`m-${readMark(guess, truth)}`] ?? ''}`}
            title={readMark(guess, truth)}
          >
            {MARK[readMark(guess, truth)]}
          </span>
        </footer>
      ) : null}
    </div>
  );
}

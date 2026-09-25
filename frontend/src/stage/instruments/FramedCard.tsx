'use client';

/**
 * Your role card, standing in a brass-edged frame at the left end of the shelf, and the same
 * card opened full size over the room when you tap it. At night the card is the one reminder
 * of who you are and what your act does, so it stands where your eye starts: name, sigil,
 * the role's felt figure and the night line. Tapped open it reads in full (name, sigil, the
 * figure, the front line, what you do at night), and a tap anywhere closes it.
 *
 * The faction's colour is on the card because the card is face up: it is your own.
 */
import type { CSSProperties } from 'react';
import { CARD_TEXT } from '../card-text';
import { roleFigure } from '../paint/role-kit';
import { factionOf } from '../roles';
import { Sigil } from './Sigil';
import styles from './NightRoom.module.css';

export interface FramedCardProps {
  role: string;
  /** The frame's centre x and the shelf's top face it stands on, in units. */
  x: number;
  foot: number;
  /** The frame's height in units (bench 70: 0.31 of the stage's height). */
  height: number;
  /** One card unit, in stage units: the frame's type scales with it. */
  u: number;
  /** A lone wolf reads "You hunt alone now". */
  alone?: boolean;
  onOpen?: () => void;
}

export function FramedCard({ role, x, foot, height, u, alone, onOpen }: FramedCardProps) {
  const text = CARD_TEXT[role];
  if (!text) return null;
  const w = height * 0.72;
  const faction = factionOf(role) ?? 'villagers';
  return (
    <button
      type="button"
      className={`${styles.framed} ${styles[faction]}`}
      data-card={role}
      aria-label={`Your card: ${text.name}. Tap to read`}
      onClick={onOpen}
      style={
        {
          left: x - w / 2,
          top: foot - height,
          width: w,
          height,
          '--u': `${u}px`,
        } as CSSProperties
      }
    >
      <span className={styles.framedIn}>
        <span className={styles.framedHead}>
          <span>{text.name}</span>
          <Sigil role={role} />
        </span>
        <span
          className={styles.framedFig}
          dangerouslySetInnerHTML={{ __html: roleFigure(role) }}
        />
        <span className={styles.framedLine}>
          {alone && text.nightAlone ? text.nightAlone : text.night}
        </span>
      </span>
      <em>tap to read</em>
    </button>
  );
}

export interface CardOverlayProps {
  role: string;
  /** Your seat, for the card's foot. */
  seat: number;
  /** One card unit, in stage units (bench 70: 1.6 puppet units). */
  u: number;
  alone?: boolean;
  onClose?: () => void;
}

export function CardOverlay({ role, seat, u, alone, onClose }: CardOverlayProps) {
  const text = CARD_TEXT[role];
  if (!text) return null;
  const faction = factionOf(role) ?? 'villagers';
  return (
    <button
      type="button"
      className={styles.veil}
      aria-label="Close your card"
      onClick={onClose}
      data-overlay="card"
    >
      <span
        className={`${styles.card} ${styles[faction]}`}
        role="dialog"
        aria-label={text.name}
        style={{ '--u': `${u}px` } as CSSProperties}
      >
        <span className={styles.cardIn}>
          <span className={styles.cardHead}>
            <span>{text.name}</span>
            <Sigil role={role} />
          </span>
          <span
            className={styles.cardFig}
            dangerouslySetInnerHTML={{ __html: roleFigure(role) }}
          />
          <span className={styles.cardLine}>{text.line}</span>
          <span className={styles.cardNight}>
            <b>At night</b> {alone && text.nightAlone ? text.nightAlone : text.night}
          </span>
          <span className={styles.cardFoot}>Seat {seat} · tap anywhere to close</span>
        </span>
      </span>
    </button>
  );
}

'use client';

/**
 * Your role card, standing in a brass-edged frame on the table by the candle, and the same
 * card opened full size over the room when you tap it. At night the card is the one reminder
 * of who you are and what your act does, so it stands where your eye starts: name, sigil,
 * the role's felt figure and the night line. Tapped open it reads in full (name, sigil, the
 * figure, what you do at night); the front line is left to the deal and the lobby, since at night
 * the card is there for the act. A tap on the card closes it; a tap past it (`onOutside`) also
 * lets the room clear an unsent choice. The vigilante's caps left sit under the night line.
 *
 * The faction's colour is on the card because the card is face up: it is your own.
 */
import type { CSSProperties } from 'react';
import { CARD_TEXT } from '../card-text';
import { roleFigure } from '../paint/role-kit';
import { factionOf } from '../roles';
import { Sigil } from './Sigil';
import styles from './NightRoom.module.css';

/** The frame's outermost ring, drawn past its box (NightRoom.module.css `.framed`). */
const FRAME_RING = 9.6;

export interface FramedCardProps {
  role: string;
  /** The frame's centre x and the table's top it stands on, in units. */
  x: number;
  foot: number;
  /** The frame's height in units (on the night room's table, 200; bench 70's shelf had 0.31 of the stage). */
  height: number;
  /** One card unit, in stage units: the frame's type scales with it. */
  u: number;
  /** A lone wolf reads "You hunt alone now". */
  alone?: boolean;
  /** A quiet line under the night line (the vigilante's caps left). */
  note?: string;
  onOpen?: () => void;
}

export function FramedCard({
  role,
  x,
  foot,
  height,
  u,
  alone,
  note,
  onOpen,
}: FramedCardProps) {
  const text = CARD_TEXT[role];
  if (!text) return null;
  const w = height * 0.72;
  const faction = factionOf(role) ?? 'villagers';
  // the frame's outer ring (9.6 units past the box) is what stands on the table
  const top = foot - FRAME_RING - height;
  return (
    <>
      <div
        className={styles.contact}
        style={{ left: x - w * 0.55 + 7, top: foot - 8, width: w * 1.1, height: 16 }}
      />
      <button
        type="button"
        className={`${styles.framed} ${styles[faction]}`}
        data-card={role}
        aria-label={`Your card: ${text.name}. Tap to read`}
        onClick={onOpen}
        style={
          {
            left: x - w / 2,
            top,
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
          {note ? <span className={styles.framedCount}>{note}</span> : null}
        </span>
        <em>tap to read</em>
      </button>
    </>
  );
}

export interface CardOverlayProps {
  role: string;
  /** Your seat, for the card's foot. */
  seat: number;
  /** One card unit, in stage units (bench 70: 1.6 puppet units). */
  u: number;
  alone?: boolean;
  /** A quiet line under the night text (the vigilante's caps left). */
  note?: string;
  /** Any tap closes the card. */
  onClose?: () => void;
  /** A tap past the card, on the room behind it (before `onClose`). */
  onOutside?: () => void;
}

export function CardOverlay({
  role,
  seat,
  u,
  alone,
  note,
  onClose,
  onOutside,
}: CardOverlayProps) {
  const text = CARD_TEXT[role];
  if (!text) return null;
  const faction = factionOf(role) ?? 'villagers';
  return (
    <button
      type="button"
      className={styles.veil}
      aria-label="Close your card"
      onClick={(e) => {
        if (!(e.target as Element).closest('[role="dialog"]')) onOutside?.();
        onClose?.();
      }}
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
          <span className={styles.cardNight}>
            <b>At night</b> {alone && text.nightAlone ? text.nightAlone : text.night}
          </span>
          {note ? <span className={styles.cardCount}>{note}</span> : null}
          <span className={styles.cardFoot}>Seat {seat} · tap anywhere to close</span>
        </span>
      </span>
    </button>
  );
}

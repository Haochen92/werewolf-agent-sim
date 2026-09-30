'use client';

/**
 * The role cards: the paper card a role is dealt on, in three forms.
 *
 * - `CardBack`: face down. Paper, the stitched ring and the star, and no faction colour
 *   anywhere, not even the edge bands (the card-back rule: a face-down card tells nobody
 *   anything).
 * - `SmallCard`: the one hung under each chip at the deal. Face up it is the role's name over
 *   its felt figure, the big card's art (owner, 2026-09-30; it was the sigil alone), the sigil
 *   small by the seat at its foot.
 * - `RoleCard`: the full face, shown large (your card at the deal, a dead seat's at the
 *   morning, the lynch's on the lift): name and sigil, the felt figure, the front line, the
 *   seat, and the faction's colour on the edge bands.
 *
 * A card fills the box it is put in (a `StringDrop`, usually) and sizes its print from `w`,
 * its width in units, so a card reads the same small or large. `turn` plays it over from its
 * back to its face.
 */
import type { CSSProperties } from 'react';
import { factionOf } from '../roles';
import { CARD_TEXT } from '../card-text';
import { roleFigure } from '../paint/role-kit';
import { BackArt } from './CardBackArt';
import { Flip } from './Flip';
import { Sigil } from './Sigil';
import styles from './Card.module.css';

const cardVars = (w: number) => ({ '--u': `${w / 340}px` }) as CSSProperties;

export function CardBack({ w, big }: { w: number; big?: boolean }) {
  return (
    <div className={big ? `${styles.card} ${styles.big}` : styles.card} style={cardVars(w)}>
      <div className={styles.back}>
        <BackArt />
      </div>
    </div>
  );
}

interface FaceProps {
  /** The role on the face, or null for a card this viewer may only see the back of. */
  role: string | null;
  seat: number;
  /** The card's width in units: its print scales from it. */
  w: number;
  /** Play the turn from the back to the face. */
  turn?: boolean;
  turnDelay?: number;
}

const faceClass = (role: string, ...more: string[]) => {
  const f = factionOf(role);
  return [styles.card, f ? styles[`f-${f}`] : '', ...more].filter(Boolean).join(' ');
};

export function SmallCard({ role, seat, w, turn = false, turnDelay }: FaceProps) {
  if (!role) return <CardBack w={w} />;
  const face = (
    <div className={faceClass(role, styles.small)} style={cardVars(w)}>
      <div className={styles.in}>
        <header>
          <span>{CARD_TEXT[role]?.name ?? role}</span>
        </header>
        <div
          className={styles.fig}
          dangerouslySetInnerHTML={{ __html: roleFigure(role) }}
        />
        <footer>
          <Sigil role={role} className={styles.sg} />
          Seat {seat}
        </footer>
      </div>
    </div>
  );
  return <Flip back={<CardBack w={w} />} face={face} turn={turn} delay={turnDelay} />;
}

export function RoleCard({ role, seat, w, turn = false, turnDelay }: FaceProps) {
  if (!role) return <CardBack w={w} big />;
  const text = CARD_TEXT[role];
  const face = (
    <div className={faceClass(role, styles.big)} style={cardVars(w)}>
      <div className={styles.in}>
        <header>
          <span>{text?.name ?? role}</span>
          <Sigil role={role} className={styles.sg} />
        </header>
        <div
          className={styles.fig}
          dangerouslySetInnerHTML={{ __html: roleFigure(role) }}
        />
        <p className={styles.line}>
          {text?.line.split('\n').map((l, i) => (
            <span key={i}>
              {i ? <br /> : null}
              {l}
            </span>
          ))}
        </p>
        <footer>Seat {seat}</footer>
      </div>
    </div>
  );
  return <Flip back={<CardBack w={w} big />} face={face} turn={turn} delay={turnDelay} />;
}

/**
 * The stand: the puppet booth's front, below the rail, that the speaking puppet stands in.
 * A dark box with a rail cap, a recessed panel and two footlights, the plaque on its rail
 * naming the seat. It is drawn over the puppet's feet (the stand layer is above the figures),
 * which is what makes a glove puppet read as standing in a booth.
 *
 * The box is 605 puppet units wide, centred on the puppet (units.ts `standBox`). Ported from
 * the stage kit's `stand()` (kits/stage-kit.js), whose CSS came with it.
 */
import type { CSSProperties, ReactNode } from 'react';
import { standBox, type StageGeometry } from '../units';
import type { Faction } from '../roles';
import styles from './Stand.module.css';

export interface StandProps {
  g: StageGeometry;
  /** The footlights are on. */
  lit?: boolean;
  /** Width factor, for two or three figures at the end of the game. */
  widen?: number;
  /** The plaque (or nothing, for an empty stand). */
  children?: ReactNode;
}

export function Stand({ g, lit = true, widen = 1, children }: StandProps) {
  const box = standBox(g);
  const w = box.w * widen;
  return (
    <div className={styles.pit} style={{ top: g.railY }}>
      <div
        className={styles.box}
        style={{ left: g.cx - w / 2, width: w, '--u': `${g.u}px` } as CSSProperties}
      >
        {[-130, 90].map((dx) => (
          <i
            key={dx}
            className={lit ? `${styles.foot} ${styles.on}` : styles.foot}
            style={{ left: `calc(50% + ${dx * widen} * var(--u))` }}
          />
        ))}
        {children}
      </div>
    </div>
  );
}

export type PlaqueTone = Faction | 'agent';

export interface PlaqueProps {
  /** The seat numeral, 1–9; several for two or three at the stand ("Seats 3 and 8"). */
  seat: number | readonly number[];
  /** A short tag after the seat: the role (X-ray), "voted out", "your seat's agent". */
  tag?: string;
  /** The tag's colour: a faction, or the seat's own warnings. */
  tone?: PlaqueTone;
}

export function Plaque({ seat, tag, tone }: PlaqueProps) {
  const seats = typeof seat === 'number' ? [seat] : seat;
  const names =
    seats.length > 1
      ? `Seats ${seats.slice(0, -1).join(', ')} and ${seats[seats.length - 1]}`
      : `Seat ${seats[0]}`;
  return (
    <div className={styles.plaque}>
      {names}
      {tag ? (
        <span className={tone ? `${styles.tag} ${styles[`t-${tone}`]}` : styles.tag}>
          {tag}
        </span>
      ) : null}
    </div>
  );
}

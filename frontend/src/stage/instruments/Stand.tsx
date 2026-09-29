/**
 * The stand: the puppet booth's front, below the rail, that the speaking puppet stands in.
 * A painted walnut sideboard front (a brass gallery on its rounded rail, marquetry corners, a
 * flame-figured panel), two footlights, the brass plate on its rail naming the seat. It is drawn over the puppet's feet (the stand layer
 * is above the figures), which is what makes a glove puppet read as standing in a booth.
 *
 * The box is 605 puppet units wide, centred on the puppet (units.ts `standBox`); the picture
 * stretches to it as a 9-slice (Stand.module.css). Laid out after the stage kit's `stand()`
 * (kits/stage-kit.js).
 */
import type { CSSProperties, ReactNode } from 'react';
import { SPRITES } from '@/assets/manifest';
import { HUD_CHROME, STAGE_H, standBox, type StageGeometry } from '../units';
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
  /**
   * The speech box is at the foot, over the stand's front. On a phone, where its words grow and
   * it rises past the rail, the plate rises with it, to sit just above the box's nameplate.
   */
  speech?: boolean;
}

export function Stand({ g, lit = true, widen = 1, children, speech = false }: StandProps) {
  const box = standBox(g);
  const w = box.w * widen;
  // the room between the rail and the box's foot (SpeechBox's `bottom`), less a small gap
  const clear = STAGE_H - g.railY - HUD_CHROME.band[g.hud] - 19.2 - 8;
  return (
    <div className={styles.pit} style={{ top: g.railY }}>
      <div
        className={styles.box}
        data-speech-below={speech || undefined}
        style={
          {
            left: g.cx - w / 2,
            width: w,
            '--u': `${g.u}px`,
            '--front': `url(${SPRITES.props.stand.src})`,
            '--clear': `${clear}px`,
          } as CSSProperties
        }
      >
        {/* the rooms' key light: the box's shadow on the boards behind it and to its right */}
        <i className={styles.cast} aria-hidden="true" />
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
  // engraved on brass, as a railway carriage numbers its seats
  const names =
    seats.length > 1
      ? `Nos. ${seats.slice(0, -1).join(', ')} and ${seats[seats.length - 1]}`
      : `No. ${seats[0]}`;
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

/**
 * The strip along the top of the stage: where we are, on a small walnut-and-brass plaque (a
 * sun or a moon, "Day 3" engraved large, and under it the phase and the beat's name, so a
 * viewer arriving cold knows what they are looking at), and the side pane's two tabs, File and
 * Transcript, on one brass-edged plaque pinned at the right. Transcript is always the far right,
 * live and replay alike. The tabs only choose what the pane shows; File, the X-ray's own pane,
 * is greyed while the X-ray is off (owner, 2026-09-29).
 *
 * Just left of the tabs, on its own small plaque, the X-ray's one switch, which the viewer
 * knows as Reveal (owner, 2026-09-29; it was the band's "X-ray on/off"): a brass keyhole
 * that slides along a slot, "Reveal" off, "Revealed" on with the keyhole lit in verdigris. Live
 * it is locked until the game ends (the game's end is the switch), then shown on.
 *
 * The tabs only report what they are pressed to; the container decides what a press does.
 * The replay also has a way out, "← Replays" (or "← Home", whichever the viewer came from), on
 * its own small plaque just before the day's, there from the first frame: a phone on its side
 * has no browser bar to go back with (owner, 2026-09-29). A live game has none.
 */
import Link from 'next/link';
import type { ReactNode } from 'react';
import { geometry, type Hud } from '../units';
import styles from './TopStrip.module.css';

export interface TopStripProps {
  hud: Hud;
  /** The big line: "Day 3". */
  title: string;
  /** The small line under it: "Discussion · Speaks". */
  sub?: string;
  /** The disc on the plaque: the sun by day, the moon by night. Absent: read from the title. */
  disc?: 'sun' | 'moon';
  /** The X-ray is on: the File tab can be pressed. */
  xray: boolean;
  /** The film has the side slot: File reads as pressed. */
  file?: boolean;
  /** The drawer has the side slot: Transcript reads as pressed. */
  transcript?: boolean;
  /** Game over, live: the observer tier is everyone's now, and the File tab says so. */
  unlocked?: boolean;
  onFile?: () => void;
  onTranscript?: () => void;
  /** The replay's way out: where it goes and what it says. Drawn in the replay's frame only. */
  back?: { href: string; label: string };
  /**
   * The count pill ("Acted 2 of 5"), when the scene has one. It sits at the room's top centre;
   * in the replay, where the way out widens the plaques, it follows them in their row instead,
   * and wraps under them when the room is too narrow for all three.
   */
  count?: ReactNode;
  /** The side slot is open, so the room (and the replay's row) is narrower. */
  side?: boolean;
  /**
   * The Reveal switch: `on` is the X-ray; `onPress` flips it (the replay); `locked` draws it
   * disabled and unlit (live, before the game ends). Absent: no switch.
   */
  reveal?: { on: boolean; onPress?: () => void; locked?: boolean };
}

export function TopStrip({
  hud,
  title,
  sub,
  disc,
  xray,
  file = false,
  transcript = false,
  unlocked,
  onFile,
  onTranscript,
  back,
  count,
  side = false,
  reveal,
}: TopStripProps) {
  // no HUD (a preview, like the landing's): no strip, and no buttons that would go nowhere
  if (hud === 'none') return null;
  const g = geometry(hud, side);
  const out = !!back && hud === 'replay';
  // with the slot closed the room runs under the right's plaques: the row stops short of them
  // (they grow with the labels), and a count that does not fit wraps under the plaques
  const reserve = side ? 0 : reveal ? 380 : 220;
  return (
    <>
      <div
        className={styles.left}
        style={{
          left: g.wingN + 22.4,
          // the right's plaques stand out in the bleed on a wide screen: the row gains that much
          maxWidth: `calc(${g.room - 2 * 22.4}px - ${reserve}px * var(--legible-ui) + ${side ? '0px' : 'var(--slot-reach, 0px)'})`,
        }}
      >
        {out ? (
          <Link href={back.href} className={styles.back}>
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path
                d="M13 8H3.5M7.5 3.5 3 8l4.5 4.5"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.6}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            {back.label}
          </Link>
        ) : null}
        <div className={styles.phase}>
          <Disc kind={disc ?? (/^Night/.test(title) ? 'moon' : 'sun')} />
          <span className={styles.where}>
            <b>{title}</b>
            {sub ? <small>{sub}</small> : null}
          </span>
        </div>
        {out && count ? <div className={styles.count}>{count}</div> : null}
      </div>
      <div className={styles.dock}>
        {reveal ? <Reveal {...reveal} /> : null}
        <div className={styles.modes}>
          <button
            type="button"
            className={`${styles.btn} ${styles.xr}`}
            aria-pressed={file}
            disabled={!xray}
            title={xray ? undefined : 'The file opens with Reveal on'}
            onClick={onFile}
          >
            {unlocked && !file ? 'File · unlocked' : 'File'}
          </button>
          <button
            type="button"
            className={`${styles.btn} ${styles.tr}`}
            aria-pressed={transcript}
            onClick={onTranscript}
          >
            Transcript
          </button>
        </div>
      </div>
      {out ? null : count}
    </>
  );
}

/**
 * The Reveal switch: a brass escutcheon with a keyhole cut through it, riding a dark slot, and
 * the word. Off, it sits at the slot's left, the keyhole dark; on, it has slid right and the
 * keyhole glows verdigris. A switch, not a third tab: its own plaque, and it never reads as a
 * pane. Without `onPress` it cannot be pressed: locked (live, until the game ends), or on.
 */
function Reveal({ on, onPress, locked = false }: NonNullable<TopStripProps['reveal']>) {
  return (
    <button
      type="button"
      className={styles.reveal}
      aria-pressed={on}
      aria-label="Reveal"
      data-reveal={locked ? 'locked' : on ? 'on' : 'off'}
      disabled={!onPress}
      title={
        locked
          ? 'Revealed after the game'
          : !onPress
            ? 'Revealed: the game is over'
            : on
              ? 'Hide the roles and the thinking'
              : 'Reveal the roles and the thinking'
      }
      onClick={onPress}
    >
      <span className={styles.slot} aria-hidden="true">
        <span className={styles.knob}>
          <svg viewBox="0 0 16 16">
            <path
              className={styles.hole}
              d="M8 3.6a2.3 2.3 0 0 0-1.2 4.3L6 12.4h4l-.8-4.5A2.3 2.3 0 0 0 8 3.6Z"
            />
            {/* the light behind the keyhole: faded in, never a colour change */}
            <path
              className={styles.lit}
              d="M8 3.6a2.3 2.3 0 0 0-1.2 4.3L6 12.4h4l-.8-4.5A2.3 2.3 0 0 0 8 3.6Z"
            />
          </svg>
        </span>
      </span>
      <span className={styles.word}>{on && !locked ? 'Revealed' : 'Reveal'}</span>
    </button>
  );
}

/** The plaque's disc: a sun of eight rays, or a crescent moon, in brass line. */
function Disc({ kind }: { kind: 'sun' | 'moon' }) {
  return (
    <span className={styles.disc} data-disc={kind} aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6}>
        {kind === 'sun' ? (
          <>
            <circle cx={12} cy={12} r={3.6} />
            {[0, 45, 90, 135, 180, 225, 270, 315].map((a) => (
              <line
                key={a}
                x1={12}
                y1={5.4}
                x2={12}
                y2={3.4}
                strokeLinecap="round"
                transform={`rotate(${a} 12 12)`}
              />
            ))}
          </>
        ) : (
          <path
            d="M15.6 5.2a7 7 0 1 0 3.2 11.7A6 6 0 0 1 15.6 5.2Z"
            strokeLinejoin="round"
          />
        )}
      </svg>
    </span>
  );
}

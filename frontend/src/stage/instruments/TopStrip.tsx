/**
 * The strip along the top of the stage: where we are ("Day 3", and under it the phase and
 * the beat's name, so a viewer arriving cold knows what they are looking at), and the two
 * mode buttons, X-ray and Transcript, pinned at the right. Transcript is always the far right,
 * live and replay alike.
 *
 * The buttons only report what they are pressed to; the container decides what a press does.
 * The replay also has a way back to its list, a small link above the wing at the left (a
 * phone on its side has no browser bar to go back with); a live game has none.
 */
import Link from 'next/link';
import { geometry, type Hud } from '../units';
import styles from './TopStrip.module.css';

export interface TopStripProps {
  hud: Hud;
  /** The big line: "Day 3". */
  title: string;
  /** The small line under it: "Discussion · Speaks". */
  sub?: string;
  xray: boolean;
  /** The drawer has the side slot: Transcript reads as pressed. */
  transcript?: boolean;
  /** Game over, live: the observer tier is everyone's now, and the button says so. */
  unlocked?: boolean;
  onXray?: () => void;
  onTranscript?: () => void;
  /** The replay's list: where "Replays" goes. Drawn in the replay's frame only. */
  back?: string;
}

export function TopStrip({
  hud,
  title,
  sub,
  xray,
  transcript = false,
  unlocked,
  onXray,
  onTranscript,
  back,
}: TopStripProps) {
  const g = geometry(hud);
  return (
    <>
      {back && hud === 'replay' ? (
        <Link href={back} className={styles.back}>
          Replays
        </Link>
      ) : null}
      <div className={styles.phase} style={{ left: g.wingN + 22.4 }}>
        {title}
        {sub ? <small>{sub}</small> : null}
      </div>
      <div className={styles.modes}>
        <button
          type="button"
          className={`${styles.btn} ${styles.xr}`}
          aria-pressed={xray}
          onClick={onXray}
        >
          {unlocked && !xray ? 'X-ray · unlocked' : 'X-ray'}
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
    </>
  );
}

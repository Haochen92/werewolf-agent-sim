/**
 * The strip along the top of the stage: where we are, on a small walnut-and-brass plaque (a
 * sun or a moon, "Day 3" engraved large, and under it the phase and the beat's name, so a
 * viewer arriving cold knows what they are looking at), and the two mode buttons, X-ray and
 * Transcript, as two tabs of one brass-edged plaque pinned at the right. Transcript is always
 * the far right, live and replay alike.
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
  /** The disc on the plaque: the sun by day, the moon by night. Absent: read from the title. */
  disc?: 'sun' | 'moon';
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
  disc,
  xray,
  transcript = false,
  unlocked,
  onXray,
  onTranscript,
  back,
}: TopStripProps) {
  // no HUD (a preview, like the landing's): no strip, and no buttons that would go nowhere
  if (hud === 'none') return null;
  const g = geometry(hud);
  return (
    <>
      {back && hud === 'replay' ? (
        <Link href={back} className={styles.back}>
          Replays
        </Link>
      ) : null}
      <div className={styles.phase} style={{ left: g.wingN + 22.4 }}>
        <Disc kind={disc ?? (/^Night/.test(title) ? 'moon' : 'sun')} />
        <span className={styles.where}>
          <b>{title}</b>
          {sub ? <small>{sub}</small> : null}
        </span>
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

'use client';

/**
 * The speech box: what the seat at the stand says, in a dark glass box at the foot of the
 * stage, headed by the seat's chip and "Seat n". A pass is the same box saying "passes."; with
 * the X-ray on, a pass also says why, and what the agent held back, in the film's aqua.
 *
 * While the seat is still thinking the box holds a "…", so the thinking state reads as
 * thinking and not as an idle stand (ruled 2026-09-25).
 *
 * It sits in the HUD layer, over the stand, so the house lights never dim it. `arrive` fades
 * the line in once the puppet has taken the stand; at rest it is simply there.
 */
import { motion } from 'motion/react';
import type { CSSProperties } from 'react';
import type { Character } from '@/assets/manifest';
import { ChipSprite } from '../cast/ChipSprite';
import { useMotionScale } from '../motion';
import { seatify } from '../roles';
import { HUD_CHROME, STAGE_W, geometry, type Hud } from '../units';
import styles from './SpeechBox.module.css';

export interface SpeechBoxProps {
  hud: Hud;
  seat: number;
  character: Character;
  /** The line as the wire has it (seat names are rewritten for the table), or null for a pass. */
  line: string | null;
  /** A tag in the header: "you", or "your seat's agent spoke for you" (the seat's own screen). */
  tag?: { text: string; tone?: 'agent' };
  /** X-ray: why the seat passed, and the draft it held back. */
  xray?: { reason?: string | null; draft?: string | null };
  /** Fade the box in (a beat played forward); false = at rest. */
  arrive?: boolean;
  /** The seat is thinking: the box holds a "…" instead of the line. */
  thinking?: boolean;
  /**
   * The transcript drawer is open at full height: the box moves in under the puppet, narrower,
   * and a long line stops at three whole rows (an ellipsis, no fade), because the full line is
   * the drawer's newest entry.
   */
  side?: boolean;
  /**
   * The side slot holds something that stops at the rail (the film): on a phone, where the
   * words are larger and the box rises past the rail, it moves in under the puppet too (see
   * `--grown`), without the fade; at full size it keeps the band.
   */
  aside?: boolean;
}

const PASS_REASON: Record<string, string> = {
  voluntary: 'chose to pass',
  novelty_gated: 'held back: nothing new to say',
  generation_failed: 'no line came',
};

export function SpeechBox({
  hud,
  seat,
  character,
  line,
  tag,
  xray,
  arrive,
  thinking = false,
  side = false,
  aside = false,
}: SpeechBoxProps) {
  const k = useMotionScale();
  const g = geometry(hud, side);
  const inset = 22.4;
  const right = side ? STAGE_W - g.wingN - g.room + inset : inset;
  const s = geometry(hud, true);
  return (
    <div
      className={styles.zone}
      style={
        {
          left: g.wingN + inset,
          bottom: HUD_CHROME.band[hud] + 19.2,
          '--right': `${right}px`,
          '--aside': aside ? `${STAGE_W - s.wingN - s.room + inset}px` : undefined,
        } as CSSProperties
      }
    >
      {/* data-speech: the replay holds the beat while a pointer rests on the line */}
      <motion.div
        data-speech
        className={side ? `${styles.box} ${styles.faded}` : styles.box}
        initial={arrive ? { opacity: 0 } : false}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 * k }}
      >
        <header className={styles.head}>
          <span className={styles.chip}>
            <ChipSprite character={character} />
          </span>
          <strong>Seat {seat}</strong>
          {tag ? (
            <span
              className={tag.tone === 'agent' ? `${styles.tag} ${styles.agent}` : undefined}
            >
              {tag.text}
            </span>
          ) : null}
          {!thinking && xray?.reason ? (
            <span className={`${styles.tag} ${styles.xr}`}>
              {PASS_REASON[xray.reason] ?? xray.reason}
            </span>
          ) : null}
        </header>
        {thinking ? (
          <div className={styles.body} aria-label="thinking">
            …
          </div>
        ) : line === null ? (
          <div className={styles.body}>passes.</div>
        ) : (
          <div className={styles.body}>{seatify(line)}</div>
        )}
        {!thinking && line === null && xray?.draft ? (
          <div className={styles.draft}>“{seatify(xray.draft)}”</div>
        ) : null}
      </motion.div>
    </div>
  );
}

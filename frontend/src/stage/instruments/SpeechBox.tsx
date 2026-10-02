'use client';

/**
 * The speech box: what the seat at the stand says, on a walnut board edged in brass at the
 * foot of the stage, with a brass nameplate on its top-left corner (the seat's chip and
 * "Seat n"). A pass is the same board saying "passes."; with the X-ray on, a pass also says
 * why, and what the agent held back, in the X-ray's verdigris.
 *
 * The board is a fixed size: three lines (owner, 2026-09-29). A longer line is told a page at
 * a time, each page a beat of its own (beats/pages.ts); the board shows the beat's page and,
 * while more follows, "1 / 2 ▼" at its foot. A tap on the board moves on to the next page.
 * The transcript still holds the whole line.
 *
 * While the seat is still thinking the box holds a "…", so the thinking state reads as
 * thinking and not as an idle stand (ruled 2026-09-25).
 *
 * It sits in the HUD layer, over the stand, so the house lights never dim it. `arrive` fades
 * the line in once the puppet has taken the stand; at rest it is simply there.
 */
import { motion } from 'motion/react';
import type { CSSProperties } from 'react';
import { SPRITES, type Character } from '@/assets/manifest';
import { speechPages } from '../beats/pages';
import { ChipSprite } from '../cast/ChipSprite';
import { useMotionScale } from '../motion';
import { seatify } from '../roles';
import { bandFoot, STAGE_W, geometry, type Hud } from '../units';
import styles from './SpeechBox.module.css';

export interface SpeechBoxProps {
  hud: Hud;
  seat: number;
  character: Character;
  /** The line as the wire has it (seat names are rewritten for the table), or null for a pass. */
  line: string | null;
  /** Which of the line's pages the board shows (the beat's `page`); absent = the first. */
  page?: number;
  /** A tap on the board: this page is read, move on (the replay steps, live ends the hold). */
  onNext?: () => void;
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
   * with the same pages. At full size the room holds the measure and it keeps its three lines;
   * on a phone, where the words have grown past what the room holds, the board keeps its
   * height and sets the page in four slightly smaller lines (SpeechBox.module.css `.side`).
   * The film stops at the rail, over the board's top: the board keeps the band beside it.
   */
  side?: boolean;
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
  page = 0,
  onNext,
  tag,
  xray,
  arrive,
  thinking = false,
  side = false,
}: SpeechBoxProps) {
  const k = useMotionScale();
  const g = geometry(hud, side);
  const inset = 22.4;
  const right = side ? STAGE_W - g.wingN - g.room + inset : inset;
  const pages = line ? speechPages(line) : [];
  const at = Math.min(Math.max(0, page), Math.max(0, pages.length - 1));
  const more = at < pages.length - 1;
  return (
    <div
      className={styles.zone}
      style={
        {
          left: g.wingN + inset,
          bottom: bandFoot(hud, 19.2),
          '--left': `${g.wingN + inset}px`,
          '--right': `${right}px`,
        } as CSSProperties
      }
    >
      {/* data-speech: the replay holds the beat while a pointer rests on the line */}
      <motion.div
        data-speech
        data-page={pages.length > 1 ? `${at + 1}/${pages.length}` : undefined}
        className={[styles.box, side && styles.side, onNext && styles.tap]
          .filter(Boolean)
          .join(' ')}
        style={{ '--board': `url(${SPRITES.textures.walnut.src})` } as CSSProperties}
        initial={arrive ? { opacity: 0 } : false}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 * k }}
        onClick={onNext}
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
          <div className={styles.body}>
            {/* a new page fades in over the old: the board stays, the words turn */}
            <motion.span
              key={at}
              initial={arrive && at > 0 ? { opacity: 0 } : false}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 * k }}
            >
              {pages[at] ?? ''}
            </motion.span>
          </div>
        )}
        {!thinking && line === null && xray?.draft ? (
          <div className={styles.draft}>“{seatify(xray.draft)}”</div>
        ) : null}
        {!thinking && pages.length > 1 ? (
          <span className={styles.pager} aria-label={`page ${at + 1} of ${pages.length}`}>
            {at + 1} / {pages.length}
            {more ? <i aria-hidden="true">▼</i> : null}
          </span>
        ) : null}
      </motion.div>
    </div>
  );
}

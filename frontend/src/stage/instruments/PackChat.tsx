'use client';

/**
 * The wolves' chat: the pack's private talk at night, in the order it was said. Your
 * packmate is here, not on the shelf, so each of their lines carries their chip; your own
 * lines are warmer. The game master's note to the pack (the kill that failed) sits inside a
 * red tint, and the vote shows as plain lines: who voted for whom, then the kill decided.
 * The red edge says whose chat this is.
 *
 * The newest entry is always in view: the chat scrolls to its foot as lines arrive.
 *
 * When it is your turn to talk, a line and "Say it" sit at the foot of the room on the left;
 * the chat keeps the right.
 */
import { motion } from 'motion/react';
import { useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import type { Character } from '@/assets/manifest';
import { ChipSprite } from '../cast/ChipSprite';
import { useMotionScale } from '../motion';
import { seatify, seatNumber } from '../roles';
import styles from './PackChat.module.css';

export type PackEntry =
  | { kind: 'line'; seq: number; wolf: string; round: number; message: string }
  | { kind: 'gm'; seq: number; message: string }
  | { kind: 'vote'; seq: number; wolf: string; votee: string }
  | { kind: 'decided'; seq: number; target: string };

export interface PackChatProps {
  entries: readonly PackEntry[];
  /** Your seat. */
  you: string;
  /** Your packmate, or null when you hunt alone. */
  mate: string | null;
  /** Who plays which seat, for the chips; index 0 = player_1. */
  cast: readonly Character[];
  /** What the chat says while it is empty. */
  empty?: string;
  /** The header's words, in place of "Seat 3 and seat 8" (the replay reads it as nobody's). */
  heading?: string;
  /** A button at the header's right: the replay's "← Back to the night" from the pack's room. */
  action?: ReactNode;
  /** The entry that has just arrived (its seq): it fades in when `arrive` is set. */
  arriving?: number;
  arrive?: boolean;
  /** Your turn to talk: the draft line, and what "Say it" sends. */
  input?: {
    draft: string;
    onSay?: (text: string) => void;
    /** The room's left edge (past the wing), in units. */
    left: number;
    /** The small line under it. */
    note?: string;
  };
}

function Chip({ seat, cast }: { seat: string; cast: readonly Character[] }) {
  const c = cast[seatNumber(seat) - 1];
  return <span className={styles.chip}>{c ? <ChipSprite character={c} /> : null}</span>;
}

export function PackChat({
  entries,
  you,
  mate,
  cast,
  empty,
  heading,
  action,
  arriving,
  arrive,
  input,
}: PackChatProps) {
  const k = useMotionScale();
  const box = useRef<HTMLElement>(null);
  useLayoutEffect(() => {
    if (box.current) box.current.scrollTop = box.current.scrollHeight;
  }, [entries.length]);
  const row = (e: PackEntry): ReactNode => {
    switch (e.kind) {
      case 'line':
        return (
          <div className={e.wolf === you ? `${styles.msg} ${styles.me}` : styles.msg}>
            <Chip seat={e.wolf} cast={cast} />
            <div>
              <small>
                {e.wolf === you ? 'You' : `Seat ${seatNumber(e.wolf)}`} · round {e.round}
              </small>
              {seatify(e.message)}
            </div>
          </div>
        );
      case 'gm':
        return (
          <div className={`${styles.msg} ${styles.gm}`}>
            <div>
              <small>The game master</small>
              {seatify(e.message)}
            </div>
          </div>
        );
      case 'vote':
        return (
          <div className={styles.vline}>
            {e.wolf === you ? 'You vote' : `Seat ${seatNumber(e.wolf)} votes`}{' '}
            <Chip seat={e.votee} cast={cast} /> seat {seatNumber(e.votee)}
          </div>
        );
      case 'decided':
        return (
          <div className={`${styles.vline} ${styles.dec}`}>
            The pack chooses <Chip seat={e.target} cast={cast} /> seat{' '}
            {seatNumber(e.target)}
            {mate ? ' · both teeth' : ''}
          </div>
        );
    }
  };

  return (
    <>
      <section
        ref={box}
        className={styles.chat}
        aria-label="Wolf chat"
        data-chat="pack"
        data-speech
      >
        <header className={styles.head}>
          <span className={styles.tag}>Wolf chat</span>
          <span>
            {heading ??
              (mate
                ? `Seat ${seatNumber(you)} and seat ${seatNumber(mate)}`
                : 'You are the pack now')}
          </span>
          {action ? <span className={styles.action}>{action}</span> : null}
        </header>
        {entries.length === 0 && empty ? <div className={styles.empty}>{empty}</div> : null}
        {entries.map((e) => (
          <motion.div
            key={`${e.kind}:${e.seq}`}
            data-entry={e.kind}
            initial={arrive && e.seq === arriving ? { opacity: 0, y: 8 } : false}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 * k }}
          >
            {row(e)}
          </motion.div>
        ))}
      </section>
      {input ? <SayLine {...input} /> : null}
    </>
  );
}

function SayLine({ draft, onSay, left, note }: NonNullable<PackChatProps['input']>) {
  const [text, setText] = useState(draft);
  const [sent, setSent] = useState(false);
  return (
    <form
      className={styles.say}
      style={{ left }}
      onSubmit={(e) => {
        e.preventDefault();
        if (!text.trim() || sent) return;
        setSent(true);
        onSay?.(text.trim());
      }}
    >
      <input
        aria-label="Your line to the pack"
        placeholder="Say something to your packmate…"
        value={text}
        disabled={sent}
        onChange={(e) => setText(e.target.value)}
      />
      <button type="submit" disabled={sent || !text.trim()}>
        Say it
      </button>
      {note ? <span className={styles.count}>{note}</span> : null}
    </form>
  );
}

'use client';

/**
 * The seated human's speaking turn, in the box at the foot of the stage (bench 72, beat sheet
 * §2 row 4). Where the speech box would hold a seat's line, it holds a place to write one: the
 * countdown in red at its head, the box for the line, **Say it** and **Pass**.
 *
 * Beside them, the draft helper (ux_journeys D25): jot rough notes and the seat's own agent
 * phrases them into one line, which lands in the box to be sent, edited or dropped. Three
 * drafts a turn; the time spent waiting on one is given back to the clock. Nothing is sent
 * until Say it.
 *
 * It only draws what it is handed and reports the presses; the live theatre holds the words
 * and talks to the server. A line refused by the server says why, in the server's words.
 */
import { motion } from 'motion/react';
import type { KeyboardEvent } from 'react';
import { useMotionScale } from '../motion';
import type { DockInput } from '../scenes/types';
import styles from './TurnDock.module.css';

export interface TurnDockProps {
  dock: DockInput;
  /** The countdown's words ("1:52"), or null: no deadline (a solo game), no count. */
  left: string | null;
  onSay?: (text: string) => void;
  onPass?: () => void;
  /** Fade in (the turn arriving); false = at rest. */
  arrive?: boolean;
}

const drafts = (n: number) => (n === 1 ? '1 draft left' : `${n} drafts left`);

export function TurnDock({ dock, left, onSay, onPass, arrive = false }: TurnDockProps) {
  const k = useMotionScale();
  const busy = !!dock.sending || !!dock.closed;
  const line = dock.text.trim();
  const notes = dock.notes ?? '';
  const draftsLeft = dock.draftsLeft ?? 3;
  const say = () => {
    if (line && !busy) onSay?.(line);
  };
  // Ctrl/Cmd + Enter says it, as in any chat box; a plain Enter is a new line
  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      say();
    }
  };
  return (
    <motion.div
      className={styles.dock}
      data-dock="discuss"
      initial={arrive ? { opacity: 0 } : false}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 * k, delay: 0.3 * k }}
    >
      <header className={styles.head}>
        <strong>Your turn to speak</strong>
        <span>
          Say something to the table, or pass.
          {left ? ' If the clock runs out, your seat’s agent speaks for you.' : ''}
        </span>
        {left ? <span className={styles.count}>{left}</span> : null}
      </header>
      <textarea
        className={styles.line}
        aria-label="Your line"
        placeholder="Say something…"
        value={dock.text}
        onChange={(e) => dock.onText?.(e.target.value)}
        onKeyDown={onKey}
        readOnly={!dock.onText}
        disabled={busy}
        autoFocus
      />
      <div className={styles.row}>
        <button type="button" className={styles.pri} onClick={say} disabled={!line || busy}>
          {dock.sending ? 'Saying…' : 'Say it'}
        </button>
        <button type="button" onClick={onPass} disabled={busy}>
          Pass
        </button>
        {dock.onDraft ? (
          <span className={styles.notes}>
            <input
              aria-label="Notes for your agent"
              placeholder="Or jot notes (“8 dodging, why abstain?”)"
              maxLength={500}
              value={notes}
              onChange={(e) => dock.onNotes?.(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && notes.trim() && draftsLeft > 0 && !dock.drafting)
                  dock.onDraft?.(notes.trim());
              }}
              disabled={busy || !!dock.drafting}
            />
            <button
              type="button"
              onClick={() => dock.onDraft?.(notes.trim())}
              disabled={busy || !!dock.drafting || draftsLeft <= 0 || !notes.trim()}
              title="Your seat’s agent writes a line from your notes; you send it, edited or not"
            >
              {dock.drafting ? 'Drafting…' : 'Draft from notes'}
            </button>
            <span className={styles.left}>{drafts(draftsLeft)}</span>
          </span>
        ) : null}
        {dock.onDelegate ? (
          <button
            type="button"
            className={styles.agent}
            onClick={dock.onDelegate}
            disabled={busy}
          >
            Let my agent speak
          </button>
        ) : null}
      </div>
      {dock.error ? (
        <p className={styles.error} role="alert">
          {dock.error}
        </p>
      ) : null}
    </motion.div>
  );
}

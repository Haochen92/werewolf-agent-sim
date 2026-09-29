'use client';

/**
 * The seated human's speaking turn, in the box at the foot of the stage (bench 72, beat sheet
 * §2 row 4). Where the speech box would hold a seat's line, it holds a place to write one, on
 * the speech box's walnut board: the countdown in red at its head, then one flow, top to foot.
 *
 * 1. One button (ux_journeys D25) asks the seat's own agent for the line it would say:
 *    **Draft** while the reply box is empty, **Redraft** once it holds a line. An optional
 *    steer in the field beside it ("push on seat 5", "softer, ask seat 4 instead") goes along,
 *    and revises the line in the box. When the seat notebook holds anything, a "Use my seat
 *    notes" box (ticked to start) sends it along too. Three drafts a turn; the time spent
 *    waiting on one is given back to the clock.
 * 2. The reply box, where the draft lands to be read and edited, or where the player types
 *    their own line. **Send** says what is in it; **Pass** says nothing.
 *
 * Nothing is said until Send. If the clock runs out first, the seat's agent speaks on its own
 * (the live theatre sees to that; there is no hand-over button on this turn).
 *
 * It only draws what it is handed and reports the presses; the live theatre holds the words
 * and talks to the server. A line refused by the server says why, in the server's words.
 */
import { motion } from 'motion/react';
import type { CSSProperties, KeyboardEvent } from 'react';
import { SPRITES } from '@/assets/manifest';
import { useMotionScale } from '../motion';
import type { DockInput } from '../scenes/types';
import styles from './TurnDock.module.css';
import { dockControls, draftsLeftText } from './turn-dock';

export interface TurnDockProps {
  dock: DockInput;
  /** The countdown's words ("1:52"), or null: no deadline (a solo game), no count. */
  left: string | null;
  onSay?: (text: string) => void;
  onPass?: () => void;
  /** Fade in (the turn arriving); false = at rest. */
  arrive?: boolean;
}

export function TurnDock({ dock, left, onSay, onPass, arrive = false }: TurnDockProps) {
  const k = useMotionScale();
  const c = dockControls(dock);
  const say = () => {
    if (c.canSend) onSay?.(c.line);
  };
  const draft = () => {
    if (c.canDraft) dock.onDraft?.(c.notes, c.line);
  };
  // Ctrl/Cmd + Enter sends, as in any chat box; a plain Enter is a new line
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
      style={{ '--board': `url(${SPRITES.textures.walnut.src})` } as CSSProperties}
      initial={arrive ? { opacity: 0 } : false}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 * k, delay: 0.3 * k }}
    >
      <header className={styles.head}>
        <strong>Your turn to speak</strong>
        <span>
          Nothing is said until you send it.
          {left ? ' If the clock runs out, your agent speaks for you.' : ''}
        </span>
        {left ? <span className={styles.count}>{left}</span> : null}
      </header>
      {c.hasDraft ? (
        <div className={styles.agent}>
          <label htmlFor="dock-notes">Your agent</label>
          <input
            id="dock-notes"
            aria-label="Steer your agent"
            placeholder="Optional — steer or revise, e.g. push on seat 5 / softer, ask seat 4 instead"
            maxLength={500}
            value={dock.notes ?? ''}
            onChange={(e) => dock.onNotes?.(e.target.value)}
            // Enter drafts from what is written; an empty field drafts only from the button
            onKeyDown={(e) => {
              if (e.key === 'Enter' && c.notes) draft();
            }}
            disabled={c.busy || !!dock.drafting}
          />
          <button type="button" onClick={draft} disabled={!c.canDraft} title={c.draftHint}>
            {c.draftLabel}
          </button>
          <span className={styles.left}>{draftsLeftText(c.draftsLeft)}</span>
          {c.hasNotebook && dock.notebook ? (
            <label className={styles.share}>
              <input
                type="checkbox"
                checked={dock.notebook.shared}
                onChange={(e) => dock.notebook?.onShared(e.target.checked)}
                disabled={c.busy || !!dock.drafting}
              />
              Use my seat notes
            </label>
          ) : null}
        </div>
      ) : null}
      <div className={styles.reply}>
        <textarea
          className={styles.line}
          aria-label="Your line"
          placeholder={
            c.hasDraft ? 'Type your line, or draft one above…' : 'Type your line…'
          }
          value={dock.text}
          onChange={(e) => dock.onText?.(e.target.value)}
          onKeyDown={onKey}
          readOnly={!dock.onText}
          disabled={c.busy}
          autoFocus
        />
        <div className={styles.sends}>
          <button type="button" className={styles.pri} onClick={say} disabled={!c.canSend}>
            {dock.sending ? 'Sending…' : 'Send'}
          </button>
          <button type="button" onClick={onPass} disabled={c.busy}>
            Pass
          </button>
        </div>
      </div>
      {dock.error ? (
        <p className={styles.error} role="alert">
          {dock.error}
        </p>
      ) : null}
    </motion.div>
  );
}

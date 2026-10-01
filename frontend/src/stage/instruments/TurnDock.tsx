'use client';

/**
 * The seated human's speaking turn, in the box at the foot of the stage (bench 72, beat sheet
 * §2 row 4). Where the speech box would hold a seat's line, it holds the turn, on the speech
 * box's walnut board: "Your turn to speak", the hint and the countdown in red at its head, then
 * three plaques in a row and no boxes (owner, 2026-10-01; until then the dock held the steer,
 * Draft and the reply box itself):
 *
 * - **Write your line** (brass, the keyboard before its words) opens the full-screen composer,
 *   where all the writing is done. Once there is a line it reads **Edit your line**.
 * - **Send** (brass) says the line. Greyed until there is one, live the moment the composer's
 *   box holds a line, with the composer open or closed; it waits too while a line is over the cap.
 * - **Pass** (walnut) says nothing.
 *
 * Once there is a line, a row under the head previews it, on one line cut with "…", its word
 * count at the end ("23 words"); on a phone a tap on it opens the composer too. A line refused
 * by the server says why under it, in the server's words.
 *
 * The composer (beat sheet §12) holds the line in a box as big as the screen, over the whole
 * stage: the clock large; the steer, and one button (ux_journeys D25) asking the seat's own
 * agent for the line it would say, **Draft** while the box is empty, **Redraft this** once it
 * holds text (the steer revising that line), "n drafts left" (three a turn; the time spent
 * waiting on one is given back to the clock) and, when the seat notebook holds anything, "Use
 * my seat notes" (ticked to start); the box, "n words" and "612 / 700"; Pass, Send
 * (Ctrl/⌘+Enter) and Close (the X, Esc, a tap outside), which keeps the line. It is laid out in
 * css px, not stage units, and fitted to what the browser says is visible (`visualViewport`), so
 * on a phone with the soft keyboard up the box and Send stay in view. Whether it is open is kept
 * here, so it lasts across the scene's recuts within the turn; it shuts when the turn closes.
 *
 * Nothing is said until Send. If the clock runs out first, the seat's agent speaks on its own
 * (the live theatre sees to that; there is no hand-over button on this turn). The dock only
 * draws what it is handed and reports the presses; the live theatre holds the words and talks
 * to the server.
 */
import { AnimatePresence, motion } from 'motion/react';
import {
  useEffect,
  useId,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
} from 'react';
import { SPRITES } from '@/assets/manifest';
import { useMotionScale } from '../motion';
import type { DockInput } from '../scenes/types';
import { Overlay } from '../Stage';
import { PHONE_QUERY, composerBox, composerShown } from './composer';
import styles from './TurnDock.module.css';
import {
  DRAFT_WORDS,
  LINE_MAX,
  cycleDraftWords,
  dockControls,
  draftsLeftText,
  type DockControls,
} from './turn-dock';

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
  // the full-screen composer: open until closed, and never once the turn is
  const phone = usePhone();
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (dock.closed) setOpen(false);
  }, [dock.closed]);
  const expand = useRef<HTMLButtonElement>(null);
  const close = () => {
    setOpen(false);
    expand.current?.focus();
  };
  const board = { '--board': `url(${SPRITES.textures.walnut.src})` } as CSSProperties;
  return (
    <motion.div
      className={styles.dock}
      data-dock="discuss"
      style={board}
      initial={arrive ? { opacity: 0 } : false}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 * k, delay: 0.3 * k }}
    >
      <header className={`${styles.head} ${styles.top}`}>
        <strong>Your turn to speak</strong>
        <span className={styles.hint}>
          Nothing is said until you send it.
          {left ? ' If the clock runs out, your agent speaks for you.' : ''}
        </span>
        {left ? <span className={styles.count}>{left}</span> : null}
      </header>
      {c.preview ? (
        <div
          className={`${styles.preview} ${phone && !c.busy ? styles.tappable : ''}`}
          data-dock-preview
          // on a phone the preview is a way into the composer too (the plaque is the button)
          onClick={phone && !c.busy ? () => setOpen(true) : undefined}
        >
          <span className={styles.previewLine}>{c.preview}</span>
          <span className={styles.previewWords} data-preview-words>
            {c.words}
          </span>
          {c.over ? (
            <span className={`${styles.previewWords} ${styles.overCap}`}>{c.count}</span>
          ) : null}
        </div>
      ) : null}
      {dock.error ? (
        <p className={styles.error} role="alert">
          {dock.error}
        </p>
      ) : null}
      <div className={styles.plaques}>
        <button
          ref={expand}
          type="button"
          className={`${styles.pri} ${styles.plaque}`}
          title="Write your line in a full-screen box"
          aria-haspopup="dialog"
          aria-expanded={open}
          onClick={() => setOpen(true)}
          disabled={c.busy}
        >
          <KeyboardGlyph />
          {c.writeLabel}
        </button>
        <button type="button" className={styles.pri} onClick={say} disabled={!c.canSend}>
          {dock.sending ? 'Sending…' : 'Send'}
        </button>
        <button type="button" onClick={onPass} disabled={c.busy}>
          Pass
        </button>
      </div>
      {composerShown(open, dock) ? (
        <Overlay>
          <Composer
            dock={dock}
            c={c}
            left={left}
            board={board}
            say={say}
            draft={draft}
            onPass={onPass}
            onClose={close}
          />
        </Overlay>
      ) : null}
    </motion.div>
  );
}

/**
 * The instructions to the seat's agent, in the composer: a brass label, the steer, Draft (or
 * Redraft this, or the turning words while one is on its way), how many drafts are left, and
 * "Use my seat notes".
 */
function AgentRow({
  id,
  dock,
  c,
  draft,
}: {
  id: string;
  dock: DockInput;
  c: DockControls;
  draft: () => void;
}) {
  return (
    <div className={styles.agent}>
      <label htmlFor={id}>Your agent</label>
      <input
        id={id}
        aria-label="Steer your agent"
        placeholder="Optional. Leave empty for your agent's own line, or steer it: push on seat 5, softer, ask seat 4 instead."
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
        {dock.drafting ? <DraftWords /> : c.draftLabel}
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
  );
}

/**
 * The full-screen composer: the dock's line in a box as big as the screen (see the head of this
 * file). A dialog over the stage, in css px, sized to the visible part of the page.
 */
function Composer({
  dock,
  c,
  left,
  board,
  say,
  draft,
  onPass,
  onClose,
}: {
  dock: DockInput;
  c: DockControls;
  left: string | null;
  board: CSSProperties;
  say: () => void;
  draft: () => void;
  onPass?: () => void;
  onClose: () => void;
}) {
  const id = useId();
  const area = useVisibleArea();
  const line = useRef<HTMLTextAreaElement>(null);
  // opened, the writing goes on where it was: the caret at the end of the line
  useEffect(() => {
    const el = line.current;
    if (!el) return;
    el.focus();
    el.setSelectionRange(el.value.length, el.value.length);
  }, []);
  // Esc closes it wherever the focus is (a pressed Draft is disabled while it works, and the
  // focus falls back to the page)
  const shut = useRef(onClose);
  shut.current = onClose;
  useEffect(() => {
    const esc = (e: globalThis.KeyboardEvent) => {
      if (e.key === 'Escape') shut.current();
    };
    window.addEventListener('keydown', esc);
    return () => window.removeEventListener('keydown', esc);
  }, []);
  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      say();
    }
  };
  return (
    <div
      className={styles.composer}
      style={area ?? undefined}
      role="dialog"
      aria-modal="true"
      aria-label="Your line, full screen"
      data-composer
      // a tap on the dark around the sheet closes it too (the line stays)
      onPointerDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className={`${styles.dock} ${styles.sheet}`} style={board}>
        <header className={styles.head}>
          <strong>Your turn to speak</strong>
          <span className={styles.hint}>
            Nothing is said until you send it.
            {left ? ' If the clock runs out, your agent speaks for you.' : ''}
          </span>
          {left ? (
            <span className={styles.clock} data-composer-clock>
              {left}
            </span>
          ) : null}
          <button
            type="button"
            className={styles.close}
            aria-label="Close"
            title="Close (Esc). The line stays in the box."
            onClick={onClose}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M6 6 L18 18 M18 6 L6 18" />
            </svg>
          </button>
        </header>
        {c.hasDraft ? (
          <AgentRow id={`${id}-notes`} dock={dock} c={c} draft={draft} />
        ) : null}
        <textarea
          ref={line}
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
          maxLength={LINE_MAX}
        />
        <footer className={styles.foot}>
          <span className={styles.wordCount} data-word-count>
            {c.words}
          </span>
          {c.count ? (
            <span
              className={`${styles.lineCount} ${c.over ? styles.overCap : ''}`}
              data-line-count
              aria-live="polite"
            >
              {c.count}
            </span>
          ) : null}
          <div className={styles.said}>
            {dock.error ? (
              <p className={styles.error} role="alert">
                {dock.error}
              </p>
            ) : null}
          </div>
          <button type="button" onClick={onPass} disabled={c.busy}>
            Pass
          </button>
          <button type="button" className={styles.pri} onClick={say} disabled={!c.canSend}>
            {dock.sending ? 'Sending…' : 'Send'}
          </button>
        </footer>
      </div>
    </div>
  );
}

/** A frame 900 css px wide or narrower, as the browser says now. */
function usePhone(): boolean {
  const [phone, setPhone] = useState(
    () => typeof window !== 'undefined' && !!window.matchMedia?.(PHONE_QUERY).matches,
  );
  useEffect(() => {
    const mq = window.matchMedia?.(PHONE_QUERY);
    if (!mq) return;
    const on = () => setPhone(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return phone;
}

/** The visible part of the page, followed as a soft keyboard comes and goes (`composerBox`). */
function useVisibleArea() {
  const [box, setBox] = useState(() =>
    composerBox(typeof window !== 'undefined' ? window.visualViewport : null),
  );
  useEffect(() => {
    const vv = window.visualViewport;
    if (!vv) return;
    const on = () => setBox(composerBox(vv));
    on();
    vv.addEventListener('resize', on);
    vv.addEventListener('scroll', on);
    return () => {
      vv.removeEventListener('resize', on);
      vv.removeEventListener('scroll', on);
    };
  }, []);
  return box;
}

/** The keyboard on the dock's plaque to the composer, before its words. */
function KeyboardGlyph() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="2.5" y="6" width="19" height="12" rx="2" />
      <path d="M6.5 10h.01M9.5 10h.01M12.5 10h.01M15.5 10h.01M18 10h.01M6.5 14h.01M17.5 14h.01M9.5 14h5" />
    </svg>
  );
}

/**
 * The Draft button's words while a draft is on its way: "Drafting…", then every 1.6 s the next
 * of `DRAFT_WORDS`, each crossfading into the next (opacity only). The button keeps the width of
 * the longest, so nothing beside it moves; its name stays "Drafting…".
 */
function DraftWords() {
  const k = useMotionScale();
  const [i, setI] = useState(0);
  useEffect(() => cycleDraftWords(setI), []);
  return (
    <span className={styles.words}>
      <span className={styles.srOnly}>{DRAFT_WORDS[0]}</span>
      {DRAFT_WORDS.map((w) => (
        <span key={w} className={styles.sizer} aria-hidden="true">
          {w}
        </span>
      ))}
      <AnimatePresence initial={false}>
        <motion.span
          key={i}
          className={styles.word}
          aria-hidden="true"
          data-draft-word={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.45 * k }}
        >
          {DRAFT_WORDS[i]}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}

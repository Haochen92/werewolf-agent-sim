'use client';

/**
 * Borrowing your agent, working, in the guide: the live game's own composer (`TurnDock`,
 * pinned open in the page). Draft answers with sample lines (`sampleDraft`), after the wait a
 * real draft takes; no model is called and nothing is sent, and the demo says so once a sample
 * is in the box. "Use my seat notes" reads the
 * notebook the seat-card demo above writes, so a note written there steers the draft here. Send
 * shows the line as said and starts a new turn, three drafts again.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { stageFonts } from '@/stage/fonts';
import { TurnDock } from '@/stage/instruments/TurnDock';
import { DRAFT_WORD_MS } from '@/stage/instruments/turn-dock';
import { notebookForAgent, useNotebook } from '@/stage/notebook';
import { vars } from '@/stage/paint/materials';
import type { DockInput } from '@/stage/scenes/types';
import { sampleDraft } from './sample-drafts';
import classes from './Guide.module.css';

const MATERIALS = vars();
const DRAFTS = 3;

export function ComposerDemo() {
  const book = useNotebook('guide');
  const holds = !!notebookForAgent(book);
  const [text, setText] = useState('');
  const [steer, setSteer] = useState('');
  const [left, setLeft] = useState(DRAFTS);
  const [drafting, setDrafting] = useState(false);
  const [share, setShare] = useState(true);
  // the last turn's answer: the line said, '' for a pass, null before any
  const [said, setSaid] = useState<string | null>(null);
  // a sample is in the box: say so, then, and not before
  const [sampled, setSampled] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  useEffect(() => () => window.clearTimeout(timer.current), []);

  const dock: DockInput = useMemo(
    () => ({
      text,
      onText: setText,
      notes: steer,
      onNotes: setSteer,
      onDraft: (notes, current) => {
        setDrafting(true);
        // about the wait a real draft takes, so the turning words have their moment
        timer.current = window.setTimeout(() => {
          setText(
            sampleDraft({
              steer: notes,
              current,
              book: share && book ? book : null,
              taken: DRAFTS - left,
            }),
          );
          setLeft((n) => n - 1);
          setDrafting(false);
          setSampled(true);
        }, DRAFT_WORD_MS * 1.5);
      },
      notebook: holds ? { shared: share, onShared: setShare } : undefined,
      draftsLeft: left,
      drafting,
    }),
    [text, steer, left, drafting, share, holds, book],
  );
  const next = (line: string) => {
    setSaid(line);
    setSampled(false);
    setText('');
    setSteer('');
    setLeft(DRAFTS);
  };

  return (
    <div className={`${classes.composerDemo} ${stageFonts}`} style={MATERIALS}>
      <TurnDock dock={dock} clock={null} onSay={next} onPass={() => next('')} pinned />
      <p className={classes.said} aria-live="polite">
        {sampled
          ? 'A sample line: in a game, your agent writes it.'
          : said === null
            ? null
            : said
              ? `Seat 4 said: “${said}”`
              : 'Seat 4 passed.'}
      </p>
    </div>
  );
}

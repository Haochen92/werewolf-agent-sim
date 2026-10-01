/**
 * What the speaking turn's dock and its composer allow at a given moment, worked out from what
 * they are handed, so the rules can be tested without drawing them. The dock (2026-10-01) is
 * three plaques, "Write your line" (or "Edit your line" once there is one), Send and Pass, with
 * the line previewed on one row above them; the writing is all in the composer. There one
 * button asks the seat's own agent for its line: "Draft" while the box is empty, "Redraft this"
 * once it holds one. The optional steer goes with it (and revises the line in the box). Either
 * way the draft only lands in the box, and nothing is said until Send.
 */
import type { DraftRequest } from '@/types/contracts';
import type { DockInput } from '../scenes/types';
import { wordCount, wordsText } from './composer';

/** The server's cap on drafts per turn (ux_journeys D25), when the dock is not told. */
const DRAFTS_PER_TURN = 3;

/**
 * The longest line the box takes, the server's cap too (owner, 2026-09-30: the agents are asked
 * to keep under about 120 words, and a player's line may run a little longer).
 */
export const LINE_MAX = 700;

/** The box's count, "612 / 700", once the line is within 100 of the cap; null before then. */
export function lineCount(text: string): string | null {
  return text.length >= LINE_MAX - 100 ? `${text.length} / ${LINE_MAX}` : null;
}

/**
 * The longest the dock's preview of the line runs before it is cut with "…" (the row's own
 * width cuts it sooner, with the browser's ellipsis).
 */
export const PREVIEW_MAX = 120;

/**
 * The line as the dock's preview row shows it: on one line (its breaks and runs of space made
 * one space), cut at the last word before `max` with "…"; null when there is no line.
 */
export function previewText(text: string, max = PREVIEW_MAX): string | null {
  const one = text.replace(/\s+/g, ' ').trim();
  if (!one) return null;
  if (one.length <= max) return one;
  const cut = one.slice(0, max);
  const space = cut.lastIndexOf(' ');
  // a word longer than most of the cut is cut through
  return `${(space > max / 2 ? cut.slice(0, space) : cut).trimEnd()}…`;
}

export const draftsLeftText = (n: number) =>
  n === 1 ? '1 draft left' : `${n} drafts left`;

/**
 * What the Draft button says while a draft is on its way, one after another, round and round
 * (owner, 2026-09-30), so a wait of several seconds reads as work being done.
 */
export const DRAFT_WORDS = [
  'Drafting…',
  'Weighing the table…',
  'Finding the words…',
  'Reading the room…',
] as const;
export const DRAFT_WORD_MS = 1600;

/**
 * Steps through `DRAFT_WORDS` from the first (shown at the start, so not called for), handing
 * `on` the next one's index every `every` ms; returns the stop.
 */
export function cycleDraftWords(
  on: (i: number) => void,
  every = DRAFT_WORD_MS,
): () => void {
  let i = 0;
  const t = setInterval(() => {
    i = (i + 1) % DRAFT_WORDS.length;
    on(i);
  }, every);
  return () => clearInterval(t);
}

export interface DockControls {
  /** The line is on its way, or the turn is over: nothing can be pressed. */
  busy: boolean;
  /** The line in the box, trimmed: what Send sends. */
  line: string;
  /** The dock's preview of the line, on one line and cut with "…"; null: no line, no row. */
  preview: string | null;
  /** The line's word count at the preview's end, "23 words". */
  words: string;
  /** The brass plaque to the composer: "Write your line", "Edit your line" once there is one. */
  writeLabel: string;
  /** The steer for the agent, trimmed; empty = the agent writes its own line. */
  notes: string;
  canSend: boolean;
  /** The turn has a draft helper at all. */
  hasDraft: boolean;
  canDraft: boolean;
  draftsLeft: number;
  /** The Draft button's words: "Draft" for an empty box, "Redraft this" once it holds a line. */
  draftLabel: string;
  /** What the Draft button will do, for its tooltip. */
  draftHint: string;
  /** "Use my seat notes" is shown: the notebook has something to give. */
  hasNotebook: boolean;
  /** The box's count near the cap ("612 / 700"), or null; `over`: past it, and Send waits. */
  count: string | null;
  over: boolean;
}

export function dockControls(dock: DockInput): DockControls {
  const busy = !!dock.sending || !!dock.closed;
  const line = dock.text.trim();
  const notes = (dock.notes ?? '').trim();
  const draftsLeft = dock.draftsLeft ?? DRAFTS_PER_TURN;
  const hasDraft = !!dock.onDraft;
  // the box stops typing at the cap, but a draft or a paste set from outside may still run past it
  const over = dock.text.length > LINE_MAX;
  return {
    busy,
    line,
    preview: previewText(dock.text),
    words: wordsText(wordCount(dock.text)),
    writeLabel: line ? 'Edit your line' : 'Write your line',
    notes,
    // Send is live the moment there is a line, wherever it was written (the composer open or not)
    canSend: !!line && !busy && !over,
    hasDraft,
    canDraft: hasDraft && !busy && !dock.drafting && draftsLeft > 0,
    draftsLeft,
    draftLabel: dock.drafting ? 'Drafting…' : line ? 'Redraft this' : 'Draft',
    draftHint:
      (notes && line
        ? 'Your agent revises the line in the box as you asked.'
        : notes
          ? 'Your agent writes its line, steered by what you told it.'
          : 'Your agent writes the line it would say.') +
      ' It lands in the box: edit it, then Send.',
    hasNotebook: hasDraft && !!dock.notebook,
    count: lineCount(dock.text),
    over,
  };
}

/**
 * What one Draft press sends: the steer and the line in the box, and the seat notebook (from
 * `notebookForAgent`) only while "Use my seat notes" is ticked. Unticked, nothing of it goes.
 */
export function draftRequest(
  notes: string,
  current: string,
  notebook: Pick<DraftRequest, 'seat_notes' | 'suspect'> | null,
  share: boolean,
): DraftRequest {
  return {
    notes: notes.trim(),
    current: current.trim(),
    ...(share && notebook ? notebook : {}),
  };
}

/**
 * What the speaking turn's dock allows at a given moment, worked out from what it is handed,
 * so the rules can be tested without drawing it. One Draft button: with instructions in the
 * field the seat's agent drafts from them; with the field empty it drafts a line of its own.
 * Either way the draft only lands in the box, and nothing is said until Send.
 */
import type { DockInput } from '../scenes/types';

/** The server's cap on drafts per turn (ux_journeys D25), when the dock is not told. */
const DRAFTS_PER_TURN = 3;

export const draftsLeftText = (n: number) =>
  n === 1 ? '1 draft left' : `${n} drafts left`;

export interface DockControls {
  /** The line is on its way, or the turn is over: nothing can be pressed. */
  busy: boolean;
  /** The line in the box, trimmed: what Send sends. */
  line: string;
  /** The instructions to the agent, trimmed; empty = the agent writes its own line. */
  notes: string;
  canSend: boolean;
  /** The turn has a draft helper at all. */
  hasDraft: boolean;
  canDraft: boolean;
  draftsLeft: number;
  /** The Draft button's words. */
  draftLabel: string;
  /** What the Draft button will do, for its tooltip. */
  draftHint: string;
}

export function dockControls(dock: DockInput): DockControls {
  const busy = !!dock.sending || !!dock.closed;
  const line = dock.text.trim();
  const notes = (dock.notes ?? '').trim();
  const draftsLeft = dock.draftsLeft ?? DRAFTS_PER_TURN;
  const hasDraft = !!dock.onDraft;
  return {
    busy,
    line,
    notes,
    canSend: !!line && !busy,
    hasDraft,
    canDraft: hasDraft && !busy && !dock.drafting && draftsLeft > 0,
    draftsLeft,
    draftLabel: dock.drafting ? 'Drafting…' : 'Draft',
    draftHint: notes
      ? 'Your agent writes a line from what you told it. It lands in the box: edit it, then Send.'
      : 'Your agent writes a line of its own. It lands in the box: edit it, then Send.',
  };
}

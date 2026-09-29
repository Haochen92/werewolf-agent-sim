/**
 * What the speaking turn's dock allows at a given moment, worked out from what it is handed,
 * so the rules can be tested without drawing it. One button asks the seat's own agent for its
 * line: "Draft" while the box is empty, "Redraft" once it holds one. The optional steer in the
 * field goes with it (and revises the line in the box). Either way the draft only lands in the
 * box, and nothing is said until Send.
 */
import type { DraftRequest } from '@/types/contracts';
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
  /** The steer for the agent, trimmed; empty = the agent writes its own line. */
  notes: string;
  canSend: boolean;
  /** The turn has a draft helper at all. */
  hasDraft: boolean;
  canDraft: boolean;
  draftsLeft: number;
  /** The Draft button's words: "Draft" for an empty box, "Redraft" once it holds a line. */
  draftLabel: string;
  /** What the Draft button will do, for its tooltip. */
  draftHint: string;
  /** "Use my seat notes" is shown: the notebook has something to give. */
  hasNotebook: boolean;
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
    draftLabel: dock.drafting ? 'Drafting…' : line ? 'Redraft' : 'Draft',
    draftHint:
      (notes && line
        ? 'Your agent revises the line in the box as you asked.'
        : notes
          ? 'Your agent writes its line, steered by what you told it.'
          : 'Your agent writes the line it would say.') +
      ' It lands in the box: edit it, then Send.',
    hasNotebook: hasDraft && !!dock.notebook,
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

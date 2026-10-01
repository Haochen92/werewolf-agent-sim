'use client';

/**
 * The seated player's notebook for one game: a note on any other seat, a guess at its role
 * ("I think they are…", owner 2026-09-30), the one seat they suspect, and whether they have
 * seen the rail's "Tap a card to write notes" hint.
 *
 * It lives on this device only (localStorage, `notes_{gameId}`), and every scene that draws
 * the seat rail reads the same copy, so a note written in the day is on the card at night.
 * Which seat's notes are open is held above the scenes (`useNoteEditing`, 2026-10-01), so a
 * note being written stays open, its words as typed, while beats and scenes go by under it.
 * Storage may be missing or refuse a write (a private window): the notebook then lasts as
 * long as the page, and nothing breaks. It reaches the server only when the player asks their
 * agent for a draft with "Use my seat notes" ticked (`notebookForAgent`), for that one draft,
 * a guess folded into its seat's note ("(I think: wolf) …") so the request keeps its shape;
 * the suspect is the player's own mark, never a preselected ballot.
 */
import { useCallback, useMemo, useState, useSyncExternalStore } from 'react';
import { seatNotes } from '@/lib/storage';
import { ROLE_NAME } from './roles';

export interface NotebookState {
  /** A note per seat number, as written. */
  notes: Readonly<Record<number, string>>;
  /** The role the player thinks a seat holds, per seat number (a role id); none: not sure. */
  guesses: Readonly<Record<number, string>>;
  /** The seat marked as the suspect, or null. */
  suspect: number | null;
  /** The rail's hint has been dismissed (by a first tap on a card). */
  hinted: boolean;
}

export interface Notebook extends NotebookState {
  setNote: (seat: number, text: string) => void;
  /** "I think they are…": a role id, or null for "not sure". */
  setGuess: (seat: number, role: string | null) => void;
  /** Mark a seat as the suspect (replacing any other), or clear it with null. */
  setSuspect: (seat: number | null) => void;
  dismissHint: () => void;
}

const EMPTY: NotebookState = { notes: {}, guesses: {}, suspect: null, hinted: false };
/** What the server renders: no notes, and no hint (it appears once the page is live). */
const SERVER: NotebookState = { ...EMPTY, hinted: true };

/** A stored record read back, whatever state it is in. */
export function parseNotebook(raw: unknown): NotebookState {
  if (!raw || typeof raw !== 'object') return EMPTY;
  const r = raw as Record<string, unknown>;
  const notes: Record<number, string> = {};
  if (r.notes && typeof r.notes === 'object')
    for (const [k, v] of Object.entries(r.notes as Record<string, unknown>))
      if (typeof v === 'string' && Number.isInteger(Number(k))) notes[Number(k)] = v;
  // added 2026-09-30: a notebook kept before then has none, and reads as "not sure" throughout
  const guesses: Record<number, string> = {};
  if (r.guesses && typeof r.guesses === 'object')
    for (const [k, v] of Object.entries(r.guesses as Record<string, unknown>))
      if (typeof v === 'string' && v in ROLE_NAME && Number.isInteger(Number(k)))
        guesses[Number(k)] = v;
  const suspect =
    typeof r.suspect === 'number' && Number.isInteger(r.suspect) ? r.suspect : null;
  return { notes, guesses, suspect, hinted: r.hinted === true };
}

/** The roles in the order the cast is read out, for the guess's choices. */
const GUESS_ORDER = [
  'villager',
  'healer',
  'investigator',
  'vigilante',
  'wolf',
  'serial_killer',
];

/**
 * The roles a living seat could still hold, as the table knows it: the cast's counts less the
 * roles the dead have shown (deaths reveal the role), each with how many are left.
 */
export function guessChoices(
  cast: Readonly<Record<string, number>>,
  deadRoles: readonly (string | null)[],
): { role: string; left: number }[] {
  const left: Record<string, number> = { ...cast };
  for (const r of deadRoles) if (r) left[r] = (left[r] ?? 0) - 1;
  const roles = [
    ...GUESS_ORDER.filter((r) => r in left),
    ...Object.keys(left).filter((r) => !GUESS_ORDER.includes(r)),
  ];
  return roles.filter((r) => left[r] > 0).map((role) => ({ role, left: left[role] }));
}

const books = new Map<string, NotebookState>();
const listeners = new Map<string, Set<() => void>>();

function current(gameId: string): NotebookState {
  let b = books.get(gameId);
  if (!b) {
    b = parseNotebook(seatNotes.get(gameId));
    books.set(gameId, b);
  }
  return b;
}

/** Change one game's notebook, keep it, and tell every rail that shows it. */
export function updateNotebook(
  gameId: string,
  change: (b: NotebookState) => NotebookState,
): void {
  const next = change(current(gameId));
  books.set(gameId, next);
  seatNotes.set(gameId, next);
  listeners.get(gameId)?.forEach((f) => f());
}

/** The notebook for a game, or null when there is none to keep (no seated human, no game). */
export function useNotebook(gameId: string | null): Notebook | null {
  const subscribe = useCallback(
    (f: () => void) => {
      if (!gameId) return () => {};
      const set = listeners.get(gameId) ?? new Set();
      listeners.set(gameId, set);
      set.add(f);
      return () => set.delete(f);
    },
    [gameId],
  );
  const state = useSyncExternalStore(
    subscribe,
    () => (gameId ? current(gameId) : EMPTY),
    () => SERVER,
  );
  return useMemo(() => {
    if (!gameId) return null;
    return {
      ...state,
      setNote: (seat, text) =>
        updateNotebook(gameId, (b) => {
          const notes = { ...b.notes };
          if (text.trim()) notes[seat] = text;
          else delete notes[seat];
          return { ...b, notes };
        }),
      setGuess: (seat, role) =>
        updateNotebook(gameId, (b) => {
          const guesses = { ...b.guesses };
          if (role) guesses[seat] = role;
          else delete guesses[seat];
          return { ...b, guesses };
        }),
      setSuspect: (seat) => updateNotebook(gameId, (b) => ({ ...b, suspect: seat })),
      dismissHint: () =>
        updateNotebook(gameId, (b) => (b.hinted ? b : { ...b, hinted: true })),
    };
  }, [gameId, state]);
}

/** The server's cap on one shared note (DraftRequest.seat_notes). */
const SHARED_NOTE_MAX = 300;

/**
 * What the notebook gives the seat's agent with a draft, by the seat ids the agents use
 * (`player_5`), or null when it holds nothing to give. `dead` drops the suspect mark of a seat
 * that has died, as the rail does. A seat's role guess goes in front of its note, in words
 * ("(I think: serial killer) …"), so the request's shape is the server's as it was.
 */
export function notebookForAgent(
  book:
    | (Pick<NotebookState, 'notes' | 'suspect'> & Partial<Pick<NotebookState, 'guesses'>>)
    | null,
  dead: (seat: number) => boolean = () => false,
): { seat_notes: Record<string, string>; suspect: string } | null {
  if (!book) return null;
  const seatNotes: Record<string, string> = {};
  const guesses = book.guesses ?? {};
  const seats = new Set([...Object.keys(book.notes), ...Object.keys(guesses)]);
  for (const seat of seats) {
    const text = book.notes[Number(seat)]?.trim() ?? '';
    // a dead seat's role is on the table: a guess at it says nothing
    const guess = dead(Number(seat)) ? undefined : guesses[Number(seat)];
    const said = guess ? `(I think: ${(ROLE_NAME[guess] ?? guess).toLowerCase()})` : '';
    const note = [said, text].filter(Boolean).join(' ').slice(0, SHARED_NOTE_MAX);
    if (note) seatNotes[`player_${seat}`] = note;
  }
  const suspect =
    book.suspect !== null && !dead(book.suspect) ? `player_${book.suspect}` : '';
  return Object.keys(seatNotes).length || suspect
    ? { seat_notes: seatNotes, suspect }
    : null;
}

/** The game whose notebook this viewer keeps: a seated human in a live game, else none. */
export function notebookGame(
  p: { hud: string; game?: string },
  me: string | null,
): string | null {
  return p.hud === 'live' && me && p.game ? p.game : null;
}

/**
 * The note editor's open seat (`SlotInput.notebook`), and whether that seat was already dead
 * when its notes were opened: a seat that dies while its notes are open closes them, but the
 * notes on a seat already dead may be read and written.
 */
export interface NoteEdit {
  seat: number;
  dead: boolean;
}

/**
 * Whether the open editor stays open on this render of the wing: its seat is on the rail and
 * still writable (`editable`), and has not died since its notes were opened. Beats, scenes and
 * recuts go by under it; this is the only thing besides Done, Escape and a tap outside that
 * closes it.
 */
export function editorStays(
  edit: NoteEdit | null,
  tile: { dead?: unknown } | undefined,
  editable: boolean,
): boolean {
  if (!edit || !tile || !editable) return false;
  return !tile.dead || edit.dead;
}

/**
 * The open seat held by a container (the live game, the replay, the workbench), above the
 * scenes, so the editor outlives the wing, which is remounted with every turn and scene.
 */
export function useNoteEditing(): {
  editing: NoteEdit | null;
  onEdit: (edit: NoteEdit | null) => void;
} {
  const [editing, onEdit] = useState<NoteEdit | null>(null);
  return useMemo(() => ({ editing, onEdit }), [editing]);
}
